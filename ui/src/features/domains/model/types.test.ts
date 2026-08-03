import { describe, expect, it } from 'vitest'
import { formatDomainType } from './types'

describe('formatDomainType', () => {
  it('formats varchar with length', () => {
    expect(formatDomainType({ data_type: 'VARCHAR', length: 100, precision: null, scale: null })).toBe(
      'VARCHAR(100)',
    )
  })

  it('formats number with precision and scale', () => {
    expect(formatDomainType({ data_type: 'NUMBER', length: null, precision: 15, scale: 4 })).toBe('NUMBER(15,4)')
  })

  it('formats number with precision only', () => {
    expect(formatDomainType({ data_type: 'NUMBER', length: null, precision: 10, scale: null })).toBe('NUMBER(10)')
  })

  it('falls back to bare type when no length info', () => {
    expect(formatDomainType({ data_type: 'DATE', length: null, precision: null, scale: null })).toBe('DATE')
  })
})
