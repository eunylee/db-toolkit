import { api } from '../../../shared/api/client'
import type { ColumnSuggestion, TablePayload } from '../model/types'

export function suggestColumns(logicalNames: string[]): Promise<ColumnSuggestion[]> {
  return api.post<ColumnSuggestion[]>('/naming/suggest', { logical_names: logicalNames })
}

export function saveTable(payload: TablePayload): Promise<TablePayload> {
  return api.post<TablePayload>('/tables', payload)
}
