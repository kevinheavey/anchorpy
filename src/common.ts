import { Idl } from "@project-serum/anchor"
import { IdlField, IdlType } from "@project-serum/anchor/dist/cjs/idl"
import camelcase from "camelcase"
import { sha256 } from "js-sha256"
import { snakeCase } from "snake-case"

/**
 *
 * Makes the type checker error if this part of code is reachable (all cases aren't handled).
 *
 */
/* eslint-disable-next-line @typescript-eslint/no-unused-vars */
export function unreachable(_: never) {
  return undefined
}

export function fieldsInterfaceName(typeName: string) {
  return `${typeName}Fields`
}

export function valueInterfaceName(typeName: string) {
  return `${typeName}Value`
}

export function kindInterfaceName(typeName: string) {
  return `${typeName}Kind`
}

export function jsonInterfaceName(typeName: string) {
  return `${typeName}JSON`
}

export function tsTypeFromIdl(
  idl: Idl,
  ty: IdlType,
  definedTypesPrefix = "types.",
  useFieldsInterfaceForStruct = true
): string {
  switch (ty) {
    case "bool":
      return "boolean"
    case "u8":
    case "i8":
    case "u16":
    case "i16":
    case "u32":
    case "i32":
    case "f32":
      return "number"
    case "u64":
    case "i64":
      return "BN"
    case "f64":
      return "number"
    case "u128":
    case "i128":
      return "BN"
    case "bytes":
      return "Array<number>"
    case "string":
      return "string"
    case "publicKey":
      return "PublicKey"
    default:
      if ("vec" in ty) {
        return `Array<${tsTypeFromIdl(
          idl,
          ty.vec,
          definedTypesPrefix,
          useFieldsInterfaceForStruct
        )}>`
      }
      if ("option" in ty) {
        return `${tsTypeFromIdl(
          idl,
          ty.option,
          definedTypesPrefix,
          useFieldsInterfaceForStruct
        )} | null`
      }
      if ("coption" in ty) {
        return `${tsTypeFromIdl(
          idl,
          ty.coption,
          definedTypesPrefix,
          useFieldsInterfaceForStruct
        )} | null`
      }
      if ("defined" in ty) {
        const filtered = idl.types?.filter((t) => t.name === ty.defined) ?? []
        if (filtered.length !== 1) {
          throw new Error(`Defined type not found: ${JSON.stringify(ty)}`)
        }

        switch (filtered[0].type.kind) {
          case "struct": {
            const name = useFieldsInterfaceForStruct
              ? fieldsInterfaceName(ty.defined)
              : ty.defined
            return `${definedTypesPrefix}${name}`
          }
          case "enum": {
            const name = kindInterfaceName(ty.defined)
            return `${definedTypesPrefix}${name}`
          }
        }
      }
      if ("array" in ty) {
        return `Array<${tsTypeFromIdl(
          idl,
          ty.array[0],
          definedTypesPrefix,
          useFieldsInterfaceForStruct
        )}>`
      }
  }

  unreachable(ty)
  throw new Error("Unreachable.")
}

export function layoutForType(
  ty: IdlType,
  property?: string,
  definedTypesPrefix = "types."
): string {
  const q = (property?: string) => {
    if (property === undefined) {
      return ""
    }

    return `"${property}"`
  }

  switch (ty) {
    case "bool":
      return `borsh.bool(${q(property)})`
    case "u8":
      return `borsh.u8(${q(property)})`
    case "i8":
      return `borsh.i8(${q(property)})`
    case "u16":
      return `borsh.u16(${q(property)})`
    case "i16":
      return `borsh.i16(${q(property)})`
    case "u32":
      return `borsh.u32(${q(property)})`
    case "f32":
      return `borsh.f32(${q(property)})`
    case "i32":
      return `borsh.i32(${q(property)})`
    case "u64":
      return `borsh.u64(${q(property)})`
    case "i64":
      return `borsh.i64(${q(property)})`
    case "f64":
      return `borsh.f64(${q(property)})`
    case "u128":
      return `borsh.u128(${q(property)})`
    case "i128":
      return `borsh.i128(${q(property)})`
    case "bytes":
      return `borsh.vecU8(${q(property)})`
    case "string":
      return `borsh.str(${q(property)})`
    case "publicKey":
      return `borsh.publicKey(${q(property)})`
    default:
      if ("vec" in ty) {
        return `borsh.vec(${layoutForType(ty.vec)}, ${q(property)})`
      }
      if ("option" in ty) {
        return `borsh.option(${layoutForType(ty.option)}, ${q(property)})`
      }
      if ("coption" in ty) {
        throw new Error("coption layout support not implemented") // TODO add support
      }
      if ("defined" in ty) {
        return `${definedTypesPrefix}${ty.defined}.layout(${q(property)})`
      }
      if ("array" in ty) {
        const propTxt = (property && `, ${q(property)}`) || ""

        return `borsh.array(${layoutForType(ty.array[0])}, ${
          ty.array[1]
        }${propTxt})`
      }
  }

  unreachable(ty)
  throw new Error("Unreachable.")
}

