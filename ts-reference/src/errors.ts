import { Idl } from "@project-serum/anchor"
import { Project, VariableDeclarationKind } from "ts-morph"
import {
  LangErrorCode,
  LangErrorMessage,
} from "@project-serum/anchor/dist/cjs/error"

export function genErrors(
  project: Project,
  idl: Idl,
  outPath: (path: string) => string
) {
  genIndex(project, idl, outPath)
  genCustomErrors(project, idl, outPath)
  genAnchorErrors(project, idl, outPath)
}

export function genIndex(
  project: Project,
  idl: Idl,
  outPath: (path: string) => string
) {
  const src = project.createSourceFile(outPath("errors/index.ts"), "", {
    overwrite: true,
  })

  const hasCustomErrors = idl.errors && idl.errors.length > 0

  src.addImportDeclaration({
    namedImports: ["PROGRAM_ID"],
    moduleSpecifier: "../programId",
  })
  src.addImportDeclaration({
    namespaceImport: "anchor",
    moduleSpecifier: "./anchor",
  })
  if (hasCustomErrors) {
    src.addImportDeclaration({
      namespaceImport: "custom",
      moduleSpecifier: "./custom",
    })
  }

  // fromCode function
  const fromCodeFn = src.addFunction({
    isExported: true,
    name: "fromCode",
    parameters: [
      {
        name: "code",
        type: "number",
      },
    ],
    returnType: hasCustomErrors
      ? "custom.CustomError | anchor.AnchorError | null"
      : "anchor.AnchorError | null",
  })
  hasCustomErrors
    ? fromCodeFn.setBodyText(
        "return code >= 6000 ? custom.fromCode(code) : anchor.fromCode(code)"
      )
    : fromCodeFn.setBodyText("return anchor.fromCode(code)")

  // hasOwnProperty function
  const hasOwnPropertyFn = src.addFunction({
    name: "hasOwnProperty",
    typeParameters: [
      {
        name: "X extends object",
      },
      {
        name: "Y extends PropertyKey",
      },
    ],
    parameters: [
      {
        name: "obj",
        type: "X",
      },
      {
        name: "prop",
        type: "Y",
      },
    ],
    returnType: "obj is X & Record<Y, unknown>",
  })
  hasOwnPropertyFn.setBodyText("return Object.hasOwnProperty.call(obj, prop);")

  // errorRe
  src.addVariableStatement({
    declarationKind: VariableDeclarationKind.Const,
    declarations: [
      {
        name: "errorRe",
        initializer: "/Program (\\w+) failed: custom program error: (\\w+)/",
      },
    ],
  })

  // fromTxError function
  const fromTxErrorFn = src.addFunction({
    isExported: true,
    name: "fromTxError",
    parameters: [
      {
        name: "err",
        type: "unknown",
      },
    ],
    returnType: hasCustomErrors
      ? "custom.CustomError | anchor.AnchorError | null"
      : "anchor.AnchorError | null",
  })
  fromTxErrorFn.setBodyText(`if (
  typeof err !== "object" ||
  err === null ||
  !hasOwnProperty(err, "logs") ||
  !Array.isArray(err.logs)
) {
  return null
}

let firstMatch: RegExpExecArray | null = null
for (const logLine of err.logs) {
  firstMatch = errorRe.exec(logLine)
  if (firstMatch !== null) {
    break
  }
}

if (firstMatch === null) {
  return null
}

const [programIdRaw, codeRaw] = firstMatch.slice(1)
if (programIdRaw !== PROGRAM_ID.toString()) {
  return null
}

let errorCode: number
try {
  errorCode = parseInt(codeRaw, 16)
} catch (parseErr) {
  return null
}

return fromCode(errorCode)`)
}

export function genCustomErrors(
  project: Project,
  idl: Idl,
  outPath: (path: string) => string
) {
  if (!idl.errors || idl.errors.length === 0) {
    return
  }
  const errors = idl.errors

  const src = project.createSourceFile(outPath("errors/custom.ts"), "", {
    overwrite: true,
  })

  // type alias
  src.addTypeAlias({
    name: "CustomError",
    type: errors.map((error) => error.name).join(" | "),
    isExported: true,
  })

  // error classes
  errors.forEach((error) => {
    const cls = src.addClass({
      isExported: true,
      name: error.name,
      extends: "Error",
      properties: [
        {
          name: "code",
          initializer: error.code.toString(),
          isReadonly: true,
        },
        {
          name: "name",
          initializer: `"${error.name}"`,
          isReadonly: true,
        },
        {
          name: "msg",
          initializer: `"${error.msg}"`,
          isReadonly: true,
        },
      ],
    })
    const ctor = cls.addConstructor()
    ctor.setBodyText(`super("${error.code}: ${error.msg}")`)
  })

  // fromCode function
  const fromCodeFn = src.addFunction({
    isExported: true,
    name: "fromCode",
    parameters: [
      {
        name: "code",
        type: "number",
      },
    ],
    returnType: "CustomError | null",
  })
  fromCodeFn.setBodyText((writer) => {
    writer
      .writeLine("switch (code)")
      .block(() => {
        errors.forEach((error) => {
          writer.writeLine(`case ${error.code}:`).indent(() => {
            writer.writeLine(`return new ${error.name}();`)
          })
        })
      })
      .blankLine()
      .writeLine("return null")
  })
}

export function genAnchorErrors(
  project: Project,
  idl: Idl,
  outPath: (path: string) => string
) {
  const src = project.createSourceFile(outPath("errors/anchor.ts"), "", {
    overwrite: true,
  })

  // type alias
  src.addTypeAlias({
    name: "AnchorError",
    type: Object.keys(LangErrorCode).join(" | "),
    isExported: true,
  })

  // error classes
  Object.keys(LangErrorCode).forEach((errorName) => {
    const code: number = LangErrorCode[errorName]
    const message: string = LangErrorMessage.get(code) || ""

    const cls = src.addClass({
      isExported: true,
      name: errorName,
      extends: "Error",
      properties: [
        {
          name: "code",
          initializer: code.toString(),
          isReadonly: true,
        },
        {
          name: "name",
          initializer: `"${errorName}"`,
          isReadonly: true,
        },
        {
          name: "msg",
          initializer: `"${message}"`,
          isReadonly: true,
        },
      ],
    })
    const ctor = cls.addConstructor()
    ctor.setBodyText(`super("${code}: ${message}")`)
  })

  // fromCode function
  const fromCodeFn = src.addFunction({
    isExported: true,
    name: "fromCode",
    parameters: [
      {
        name: "code",
        type: "number",
      },
    ],
    returnType: "AnchorError | null",
  })
  fromCodeFn.setBodyText((writer) => {
    writer
      .writeLine("switch (code)")
      .block(() => {
        Object.keys(LangErrorCode).forEach((errorName) => {
          writer.writeLine(`case ${LangErrorCode[errorName]}:`).indent(() => {
            writer.writeLine(`return new ${errorName}();`)
          })
        })
      })
      .blankLine()
      .writeLine("return null")
  })
}
