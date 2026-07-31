import { describe, expect, it } from 'vitest'
import { applySuggestion, createEmptyColumn, toTablePayload } from './columnDraft'
import type { ColumnSuggestion } from './types'

describe('createEmptyColumn', () => {
  it('creates a blank column draft', () => {
    const col = createEmptyColumn()

    expect(col.logicalName).toBe('')
    expect(col.isPk).toBe(false)
    expect(col.unmatchedSegments).toEqual([])
  })
})

describe('applySuggestion', () => {
  it('fills physical name and data type when fully matched', () => {
    const column = { ...createEmptyColumn(), logicalName: '고객명' }
    const suggestion: ColumnSuggestion = {
      logical_name: '고객명',
      physical_name_suggestion: 'CUST_NM',
      fully_matched: true,
      segments: [{ text: '고객명', matched: true, term: null }],
      data_type: 'VARCHAR',
      length: 100,
      precision: null,
      scale: null,
    }

    const result = applySuggestion(column, suggestion)

    expect(result.physicalName).toBe('CUST_NM')
    expect(result.dataType).toBe('VARCHAR')
    expect(result.length).toBe(100)
    expect(result.unmatchedSegments).toEqual([])
  })

  it('keeps user-entered physical name and reports unmatched segments on partial match', () => {
    const column = { ...createEmptyColumn(), logicalName: 'VIP고객명', physicalName: 'MY_MANUAL_NAME' }
    const suggestion: ColumnSuggestion = {
      logical_name: 'VIP고객명',
      physical_name_suggestion: null,
      fully_matched: false,
      segments: [
        { text: 'VIP', matched: false, term: null },
        { text: '고객명', matched: true, term: null },
      ],
      data_type: 'VARCHAR',
      length: 100,
      precision: null,
      scale: null,
    }

    const result = applySuggestion(column, suggestion)

    expect(result.physicalName).toBe('MY_MANUAL_NAME')
    expect(result.unmatchedSegments).toEqual(['VIP'])
    // 마지막 매칭 구간('고객명') 기준으로 데이터타입은 그래도 채워준다
    expect(result.dataType).toBe('VARCHAR')
    expect(result.length).toBe(100)
  })
})

describe('toTablePayload', () => {
  it('converts drafts to the API snake_case shape and drops blank rows', () => {
    const columns = [
      { ...createEmptyColumn(), logicalName: '고객번호', physicalName: 'CUST_NO', isPk: true },
      createEmptyColumn(),
    ]

    const payload = toTablePayload('고객', 'CUSTOMER', columns)

    expect(payload).toEqual({
      logical_name: '고객',
      physical_name: 'CUSTOMER',
      columns: [
        {
          logical_name: '고객번호',
          physical_name: 'CUST_NO',
          data_type: 'UNKNOWN',
          length: null,
          precision: null,
          scale: null,
          is_pk: true,
          note: '',
        },
      ],
    })
  })
})
