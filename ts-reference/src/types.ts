import { Idl } from "@project-serum/anchor"
import { IdlEnumVariant, IdlField } from "@project-serum/anchor/dist/cjs/idl"
import { CodeBlockWriter, Project, SourceFile, WriterFunction } from "ts-morph"
import camelcase from "camelcase"
import {
  fieldFromDecoded,
  fieldToJSON,
  unreachable,
  fieldToEncodable,
  layoutForType,
  tsTypeFromIdl,
  fieldsInterfaceName,
  kindInterfaceName,
  valueInterfaceName,
  structFieldInitializer,
  jsonInterfaceName,
  idlTypeToJSONType,
  fieldFromJSON,
} from "./common"

export function genTypes(
  project: Project,
  idl: Idl,
  outPath: (path: string) => string
) {
  if (idl.types === undefined || idl.types.length === 0) {
    return
  }

  genIndexFile(project, idl, outPath)
  genTypeFiles(project, idl, outPath)
}

function genIndexFile(
  project: Project,
  idl: Idl,
  outPath: (path: string) => string
) {
  const src = project.createSourceFile(outPath("types/index.ts"), "", {
    overwrite: true,
  })

  idl.types?.forEach((ty) => {
    switch (ty.type.kind) {
      case "struct":
        src.addExportDeclaration({
          namedExports: [
            ty.name,
            fieldsInterfaceName(ty.name),
            jsonInterfaceName(ty.name),
          ],
          moduleSpecifier: `./${ty.name}`,
        })
        return
      case "enum":
        src.addImportDeclaration({
          namespaceImport: ty.name,
          moduleSpecifier: `./${ty.name}`,
        })
        src.addExportDeclaration({
          namedExports: [ty.name],
        })
        src.addTypeAlias({
          isExported: true,
          name: kindInterfaceName(ty.name),
          type: ty.type.variants
            .map((variant) => {
              return `${ty.name}.${variant.name}`
            })
            .join(" | "),
        })
        src.addTypeAlias({
          isExported: true,
          name: jsonInterfaceName(ty.name),
          type: ty.type.variants
            .map((variant) => {
              return `${ty.name}.${jsonInterfaceName(variant.name)}`
            })
            .join(" | "),
        })
        return
      default:
        unreachable(ty.type)
    }
  })
}

function genTypeFiles(
  project: Project,
  idl: Idl,
  outPath: (path: string) => string
) {
  idl.types?.forEach((ty) => {
    const src = project.createSourceFile(outPath(`types/${ty.name}.ts`), "", {
      overwrite: true,
    })

    switch (ty.type.kind) {
      case "struct": {
        genStruct(idl, src, ty.name, ty.type.fields)
        return
      }
      case "enum": {
        genEnum(idl, src, ty.name, ty.type.variants)
        return
      }
      default:
        unreachable(ty.type)
    }
  })
}

