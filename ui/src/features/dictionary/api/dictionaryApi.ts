import { api } from '../../../shared/api/client'
import type { DictionaryTermPayload, SplitCandidate } from '../model/types'

export function addTerm(payload: DictionaryTermPayload): Promise<DictionaryTermPayload> {
  return api.post<DictionaryTermPayload>('/dictionary/terms', payload)
}

export function getSplitCandidates(text: string): Promise<SplitCandidate[]> {
  return api.get<SplitCandidate[]>(`/dictionary/split-candidates?text=${encodeURIComponent(text)}`)
}
