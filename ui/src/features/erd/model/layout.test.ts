import { describe, expect, it } from 'vitest'
import { boxHeight, computeCanvasSize, computeLayout, HEADER_H, PAD, ROW_H } from './layout'
import type { ErdTable } from './types'

function table(name: string, columnCount: number): ErdTable {
  return {
    logical_name: name,
    physical_name: name.toUpperCase(),
    columns: Array.from({ length: columnCount }, (_, i) => ({
      logical_name: `col${i}`,
      physical_name: `COL${i}`,
      is_pk: i === 0,
    })),
  }
}

describe('boxHeight', () => {
  it('grows linearly with column count', () => {
    expect(boxHeight(0)).toBe(HEADER_H + PAD)
    expect(boxHeight(3)).toBe(HEADER_H + 3 * ROW_H + PAD)
  })
})

describe('computeLayout', () => {
  it('places a single table at the origin', () => {
    const [layout] = computeLayout([table('고객', 3)])

    expect(layout.x).toBe(0)
    expect(layout.y).toBe(0)
  })

  it('places tables left-to-right within a row', () => {
    const layouts = computeLayout([table('a', 1), table('b', 1)], 3)

    expect(layouts[1].x).toBeGreaterThan(layouts[0].x)
    expect(layouts[1].y).toBe(layouts[0].y)
  })

  it('wraps to a new row after columnsPerRow tables', () => {
    const layouts = computeLayout([table('a', 1), table('b', 1), table('c', 1)], 2)

    expect(layouts[2].x).toBe(0)
    expect(layouts[2].y).toBeGreaterThan(layouts[0].y)
  })

  it('uses the tallest box in a row to determine the next row offset', () => {
    const layouts = computeLayout([table('short', 1), table('tall', 10), table('next-row', 1)], 2)

    const expectedY = layouts[1].h + 40
    expect(layouts[2].y).toBe(expectedY)
  })

  it('returns an empty array for no tables', () => {
    expect(computeLayout([])).toEqual([])
  })
})

describe('computeCanvasSize', () => {
  it('returns zero size for no layouts', () => {
    expect(computeCanvasSize([])).toEqual({ width: 0, height: 0 })
  })

  it('covers the furthest extent of all boxes', () => {
    const layouts = computeLayout([table('a', 1), table('b', 1), table('c', 1)], 2)

    const size = computeCanvasSize(layouts)

    expect(size.width).toBeGreaterThan(0)
    expect(size.height).toBeGreaterThan(0)
  })
})