export function genIxIdentifier(ixName: string) {
  const namespace = "global"
  const name = snakeCase(ixName)
  const preimage = `${namespace}:${name}`

  return sha256.digest(preimage).slice(0, 8)
}
export function genAccDiscriminator(accName: string) {
  return sha256
    .digest(`account:${camelcase(accName, { pascalCase: true })}`)
    .slice(0, 8)
}

export function fieldToEncodable(
  idl: Idl,
  ty: IdlField,
  valPrefix = "",
  definedTypesPrefix = "types."
): string {
  switch (ty.type) {
    case "bool":
    case "u8":
    case "i8":
    case "u16":
    case "i16":
    case "u32":
    case "i32":
    case "f32":
    case "u64":
    case "i64":
    case "f64":
    case "u128":
    case "i128":
    case "string":
    case "publicKey":
      return `${valPrefix}${ty.name}`
    case "bytes":
      return `Buffer.from(${valPrefix}${ty.name})`
    default:
      if ("vec" in ty.type) {
        const mapBody = fieldToEncodable(
          idl,
          {
            name: "item",
            type: ty.type.vec,
          },
          "",
          definedTypesPrefix
        )
        // skip mapping when not needed
        if (mapBody === "item") {
          return `${valPrefix}${ty.name}`
        }
        return `${valPrefix}${ty.name}.map((item) => ${mapBody})`
      }
      if ("option" in ty.type) {
        const encodable = fieldToEncodable(
          idl,
          { name: ty.name, type: ty.type.option },
          valPrefix,
          definedTypesPrefix
        )
        // skip coercion when not needed
        if (encodable === `${valPrefix}${ty.name}`) {
          return encodable
        }
        return `(${valPrefix}${ty.name} && ${encodable}) || null`
      }
      if ("coption" in ty.type) {
        throw new Error("coption layout support not implemented") // TODO add support
      }
      if ("defined" in ty.type) {
        const defined = ty.type.defined
        const filtered = idl.types?.filter((t) => t.name === defined) ?? []
        if (filtered.length !== 1) {
          throw new Error(`Defined type not found: ${JSON.stringify(ty)}`)
        }

        switch (filtered[0].type.kind) {
          case "struct": {
            return `${definedTypesPrefix}${ty.type.defined}.toEncodable(${valPrefix}${ty.name})`
          }
          case "enum": {
            return `${valPrefix}${ty.name}.toEncodable()`
          }
        }
      }
      if ("array" in ty.type) {
        const mapBody = fieldToEncodable(
          idl,
          {
            name: "item",
            type: ty.type.array[0],
          },
          "",
          definedTypesPrefix
        )
        // skip mapping when not needed
        if (mapBody === "item") {
          return `${valPrefix}${ty.name}`
        }
        return `${valPrefix}${ty.name}.map((item) => ${mapBody})`
      }

      unreachable(ty.type)
      throw new Error("Unreachable.")
  }
}

export function fieldFromDecoded(
  idl: Idl,
  ty: IdlField,
  valPrefix = "",
  definedTypesPrefix = "types."
): string {
  switch (ty.type) {
    case "bool":
    case "u8":
    case "i8":
    case "u16":
    case "i16":
    case "u32":
    case "i32":
    case "f32":
    case "u64":
    case "i64":
    case "f64":
    case "u128":
    case "i128":
    case "string":
    case "publicKey":
      return `${valPrefix}${ty.name}`
    case "bytes":
      return `Array.from(${valPrefix}${ty.name})`
    default:
      if ("vec" in ty.type) {
        const mapBody = fieldFromDecoded(
          idl,
          {
            name: "item",
            type: ty.type.vec,
          },
          "",
          definedTypesPrefix
        )
        // skip mapping when not needed
        if (mapBody === "item") {
          return `${valPrefix}${ty.name}`
        }
        return `${valPrefix}${ty.name}.map((item) => ${mapBody})`
      }
      if ("option" in ty.type) {
        const decoded = fieldFromDecoded(
          idl,
          { name: ty.name, type: ty.type.option },
          valPrefix
        )
        // skip coercion when not needed
        if (decoded === `${valPrefix}${ty.name}`) {
          return decoded
        }
        return `(${valPrefix}${ty.name} && ${decoded}) || null`
      }
      if ("coption" in ty.type) {
        throw new Error("coption layout support not implemented") // TODO add support
      }
      if ("defined" in ty.type) {
        const defined = ty.type.defined
        const filtered = idl.types?.filter((t) => t.name === defined) ?? []
        if (filtered.length !== 1) {
          throw new Error(`Defined type not found: ${JSON.stringify(ty)}`)
        }

        switch (filtered[0].type.kind) {
          case "struct":
          case "enum":
            return `${definedTypesPrefix}${ty.type.defined}.fromDecoded(${valPrefix}${ty.name})`
          default: {
            unreachable(filtered[0].type)
            throw new Error("Unreachable.")
          }
        }
      }
      if ("array" in ty.type) {
        const mapBody = fieldFromDecoded(
          idl,
          {
            name: "item",
            type: ty.type.array[0],
          },
          "",
          definedTypesPrefix
        )
        // skip mapping when not needed
        if (mapBody === "item") {
          return `${valPrefix}${ty.name}`
        }
        return `${valPrefix}${ty.name}.map((item) => ${mapBody})`
      }

      unreachable(ty.type)
      throw new Error("Unreachable.")
  }
}

