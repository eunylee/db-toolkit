import { ApiError, api } from '../../../shared/api/client'
import type { AbbreviationSuggestion, DataType, DictionaryTermPayload, SplitCandidate } from '../model/types'

// 백엔드 /words 엔드포인트의 필드명(word 등)과, 이 파일이 노출하는 TS 계약(term 등)을
// 여기서 흡수한다 — 단어(word)/용어(term) 분리는 백엔드 스키마 사정이고, 이 모듈을 쓰는
// 화면 코드(AddTermModal 등)는 그 사정을 몰라도 되게 유지한다.
interface WordResponse {
  word: string
  abbreviation: string
  is_domain_word: boolean
  data_type: DataType
  length: number | null
  precision: number | null
  scale: number | null
}

function toDictionaryTermPayload(w: WordResponse): DictionaryTermPayload {
  return {
    term: w.word,
    abbreviation: w.abbreviation,
    is_domain_word: w.is_domain_word,
    data_type: w.data_type,
    length: w.length,
    precision: w.precision,
    scale: w.scale,
  }
}

export function addTerm(payload: DictionaryTermPayload): Promise<DictionaryTermPayload> {
  return api
    .post<WordResponse>('/words', {
      word: payload.term,
      abbreviation: payload.abbreviation,
      is_domain_word: payload.is_domain_word,
      domain_name: '',
      data_type: payload.data_type,
      length: payload.length,
      precision: payload.precision,
      scale: payload.scale,
    })
    .then(toDictionaryTermPayload)
}

export function getSplitCandidates(text: string): Promise<SplitCandidate[]> {
  return api.get<SplitCandidate[]>(`/words/split-candidates?text=${encodeURIComponent(text)}`)
}

/** 이 단어가 접두/접미로 들어간 기존 용어들의 약어 패턴에서 추천안을 가져온다. */
export function getAbbreviationSuggestions(word: string): Promise<AbbreviationSuggestion[]> {
  return api.get<AbbreviationSuggestion[]>(`/dictionary/abbreviation-suggestions?word=${encodeURIComponent(word)}`)
}

/** 사용자가 직접 지정한 단어 하나가 사전에 이미 있는지 확인한다 (수동 재분리용). */
export async function checkTermExists(term: string): Promise<SplitCandidate> {
  try {
    const found = await api.get<WordResponse>(`/words/lookup?word=${encodeURIComponent(term)}`)
    return {
      term,
      exists: true,
      is_domain_word: found.is_domain_word,
      abbreviation: found.abbreviation,
      data_type: found.data_type,
      length: found.length,
      precision: found.precision,
      scale: found.scale,
    }
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) {
      return {
        term,
        exists: false,
        is_domain_word: false,
        abbreviation: null,
        data_type: null,
        length: null,
        precision: null,
        scale: null,
      }
    }
    throw e
  }
}
