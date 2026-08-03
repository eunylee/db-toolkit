import { api } from '../../../shared/api/client'
import type { DictionaryTermPayload } from '../model/types'

export function addTerm(payload: DictionaryTermPayload): Promise<DictionaryTermPayload> {
  return api.post<DictionaryTermPayload>('/dictionary/terms', payload)
}