export function structFieldInitializer(
  idl: Idl,
  field: IdlField,
  prefix = "fields."
) {
  switch (field.type) {
    case "bool":
    case "u8":
    case "i8":
    case "u16":
    case "i16":
    case "u32":
    case "i32":
    case "f32":
    case "u64":
    case "i64":
    case "f64":
    case "u128":
    case "i128":
    case "bytes":
    case "string":
    case "publicKey":
      return `${prefix}${field.name}`
    default:
      if ("defined" in field.type) {
        const defined = field.type.defined
        const filtered = idl.types?.filter((t) => t.name === defined) ?? []
        if (filtered.length !== 1) {
          throw new Error(`Defined type not found: ${defined}`)
        }

        switch (filtered[0].type.kind) {
          case "struct":
            return `new types.${filtered[0].name}({ ...${prefix}${field.name} })`
          case "enum":
            filtered[0].type.kind
            return `${prefix}${field.name}`
          default:
            unreachable(filtered[0].type)
            return
        }
      }
      if ("option" in field.type) {
        const initializer = structFieldInitializer(
          idl,
          { name: field.name, type: field.type.option },
          prefix
        )
        // skip coercion when not needed
        if (initializer === `${prefix}${field.name}`) {
          return initializer
        } else {
          return `(${prefix}${field.name} && ${initializer}) || null`
        }
      }
      if ("coption" in field.type) {
        const initializer = structFieldInitializer(
          idl,
          { name: field.name, type: field.type.coption },
          prefix
        )
        // skip coercion when not needed
        if (initializer === `${prefix}${field.name}`) {
          return initializer
        } else {
          return `(${prefix}${field.name} && ${initializer}) || null`
        }
      }
      if ("array" in field.type) {
        const mapBody = `${structFieldInitializer(
          idl,
          {
            name: "item",
            type: field.type.array[0],
          },
          ""
        )}`
        // skip mapping when not needed
        if (mapBody === "item") {
          return `${prefix}${field.name}`
        }

        return `${prefix}${field.name}.map((item) => ${mapBody})`
      }
      if ("vec" in field.type) {
        const mapBody = `${structFieldInitializer(
          idl,
          {
            name: "item",
            type: field.type.vec,
          },
          ""
        )}`
        // skip mapping when not needed
        if (mapBody === "item") {
          return `${prefix}${field.name}`
        }

        return `${prefix}${field.name}.map((item) => ${mapBody})`
      }

      unreachable(field.type)
  }
}

export function fieldToJSON(idl: Idl, ty: IdlField, valPrefix = ""): string {
  switch (ty.type) {
    case "bool":
    case "u8":
    case "i8":
    case "u16":
    case "i16":
    case "u32":
    case "i32":
    case "f32":
    case "f64":
    case "string":
      return `${valPrefix}${ty.name}`
    case "u64":
    case "i64":
    case "u128":
    case "i128":
    case "publicKey":
      return `${valPrefix}${ty.name}.toString()`
    case "bytes":
      return `${valPrefix}${ty.name}`
    default:
      if ("vec" in ty.type) {
        const mapBody = fieldToJSON(idl, {
          name: "item",
          type: ty.type.vec,
        })
        // skip mapping when not needed
        if (mapBody === "item") {
          return `${valPrefix}${ty.name}`
        }
        return `${valPrefix}${ty.name}.map((item) => ${mapBody})`
      }
      if ("array" in ty.type) {
        const mapBody = fieldToJSON(idl, {
          name: "item",
          type: ty.type.array[0],
        })
        // skip mapping when not needed
        if (mapBody === "item") {
          return `${valPrefix}${ty.name}`
        }
        return `${valPrefix}${ty.name}.map((item) => ${mapBody})`
      }
      if ("option" in ty.type) {
        const value = fieldToJSON(
          idl,
          { name: ty.name, type: ty.type.option },
          valPrefix
        )
        // skip coercion when not needed
        if (value === `${valPrefix}${ty.name}`) {
          return value
        }
        return `(${valPrefix}${ty.name} && ${value}) || null`
      }
      if ("coption" in ty.type) {
        const value = fieldToJSON(
          idl,
          { name: ty.name, type: ty.type.coption },
          valPrefix
        )
        // skip coercion when not needed
        if (value === `${valPrefix}${ty.name}`) {
          return value
        }
        return `(${valPrefix}${ty.name} && ${value}) || null`
      }
      if ("defined" in ty.type) {
        const defined = ty.type.defined
        const filtered = idl.types?.filter((t) => t.name === defined) ?? []
        if (filtered.length !== 1) {
          throw new Error(`Defined type not found: ${JSON.stringify(ty)}`)
        }

        switch (filtered[0].type.kind) {
          case "struct":
          case "enum":
            return `${valPrefix}${ty.name}.toJSON()`
          default: {
            unreachable(filtered[0].type)
            throw new Error("Unreachable.")
          }
        }
      }

      unreachable(ty.type)
      throw new Error("Unreachable.")
  }
}