function genStruct(
  idl: Idl,
  src: SourceFile,
  name: string,
  fields: Array<IdlField>
) {
  // imports
  src.addStatements([
    `import { PublicKey } from "@solana/web3.js" // eslint-disable-line @typescript-eslint/no-unused-vars`,
    `import BN from "bn.js" // eslint-disable-line @typescript-eslint/no-unused-vars`,
    `import * as types from "../types" // eslint-disable-line @typescript-eslint/no-unused-vars`,
    `import * as borsh from "@project-serum/borsh"`,
  ])

  // fields interface
  src.addInterface({
    isExported: true,
    name: fieldsInterfaceName(name),
    properties: fields.map((field) => {
      return {
        name: field.name,
        type: tsTypeFromIdl(idl, field.type),
      }
    }),
  })

  // json interface
  src.addInterface({
    isExported: true,
    name: jsonInterfaceName(name),
    properties: fields.map((field) => {
      return {
        name: field.name,
        type: idlTypeToJSONType(field.type),
      }
    }),
  })

  // struct class
  const cls = src.addClass({
    isExported: true,
    name: name,
    properties: fields.map((field) => {
      return {
        isReadonly: true,
        name: field.name,
        type: tsTypeFromIdl(idl, field.type, "types.", false),
      }
    }),
  })

  // constructor
  cls.addConstructor({
    parameters: [
      {
        name: "fields",
        type: fieldsInterfaceName(name),
      },
    ],
    statements: (writer) => {
      fields.forEach((field) => {
        const initializer = structFieldInitializer(idl, field)
        writer.writeLine(`this.${field.name} = ${initializer}`)
      })
    },
  })

  // static layout
  cls.addMethod({
    isStatic: true,
    name: "layout",
    parameters: [
      {
        name: "property",
        type: "string",
        hasQuestionToken: true,
      },
    ],
    statements: [
      (writer) => {
        writer.write("return borsh.struct([")

        fields.forEach((field) => {
          writer.writeLine(layoutForType(field.type, field.name) + ",")
        })

        writer.write("], property)")
      },
    ],
  })

  // static fromDecoded
  const fromDecoded = cls.addMethod({
    isStatic: true,
    name: "fromDecoded",
    parameters: [
      {
        name: "obj",
        type: "any",
      },
    ],
    statements: [
      (writer) => {
        writer.write(`return new ${name}({`)

        fields.forEach((field) => {
          const decoded = fieldFromDecoded(idl, field, "obj.")
          writer.writeLine(`${field.name}: ${decoded},`)
        })

        writer.write("})")
      },
    ],
  })
  cls.insertText(
    fromDecoded.getStart(),
    "// eslint-disable-next-line @typescript-eslint/no-explicit-any\n"
  )

  // static toEncodable
  cls.addMethod({
    isStatic: true,
    name: "toEncodable",
    parameters: [
      {
        name: "fields",
        type: fieldsInterfaceName(name),
      },
    ],
    statements: [
      (writer) => {
        writer.write(`return {`)

        fields.forEach((field) => {
          writer.writeLine(
            `${field.name}: ${fieldToEncodable(idl, field, "fields.")},`
          )
        })

        writer.write("}")
      },
    ],
  })

  // toJSON
  cls.addMethod({
    name: "toJSON",
    returnType: jsonInterfaceName(name),
    statements: [
      (writer) => {
        writer.write(`return {`)

        fields.forEach((field) => {
          writer.writeLine(
            `${field.name}: ${fieldToJSON(idl, field, "this.")},`
          )
        })

        writer.write("}")
      },
    ],
  })

  // fromJSON
  cls.addMethod({
    isStatic: true,
    name: "fromJSON",
    returnType: name,
    parameters: [
      {
        name: "obj",
        type: jsonInterfaceName(name),
      },
    ],
    statements: [
      (writer) => {
        writer.write(`return new ${name}({`)

        fields.forEach((field) => {
          writer.writeLine(`${field.name}: ${fieldFromJSON(field)},`)
        })

        writer.write("})")
      },
    ],
  })

  // toEncodable
  cls.addMethod({
    name: "toEncodable",
    statements: [`return ${name}.toEncodable(this)`],
  })
}

