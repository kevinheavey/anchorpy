import * as FooEnum from "./FooEnum"

export { BarStruct, BarStructFields, BarStructJSON } from "./BarStruct"
export { FooStruct, FooStructFields, FooStructJSON } from "./FooStruct"
export { FooEnum }

export type FooEnumKind =
  | FooEnum.Unnamed
  | FooEnum.UnnamedSingle
  | FooEnum.Named
  | FooEnum.Struct
  | FooEnum.OptionStruct
  | FooEnum.VecStruct
  | FooEnum.NoFields
export type FooEnumJSON =
  | FooEnum.UnnamedJSON
  | FooEnum.UnnamedSingleJSON
  | FooEnum.NamedJSON
  | FooEnum.StructJSON
  | FooEnum.OptionStructJSON
  | FooEnum.VecStructJSON
  | FooEnum.NoFieldsJSON
