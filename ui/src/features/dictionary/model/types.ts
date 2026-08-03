export type DataType = 'VARCHAR' | 'CHAR' | 'NUMBER' | 'DATE' | 'UNKNOWN'

export interface DictionaryTermPayload {
  term: string
  abbreviation: string
  data_type: DataType
  length: number | null
  precision: number | null
  scale: number | null
}

export interface SplitCandidate {
  term: string
  exists: boolean
  abbreviation: string | null
  data_type: DataType | null
  length: number | null
  precision: number | null
  scale: number | null
}
