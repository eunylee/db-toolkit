import { describe, expect, it } from 'vitest'
import { createEmptyGrid, mergeGridAt } from './gridMerge'

describe('createEmptyGrid', () => {
  it('creates a grid of the given size filled with empty strings', () => {
    const grid = createEmptyGrid(2, 3)
    expect(grid).toEqual([
      ['', '', ''],
      ['', '', ''],
    ])
  })
})

describe('mergeGridAt', () => {
  it('writes incoming cells at the anchor position without touching others', () => {
    const existing = createEmptyGrid(3, 3)
    const result = mergeGridAt(existing, [['a', 'b']], 0, 0)

    expect(result[0]).toEqual(['a', 'b', ''])
    expect(result[1]).toEqual(['', '', ''])
  })

  it('pastes starting from a non-zero anchor cell', () => {
    const existing = createEmptyGrid(3, 3)
    const result = mergeGridAt(existing, [['x']], 1, 1)

    expect(result[1][1]).toBe('x')
    expect(result[0][0]).toBe('')
  })

  it('expands the grid when incoming data overflows existing bounds', () => {
    const existing = createEmptyGrid(2, 2)
    const result = mergeGridAt(existing, [['a', 'b', 'c']], 0, 1)

    expect(result.length).toBe(2)
    expect(result[0].length).toBe(4)
    expect(result[0]).toEqual(['', 'a', 'b', 'c'])
  })

  it('expands rows when pasted block extends past the last row', () => {
    const existing = createEmptyGrid(1, 2)
    const result = mergeGridAt(existing, [['a'], ['b']], 0, 0)

    expect(result.length).toBe(2)
    expect(result[1][0]).toBe('b')
  })

  it('preserves existing cell values outside the pasted region', () => {
    const existing = [
      ['keep1', 'keep2'],
      ['keep3', 'keep4'],
    ]
    const result = mergeGridAt(existing, [['new']], 0, 0)

    expect(result[0][0]).toBe('new')
    expect(result[0][1]).toBe('keep2')
    expect(result[1]).toEqual(['keep3', 'keep4'])
  })

  it('returns the original grid unchanged when incoming is empty', () => {
    const existing = createEmptyGrid(2, 2)
    const result = mergeGridAt(existing, [], 0, 0)

    expect(result).toEqual(existing)
  })

  it('handles ragged incoming rows by padding with empty strings', () => {
    const existing = createEmptyGrid(2, 3)
    const result = mergeGridAt(existing, [['a', 'b', 'c'], ['d']], 0, 0)

    expect(result[1]).toEqual(['d', '', ''])
  })
})
