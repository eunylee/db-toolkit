export type DataType = 'VARCHAR' | 'CHAR' | 'NUMBER' | 'DATE' | 'UNKNOWN'

export interface Domain {
  id: number | null
  name: string
  data_type: DataType
  length: number | null
  precision: number | null
  scale: number | null
  source: 'standard' | 'custom'
  usage_count: number
}

export type DomainDraft = Pick<Domain, 'name' | 'data_type' | 'length' | 'precision' | 'scale'>

export function createEmptyDomainDraft(): DomainDraft {
  return { name: '', data_type: 'VARCHAR', length: null, precision: null, scale: null }
}

export function formatDomainType(domain: Pick<Domain, 'data_type' | 'length' | 'precision' | 'scale'>): string {
  if (domain.data_type === 'NUMBER' && domain.precision != null) {
    return `NUMBER(${domain.precision}${domain.scale != null ? `,${domain.scale}` : ''})`
  }
  if (domain.length != null) {
    return `${domain.data_type}(${domain.length})`
  }
  return domain.data_type
}
