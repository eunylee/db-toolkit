export interface ErdColumn {
  logical_name: string
  physical_name: string
  is_pk: boolean
}

export interface ErdTable {
  logical_name: string
  physical_name: string
  columns: ErdColumn[]
}
