import { Idl } from "@project-serum/anchor"
import { Project } from "ts-morph"
import {
  fieldFromDecoded,
  fieldFromJSON,
  fieldsInterfaceName,
  fieldToJSON,
  genAccDiscriminator,
  idlTypeToJSONType,
  jsonInterfaceName,
  layoutForType,
  structFieldInitializer,
  tsTypeFromIdl,
} from "./common"

export function genAccounts(
  project: Project,
  idl: Idl,
  outPath: (path: string) => string
) {
  if (idl.accounts === undefined || idl.accounts.length === 0) {
    return
  }

  genIndexFile(project, idl, outPath)
  genAccountFiles(project, idl, outPath)
}

function genIndexFile(
  project: Project,
  idl: Idl,
  outPath: (path: string) => string
) {
  const src = project.createSourceFile(outPath("accounts/index.ts"), "", {
    overwrite: true,
  })

  idl.accounts?.forEach((ix) => {
    src.addExportDeclaration({
      namedExports: [
        ix.name,
        fieldsInterfaceName(ix.name),
        jsonInterfaceName(ix.name),
      ],
      moduleSpecifier: `./${ix.name}`,
    })
  })
}

function genAccountFiles(
  project: Project,
  idl: Idl,
  outPath: (path: string) => string
) {
  idl.accounts?.forEach((acc) => {
    const src = project.createSourceFile(
      outPath(`accounts/${acc.name}.ts`),
      "",
      {
        overwrite: true,
      }
    )

    // imports
    src.addStatements([
      `import { PublicKey, Connection } from "@solana/web3.js"`,
      `import BN from "bn.js" // eslint-disable-line @typescript-eslint/no-unused-vars`,
      `import * as borsh from "@project-serum/borsh" // eslint-disable-line @typescript-eslint/no-unused-vars`,
      ...(idl.types && idl.types.length > 0
        ? [
            `import * as types from "../types" // eslint-disable-line @typescript-eslint/no-unused-vars`,
          ]
        : []),
      `import { PROGRAM_ID } from "../programId"`,
    ])

    const fields = acc.type.fields
    const name = acc.name

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

    // account class
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

    // discriminator
    cls
      .addProperty({
        isStatic: true,
        isReadonly: true,
        name: "discriminator",
        initializer: `Buffer.from([${genAccDiscriminator(name).toString()}])`,
      })
      .prependWhitespace("\n")

    // layout
    cls
      .addProperty({
        isStatic: true,
        isReadonly: true,
        name: "layout",
        initializer: (writer) => {
          writer.write("borsh.struct([")

          fields.forEach((field) => {
            writer.writeLine(layoutForType(field.type, field.name) + ",")
          })

          writer.write("])")
        },
      })
      .prependWhitespace("\n")

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

    // fetch
    cls.addMethod({
      isStatic: true,
      isAsync: true,
      name: "fetch",
      parameters: [
        {
          name: "c",
          type: "Connection",
        },
        {
          name: "address",
          type: "PublicKey",
        },
      ],
      returnType: `Promise<${name} | null>`,
      statements: [
        (writer) => {
          writer.writeLine("const info = await c.getAccountInfo(address)")
          writer.blankLine()
          writer.write("if (info === null)")
          writer.inlineBlock(() => {
            writer.writeLine("return null")
          })
          writer.write("if (!info.owner.equals(PROGRAM_ID))")
          writer.inlineBlock(() => {
            writer.writeLine(
              `throw new Error("account doesn't belong to this program")`
            )
          })
          writer.blankLine()
          writer.writeLine("return this.decode(info.data)")
        },
      ],
    })

    // fetchMultiple
    cls.addMethod({
      isStatic: true,
      isAsync: true,
      name: "fetchMultiple",
      parameters: [
        {
          name: "c",
          type: "Connection",
        },
        {
          name: "addresses",
          type: "PublicKey[]",
        },
      ],
      returnType: `Promise<Array<${name} | null>>`,
      statements: [
        (writer) => {
          writer.writeLine(
            "const infos = await c.getMultipleAccountsInfo(addresses)"
          )
          writer.blankLine()
          writer.write("return infos.map((info) => ")
          writer.inlineBlock(() => {
            writer.write("if (info === null)")
            writer.inlineBlock(() => {
              writer.writeLine("return null")
            })
            writer.write("")

            writer.write("if (!info.owner.equals(PROGRAM_ID))")
            writer.inlineBlock(() => {
              writer.writeLine(
                `throw new Error("account doesn't belong to this program")`
              )
            })
            writer.blankLine()
            writer.writeLine("return this.decode(info.data)")
          })
          writer.write(")")
        },
      ],
    })

    // decode
    cls.addMethod({
      isStatic: true,
      name: "decode",
      parameters: [
        {
          name: "data",
          type: "Buffer",
        },
      ],
      returnType: name,
      statements: [
        (writer) => {
          writer.write(`if (!data.slice(0, 8).equals(${name}.discriminator))`)
          writer.inlineBlock(() => {
            writer.writeLine(`throw new Error("invalid account discriminator")`)
          })
          writer.blankLine()
          writer.writeLine(`const dec = ${name}.layout.decode(data.slice(8))`)

          writer.blankLine()
          writer.write(`return new ${name}({`)
          fields.forEach((field) => {
            const decoded = fieldFromDecoded(idl, field, "dec.")
            writer.writeLine(`${field.name}: ${decoded},`)
          })
          writer.write("})")
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
  })
}
