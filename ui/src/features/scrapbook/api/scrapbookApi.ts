import { api } from '../../../shared/api/client'

export interface ParsedGrid {
  rows: string[][]
  row_count: number
  column_count: number
}

export function parseGridText(rawText: string): Promise<ParsedGrid> {
  return api.post<ParsedGrid>('/scrapbook/parse', { raw_text: rawText })
}