function genEnum(
  idl: Idl,
  src: SourceFile,
  name: string,
  variants: Array<IdlEnumVariant>
) {
  // imports
  src.addStatements([
    `import { PublicKey } from "@solana/web3.js" // eslint-disable-line @typescript-eslint/no-unused-vars`,
    `import BN from "bn.js" // eslint-disable-line @typescript-eslint/no-unused-vars`,
    `import * as types from "../types" // eslint-disable-line @typescript-eslint/no-unused-vars`,
    `import * as borsh from "@project-serum/borsh"`,
  ])

  // variants
  variants.forEach((variant, i) => {
    const discriminator = i

    // fields and value type aliases
    const fields = variant.fields

    if (fields && fields.length > 0) {
      let fieldsAliasType: string | WriterFunction
      let valueAliasType: string | WriterFunction

      if (typeof fields[0] === "object" && "name" in fields[0]) {
        // named enums
        fieldsAliasType = (writer) => {
          writer.write("{")

          fields.forEach((field) => {
            writer.writeLine(
              `${camelcase(field.name)}: ${tsTypeFromIdl(idl, field.type)}`
            )
          })

          writer.writeLine("}")
        }

        valueAliasType = (writer) => {
          writer.write("{")

          fields.forEach((field) => {
            writer.writeLine(
              `${camelcase(field.name)}: ${tsTypeFromIdl(
                idl,
                field.type,
                "types.",
                false
              )}`
            )
          })

          writer.writeLine("}")
        }
      } else {
        // tuple enums
        fieldsAliasType = (writer) => {
          writer.write("[")

          fields.forEach((field) => {
            writer.writeLine(`${tsTypeFromIdl(idl, field)},`)
          })

          writer.writeLine("]")
        }

        valueAliasType = (writer) => {
          writer.write("[")

          fields.forEach((field) => {
            writer.writeLine(`${tsTypeFromIdl(idl, field, "types.", false)},`)
          })

          writer.writeLine("]")
        }
      }

      src.addTypeAlias({
        isExported: true,
        name: fieldsInterfaceName(variant.name),
        type: fieldsAliasType,
      })

      src.addTypeAlias({
        isExported: true,
        name: valueInterfaceName(variant.name),
        type: valueAliasType,
      })
    }

    // json interface
    const jsonInterface = src.addInterface({
      isExported: true,
      name: jsonInterfaceName(variant.name),
      properties: [
        {
          name: "kind",
          type: `"${variant.name}"`,
        },
      ],
    })
    if (fields !== undefined && fields.length > 0) {
      const valueTypeWriter: WriterFunction = (writer: CodeBlockWriter) => {
        if (typeof fields[0] === "object" && "name" in fields[0]) {
          writer.inlineBlock(() => {
            fields.forEach((field) => {
              const name = camelcase(field.name)
              writer.writeLine(`${name}: ${idlTypeToJSONType(field.type)},`)
            })
          })
        } else {
          writer.write(`[`)
          writer.blankLine()

          fields.forEach((field) => {
            writer.writeLine(`${idlTypeToJSONType(field)},`)
          })

          writer.write("]")
        }
      }

      jsonInterface.addProperty({
        name: "value",
        type: valueTypeWriter,
      })
    }

    // enum class
    const cls = src.addClass({
      isExported: true,
      name: variant.name,
      properties: [
        {
          isReadonly: true,
          name: "discriminator",
          initializer: discriminator.toString(),
        },
        {
          isReadonly: true,
          name: "kind",
          initializer: `"${variant.name}"`,
        },
      ],
    })
    if (fields && fields.length > 0) {
      cls.addProperty({
        isReadonly: true,
        name: "value",
        type: valueInterfaceName(variant.name),
      })
    }

    // constructor
    if (fields && fields.length > 0) {
      const cstr = cls.addConstructor({
        parameters: [
          {
            name: "value",
            type: fieldsInterfaceName(variant.name),
          },
        ],
      })
      cstr.setBodyText((writer) => {
        if (typeof fields[0] === "object" && "name" in fields[0]) {
          writer.write("this.value = {")

          fields.forEach((field) => {
            const name = camelcase(field.name)
            writer.writeLine(
              `${name}: ${structFieldInitializer(
                idl,
                { ...field, name },
                "value."
              )},`
            )
          })

          writer.writeLine("}")
        } else {
          writer.write("this.value = [")

          fields.forEach((field, i) => {
            const name = `value[${i}]`
            writer.writeLine(
              `${structFieldInitializer(idl, { name, type: field }, "")},`
            )
          })

          writer.writeLine("]")
        }
      })
    }

    // toJSON
    const toJSONstmt: WriterFunction = (writer: CodeBlockWriter) => {
      writer.write("return")
      writer.inlineBlock(() => {
        writer.writeLine(`kind: "${variant.name}",`)

        if (fields === undefined || fields.length === 0) {
          return
        }

        writer.write("value: ")

        if (typeof fields[0] === "object" && "name" in fields[0]) {
          writer.inlineBlock(() => {
            fields.forEach((field) => {
              const name = camelcase(field.name)
              writer.writeLine(
                `${name}: ${fieldToJSON(
                  idl,
                  { ...field, name },
                  "this.value."
                )},`
              )
            })
          })
        } else {
          writer.write(`[`)

          fields.forEach((field, i) => {
            const name = `value[${i}]`
            writer.writeLine(
              `${fieldToJSON(idl, { name, type: field }, "this.")},`
            )
          })

          writer.write("]")
        }
      })
    }
    cls.addMethod({
      name: "toJSON",
      returnType: jsonInterfaceName(variant.name),
      statements: [toJSONstmt],
    })

    // toEncodable
    const toEncodableStmt: WriterFunction = (writer) => {
      writer.write(`return`).inlineBlock(() => {
        writer.writeLine(`${variant.name}: {`)

        fields?.forEach((field, i) => {
          if (typeof field === "object" && "name" in field) {
            const encodable = fieldToEncodable(
              idl,
              { ...field, name: camelcase(field.name) },
              "this.value."
            )
            writer.writeLine(`${field.name}: ${encodable},`)
          } else {
            const encodable = fieldToEncodable(
              idl,
              { type: field, name: `[${i}]` },
              "this.value"
            )
            writer.writeLine(`_${i}: ${encodable},`)
          }
        })

        writer.writeLine(`}`)
      })
    }
    cls.addMethod({
      name: "toEncodable",
      statements: [toEncodableStmt],
    })
  })

  // fromDecoded
  const fromDecoded = src.addFunction({
    isExported: true,
    name: "fromDecoded",
    parameters: [
      {
        name: "obj",
        type: "any",
      },
    ],
    returnType: `types.${kindInterfaceName(name)}`,
    statements: [
      (writer) => {
        writer.write('if (typeof obj !== "object")').block(() => {
          writer.writeLine('throw new Error("Invalid enum object")')
        })
        writer.blankLine()

        variants.forEach((variant) => {
          writer.write(`if ("${variant.name}" in obj)`).block(() => {
            if (variant.fields && variant.fields.length > 0) {
              writer.writeLine(`const val = obj["${variant.name}"]`)

              if (
                typeof variant.fields[0] === "object" &&
                "name" in variant.fields[0]
              ) {
                // struct enum
                writer.write(`return new ${variant.name}({`)
                variant.fields.forEach((field) => {
                  const decoded = fieldFromDecoded(
                    idl,
                    {
                      ...field,
                      name: `val["${field.name}"],`,
                    },
                    ""
                  )
                  writer.writeLine(`${camelcase(field.name)}: ${decoded}`)
                })
                writer.writeLine(`})`)
              } else {
                // tuple enum
                writer.write(`return new ${variant.name}([`)
                variant.fields.forEach((field, i) => {
                  const decoded = fieldFromDecoded(
                    idl,
                    {
                      type: field,
                      name: `val["_${i}"]`,
                    },
                    ""
                  )
                  writer.writeLine(`${decoded},`)
                })
                writer.writeLine(`])`)
              }
            } else {
              // discriminant enum
              writer.writeLine(`return new ${variant.name}()`)
            }
          })
        })

        writer.blankLine()
        writer.writeLine('throw new Error("Invalid enum object")')
      },
    ],
  })
  src.insertText(
    fromDecoded.getStart(),
    "// eslint-disable-next-line @typescript-eslint/no-explicit-any\n"
  )
  // fromJSON
  src.addFunction({
    isExported: true,
    name: "fromJSON",
    parameters: [
      {
        name: "obj",
        type: `types.${jsonInterfaceName(name)}`,
      },
    ],
    returnType: `types.${kindInterfaceName(name)}`,
    statements: [
      (writer) => {
        writer.write("switch (obj.kind)").block(() => {
          variants.forEach((variant) => {
            writer.write(`case "${variant.name}":`).block(() => {
              if (variant.fields && variant.fields.length > 0) {
                if (
                  typeof variant.fields[0] === "object" &&
                  "name" in variant.fields[0]
                ) {
                  // struct enum
                  writer.write(`return new ${variant.name}({`)
                  variant.fields.forEach((field) => {
                    const jf = fieldFromJSON(
                      { ...field, name: camelcase(field.name) },
                      "obj.value"
                    )
                    writer.writeLine(`${camelcase(field.name)}: ${jf},`)
                  })
                  writer.writeLine(`})`)
                } else {
                  // tuple enum
                  writer.write(`return new ${variant.name}([`)
                  variant.fields.forEach((field, i) => {
                    const jf = fieldFromJSON({
                      type: field,
                      name: `value[${i}]`,
                    })
                    writer.writeLine(`${jf},`)
                  })
                  writer.writeLine(`])`)
                }
              } else {
                // discriminant enum
                writer.writeLine(`return new ${variant.name}()`)
              }
            })
          })
        })
      },
    ],
  })

  // layout
  src.addFunction({
    isExported: true,
    name: "layout",
    parameters: [
      {
        name: "property",
        hasQuestionToken: true,
        type: "string",
      },
    ],
    statements: [
      (writer) => {
        writer.write("const ret = borsh.rustEnum([")
        writer.indent(() => {
          variants.forEach((variant) => {
            writer.writeLine("borsh.struct([")
            writer.indent(() => {
              variant.fields?.forEach((field, i) => {
                if (typeof field === "object" && "type" in field) {
                  writer.writeLine(layoutForType(field.type, field.name) + ",")
                } else {
                  writer.writeLine(layoutForType(field, `_${i}`) + ",")
                }
              })
            })
            writer.writeLine(`], "${variant.name}"),`)
          })
        })
        writer.writeLine("])")

        writer.writeLine("if (property !== undefined)").block(() => {
          writer.writeLine("return ret.replicate(property)")
        })
        writer.writeLine("return ret")
      },
    ],
  })
}
