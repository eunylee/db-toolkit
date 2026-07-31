import type { ColumnDraft, ColumnSuggestion, TablePayload } from './types'

export function createEmptyColumn(): ColumnDraft {
  return {
    logicalName: '',
    physicalName: '',
    dataType: 'UNKNOWN',
    length: null,
    precision: null,
    scale: null,
    isPk: false,
    note: '',
    unmatchedSegments: [],
  }
}

// F-103: 물리명은 전체 구간이 사전에 매칭됐을 때만 채운다(일부만 맞으면 불완전한 이름을
// 지어내지 않고 사용자가 이미 적어둔 값을 보존). 데이터타입은 한글 복합명사가 보통
// 끝 단어가 핵심이라 마지막 매칭 구간만으로도 추천 가능해서 부분 매칭이어도 채운다.
export function applySuggestion(column: ColumnDraft, suggestion: ColumnSuggestion): ColumnDraft {
  const unmatchedSegments = suggestion.segments.filter((s) => !s.matched).map((s) => s.text)

  return {
    ...column,
    physicalName: suggestion.fully_matched
      ? (suggestion.physical_name_suggestion ?? column.physicalName)
      : column.physicalName,
    dataType: suggestion.data_type,
    length: suggestion.length,
    precision: suggestion.precision,
    scale: suggestion.scale,
    unmatchedSegments,
  }
}

export function toTablePayload(logicalName: string, physicalName: string, columns: ColumnDraft[]): TablePayload {
  return {
    logical_name: logicalName,
    physical_name: physicalName,
    columns: columns
      .filter((c) => c.logicalName.trim() !== '')
      .map((c) => ({
        logical_name: c.logicalName,
        physical_name: c.physicalName,
        data_type: c.dataType,
        length: c.length,
        precision: c.precision,
        scale: c.scale,
        is_pk: c.isPk,
        note: c.note,
      })),
  }
}
