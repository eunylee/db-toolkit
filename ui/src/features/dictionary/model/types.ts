export type DataType = 'VARCHAR' | 'CHAR' | 'NUMBER' | 'DATE' | 'UNKNOWN'

export interface DictionaryTermPayload {
  term: string
  abbreviation: string
  is_domain_word: boolean
  data_type: DataType
  length: number | null
  precision: number | null
  scale: number | null
}

export interface SplitCandidate {
  term: string
  exists: boolean
  is_domain_word: boolean
  abbreviation: string | null
  data_type: DataType | null
  length: number | null
  precision: number | null
  scale: number | null
}

export interface AbbreviationSuggestion {
  token: string
  count: number
}