export function idlTypeToJSONType(
  ty: IdlType,
  definedTypesPrefix = "types."
): string {
  switch (ty) {
    case "bool":
      return "boolean"
    case "u8":
    case "i8":
    case "u16":
    case "i16":
    case "u32":
    case "i32":
    case "f32":
    case "f64":
      return "number"
    case "string":
    case "u64":
    case "i64":
    case "u128":
    case "i128":
    case "publicKey":
      return "string"
    case "bytes":
      return "Array<number>"
    default:
      if ("vec" in ty) {
        const inner = idlTypeToJSONType(ty.vec, definedTypesPrefix)
        return `Array<${inner}>`
      }
      if ("array" in ty) {
        const inner = idlTypeToJSONType(ty.array[0], definedTypesPrefix)
        return `Array<${inner}>`
      }
      if ("option" in ty) {
        const inner = idlTypeToJSONType(ty.option, definedTypesPrefix)
        return `${inner} | null`
      }
      if ("coption" in ty) {
        const inner = idlTypeToJSONType(ty.coption, definedTypesPrefix)
        return `${inner} | null`
      }
      if ("defined" in ty) {
        return `${definedTypesPrefix}${jsonInterfaceName(ty.defined)}`
      }

      unreachable(ty)
      throw new Error("Unreachable.")
  }
}

export function fieldFromJSON(
  ty: IdlField,
  jsonParamName = "obj",
  definedTypesPrefix = "types."
): string {
  const paramPrefix = jsonParamName ? jsonParamName + "." : ""

  switch (ty.type) {
    case "bool":
    case "u8":
    case "i8":
    case "u16":
    case "i16":
    case "u32":
    case "i32":
    case "f32":
    case "f64":
    case "string":
    case "bytes":
      return `${paramPrefix}${ty.name}`
    case "u64":
    case "i64":
    case "u128":
    case "i128":
      return `new BN(${paramPrefix}${ty.name})`
    case "publicKey":
      return `new PublicKey(${paramPrefix}${ty.name})`
    default:
      if ("vec" in ty.type) {
        const mapBody = fieldFromJSON(
          {
            name: "item",
            type: ty.type.vec,
          },
          "",
          definedTypesPrefix
        )
        // skip mapping when not needed
        if (mapBody === "item") {
          return `${paramPrefix}${ty.name}`
        }
        return `${paramPrefix}${ty.name}.map((item) => ${mapBody})`
      }
      if ("array" in ty.type) {
        const mapBody = fieldFromJSON(
          {
            name: "item",
            type: ty.type.array[0],
          },
          "",
          definedTypesPrefix
        )
        // skip mapping when not needed
        if (mapBody === "item") {
          return `${paramPrefix}${ty.name}`
        }
        return `${paramPrefix}${ty.name}.map((item) => ${mapBody})`
      }
      if ("option" in ty.type) {
        const inner = fieldFromJSON(
          { name: ty.name, type: ty.type.option },
          jsonParamName,
          definedTypesPrefix
        )
        // skip coercion when not needed
        if (inner === `${paramPrefix}${ty.name}`) {
          return inner
        }
        return `(${paramPrefix}${ty.name} && ${inner}) || null`
      }
      if ("coption" in ty.type) {
        const inner = fieldFromJSON(
          { name: ty.name, type: ty.type.coption },
          jsonParamName,
          definedTypesPrefix
        )
        // skip coercion when not needed
        if (inner === `${paramPrefix}${ty.name}`) {
          return inner
        }
        return `(${paramPrefix}${ty.name} && ${inner}) || null`
      }
      if ("defined" in ty.type) {
        return `${definedTypesPrefix}${ty.type.defined}.fromJSON(${paramPrefix}${ty.name})`
      }

      unreachable(ty.type)
      throw new Error("Unreachable.")
  }
}
