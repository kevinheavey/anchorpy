import { Idl } from "@project-serum/anchor"
import { Project, VariableDeclarationKind } from "ts-morph"

export function genProgramId(
  project: Project,
  idl: Idl,
  cliProgramId: string | null,
  outPath: (path: string) => string
) {
  let idlProgramId: string | null = null
  if ("metadata" in idl && "address" in idl.metadata) {
    idlProgramId = idl.metadata.address
  }

  let src = project.addSourceFileAtPathIfExists(outPath("programId.ts"))

  if (src === undefined && idlProgramId === null && cliProgramId === null) {
    console.warn(
      "\nWARNING: program ID not found in the IDL nor provided with the `--program-id` flag. Edit the generated `programId.ts` file manually to return the correct program ID!\n"
    )
  }

  let programIdValue = src
    ?.getVariableDeclaration("PROGRAM_ID")
    ?.getInitializer()
    ?.getText()

  const programIdDefaultValue =
    "new PublicKey(/* edit this to return the correct program ID */)"
  if (programIdValue === programIdDefaultValue) {
    programIdValue = undefined // re-generate program id if it hasn't been manually modified
  }

  if (programIdValue === undefined) {
    programIdValue = programIdDefaultValue
    if (cliProgramId) {
      programIdValue = "PROGRAM_ID_CLI"
    } else if (idlProgramId) {
      programIdValue = "PROGRAM_ID_IDL"
    }
  }

  const importStatements = src
    ?.getImportDeclarations()
    .map((impt) => impt.getText())

  src = project.createSourceFile(outPath("programId.ts"), "", {
    overwrite: true,
  })

  if (importStatements === undefined || importStatements.length === 0) {
    src.addImportDeclaration({
      namedImports: ["PublicKey"],
      moduleSpecifier: "@solana/web3.js",
    })
  } else {
    src.addStatements(importStatements)
  }

  if (idlProgramId) {
    src.addStatements([
      "\n",
      "// Program ID defined in the provided IDL. Do not edit, it will get overwritten.",
    ])
    src.addVariableStatement({
      declarationKind: VariableDeclarationKind.Const,
      declarations: [
        {
          name: "PROGRAM_ID_IDL",
          initializer: `new PublicKey("${idlProgramId}")`,
        },
      ],
      isExported: true,
    })
  }
  if (cliProgramId) {
    src.addStatements([
      "\n",
      "// Program ID passed with the cli --program-id flag when running the code generator. Do not edit, it will get overwritten.",
    ])
    src.addVariableStatement({
      declarationKind: VariableDeclarationKind.Const,
      declarations: [
        {
          name: "PROGRAM_ID_CLI",
          initializer: `new PublicKey("${cliProgramId}")`,
        },
      ],
      isExported: true,
    })
  }

  src.addStatements([
    "\n",
    "// This constant will not get overwritten on subsequent code generations and it's safe to modify it's value.",
  ])
  src.addVariableStatement({
    isExported: true,
    declarationKind: VariableDeclarationKind.Const,
    declarations: [
      {
        name: "PROGRAM_ID",
        type: "PublicKey",
        initializer: programIdValue,
      },
    ],
  })
}
