import type { ErdTable } from './types'

// erd_notation_prototype.jsx의 치수를 그대로 재사용한다 (개체 박스 크기 규칙).
export const HEADER_H = 34
export const ROW_H = 24
export const PAD = 10
export const BOX_W = 210
const GAP_X = 40
const GAP_Y = 40

export function boxHeight(columnCount: number): number {
  return HEADER_H + columnCount * ROW_H + PAD
}

export interface TableLayout {
  table: ErdTable
  x: number
  y: number
  w: number
  h: number
}

/** 관계선이 없는 상태(Unit 4)이므로 테이블을 그리드로 자동 배치한다. */
export function computeLayout(tables: ErdTable[], columnsPerRow = 3): TableLayout[] {
  let x = 0
  let y = 0
  let rowMaxH = 0
  const result: TableLayout[] = []

  tables.forEach((table, i) => {
    const col = i % columnsPerRow
    if (col === 0 && i > 0) {
      y += rowMaxH + GAP_Y
      x = 0
      rowMaxH = 0
    }

    const h = boxHeight(table.columns.length)
    result.push({ table, x, y, w: BOX_W, h })
    rowMaxH = Math.max(rowMaxH, h)
    x += BOX_W + GAP_X
  })

  return result
}

export function computeCanvasSize(layouts: TableLayout[]): { width: number; height: number } {
  if (layouts.length === 0) return { width: 0, height: 0 }
  const width = Math.max(...layouts.map((l) => l.x + l.w))
  const height = Math.max(...layouts.map((l) => l.y + l.h))
  return { width, height }
}
