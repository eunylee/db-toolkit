import { useState } from 'react'
import type { ClipboardEvent } from 'react'
import { createEmptyGrid, mergeGridAt, type Grid } from '../model/gridMerge'
import { parseGridText } from '../api/scrapbookApi'
import './ScrapbookGrid.css'

const INITIAL_ROWS = 8
const INITIAL_COLS = 5

export function ScrapbookGrid() {
  const [grid, setGrid] = useState<Grid>(() => createEmptyGrid(INITIAL_ROWS, INITIAL_COLS))
  const [error, setError] = useState<string | null>(null)

  function handleCellChange(row: number, col: number, value: string) {
    setGrid((prev) => prev.map((r, ri) => (ri === row ? r.map((c, ci) => (ci === col ? value : c)) : r)))
  }

  async function handlePaste(event: ClipboardEvent<HTMLInputElement>, row: number, col: number) {
    const text = event.clipboardData.getData('text/plain')
    // 셀 하나짜리 텍스트는 브라우저 기본 붙여넣기에 맡긴다 (그리드 파싱 API 호출 불필요)
    if (!text.includes('\t') && !text.includes('\n')) return

    event.preventDefault()
    setError(null)
    try {
      const parsed = await parseGridText(text)
      setGrid((prev) => mergeGridAt(prev, parsed.rows, row, col))
    } catch {
      setError('붙여넣기 파싱에 실패했습니다. 엔진 서버가 실행 중인지 확인해주세요.')
    }
  }

  function addRow() {
    setGrid((prev) => [...prev, Array.from({ length: prev[0]?.length ?? INITIAL_COLS }, () => '')])
  }

  function addColumn() {
    setGrid((prev) => prev.map((row) => [...row, '']))
  }

  return (
    <div className="scrapbook">
      <div className="scrapbook__toolbar">
        <button onClick={addRow}>+ 행</button>
        <button onClick={addColumn}>+ 열</button>
      </div>
      {error && <p className="scrapbook__error">{error}</p>}
      <table className="scrapbook__table">
        <tbody>
          {grid.map((row, ri) => (
            <tr key={ri}>
              {row.map((cell, ci) => (
                <td key={ci}>
                  <input
                    value={cell}
                    onChange={(e) => handleCellChange(ri, ci, e.target.value)}
                    onPaste={(e) => handlePaste(e, ri, ci)}
                    aria-label={`cell-${ri}-${ci}`}
                  />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
