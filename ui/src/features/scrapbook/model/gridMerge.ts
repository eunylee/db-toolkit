// 화면(ScrapbookGrid)과 분리된 순수 로직: 엑셀처럼 특정 셀(anchor)에 붙여넣은
// 2차원 데이터를 기존 그리드에 병합한다. 기존 그리드보다 커지면 자동으로 확장한다.
export type Grid = string[][]

export function createEmptyGrid(rows: number, cols: number): Grid {
  return Array.from({ length: rows }, () => Array.from({ length: cols }, () => ''))
}

export function mergeGridAt(existing: Grid, incoming: Grid, anchorRow: number, anchorCol: number): Grid {
  if (incoming.length === 0) return existing

  const incomingCols = Math.max(...incoming.map((row) => row.length))
  const neededRows = anchorRow + incoming.length
  const neededCols = anchorCol + incomingCols
  const totalRows = Math.max(existing.length, neededRows)
  const totalCols = Math.max(existing[0]?.length ?? 0, neededCols)

  const result: Grid = Array.from({ length: totalRows }, (_, r) =>
    Array.from({ length: totalCols }, (_, c) => existing[r]?.[c] ?? ''),
  )

  incoming.forEach((row, ri) => {
    row.forEach((cell, ci) => {
      result[anchorRow + ri][anchorCol + ci] = cell
    })
  })

  return result
}
