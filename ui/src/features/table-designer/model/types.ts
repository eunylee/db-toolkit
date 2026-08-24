export type DataType = 'VARCHAR' | 'CHAR' | 'NUMBER' | 'DATE' | 'UNKNOWN'

export interface DictionaryTerm {
  term: string
  abbreviation: string
  data_type: DataType
  length: number | null
}

export interface MatchedSegment {
  text: string
  matched: boolean
  term: DictionaryTerm | null
}

export interface ColumnSuggestion {
  logical_name: string
  physical_name_suggestion: string | null
  fully_matched: boolean
  segments: MatchedSegment[]
  domain_name: string
  data_type: DataType
  length: number | null
  precision: number | null
  scale: number | null
}

export interface ColumnDraft {
  logicalName: string
  physicalName: string
  domainName: string
  dataType: DataType
  length: number | null
  precision: number | null
  scale: number | null
  isPk: boolean
  note: string
  unmatchedSegments: string[]
}

export interface TablePayload {
  logical_name: string
  physical_name: string
  columns: {
    logical_name: string
    physical_name: string
    data_type: DataType
    length: number | null
    precision: number | null
    scale: number | null
    is_pk: boolean
    note: string
  }[]
}
