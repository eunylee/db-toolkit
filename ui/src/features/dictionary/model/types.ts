export type DataType = 'VARCHAR' | 'CHAR' | 'NUMBER' | 'DATE' | 'UNKNOWN'

export interface DictionaryTermPayload {
  term: string
  abbreviation: string
  data_type: DataType
  length: number | null
  precision: number | null
  scale: number | null
}
