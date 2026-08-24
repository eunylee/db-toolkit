import { useState } from 'react'
import { applySuggestion, createEmptyColumn, toTablePayload } from '../model/columnDraft'
import type { ColumnDraft } from '../model/types'
import { saveTable, suggestColumns } from '../api/tableDesignerApi'
import { DomainPickerModal } from '../../domains/ui/DomainPickerModal'
import { formatDomainType, type Domain } from '../../domains/model/types'
import { AddTermModal } from '../../dictionary/ui/AddTermModal'
import './TableDesigner.css'

export function TableDesigner() {
  const [tableLogicalName, setTableLogicalName] = useState('')
  const [tablePhysicalName, setTablePhysicalName] = useState('')
  const [columns, setColumns] = useState<ColumnDraft[]>([createEmptyColumn()])
  const [status, setStatus] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [domainPickerFor, setDomainPickerFor] = useState<number | null>(null)
  const [addTermTarget, setAddTermTarget] = useState<{ columnIndex: number; term: string } | null>(null)

  function updateColumn(index: number, patch: Partial<ColumnDraft>) {
    setColumns((prev) => prev.map((c, i) => (i === index ? { ...c, ...patch } : c)))
  }

  function addColumn() {
    setColumns((prev) => [...prev, createEmptyColumn()])
  }

  function applyDomainToColumn(index: number, domain: Domain) {
    updateColumn(index, {
      domainName: domain.name,
      dataType: domain.data_type,
      length: domain.length,
      precision: domain.precision,
      scale: domain.scale,
    })
    setDomainPickerFor(null)
  }

  async function handleSuggest() {
    setBusy(true)
    setStatus(null)
    try {
      const suggestions = await suggestColumns(columns.map((c) => c.logicalName))
      setColumns((prev) => prev.map((c, i) => (c.logicalName.trim() ? applySuggestion(c, suggestions[i]) : c)))
    } catch {
      setStatus('물리명 제안에 실패했습니다. 엔진 서버가 실행 중인지 확인해주세요.')
    } finally {
      setBusy(false)
    }
  }

  async function refreshSuggestionForColumn(index: number) {
    const col = columns[index]
    if (!col.logicalName.trim()) return
    try {
      const [suggestion] = await suggestColumns([col.logicalName])
      setColumns((prev) => prev.map((c, i) => (i === index ? applySuggestion(c, suggestion) : c)))
    } catch {
      setStatus('물리명 제안 갱신에 실패했습니다.')
    }
  }

  async function handleSave() {
    setBusy(true)
    setStatus(null)
    try {
      const saved = await saveTable(toTablePayload(tableLogicalName, tablePhysicalName, columns))
      setStatus(`저장됨: ${saved.logical_name} (${saved.physical_name})`)
    } catch {
      setStatus('테이블 저장에 실패했습니다.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="table-designer">
      <div className="table-designer__header">
        <input
          placeholder="테이블 논리명 (예: 고객)"
          value={tableLogicalName}
          onChange={(e) => setTableLogicalName(e.target.value)}
        />
        <input
          placeholder="테이블 물리명 (예: CUSTOMER)"
          value={tablePhysicalName}
          onChange={(e) => setTablePhysicalName(e.target.value)}
        />
      </div>

      <div className="table-designer__toolbar">
        <button onClick={addColumn}>+ 컬럼</button>
        <button onClick={handleSuggest} disabled={busy}>
          물리명 제안 적용
        </button>
        <button onClick={handleSave} disabled={busy}>
          테이블로 저장
        </button>
      </div>

      {status && <p className="table-designer__status">{status}</p>}

      <table className="table-designer__table">
        <thead>
          <tr>
            <th>논리명</th>
            <th>물리명</th>
            <th>데이터타입</th>
            <th>PK</th>
            <th>비고</th>
          </tr>
        </thead>
        <tbody>
          {columns.map((col, i) => (
            <tr key={i}>
              <td>
                <input
                  aria-label={`logical-name-${i}`}
                  value={col.logicalName}
                  onChange={(e) => updateColumn(i, { logicalName: e.target.value })}
                />
                {col.unmatchedSegments.map((segment, si) => (
                  <p key={`${si}-${segment}`} className="table-designer__warning">
                    미등록: {segment}{' '}
                    <button type="button" onClick={() => setAddTermTarget({ columnIndex: i, term: segment })}>
                      사전에 추가
                    </button>
                  </p>
                ))}
              </td>
              <td>
                <input
                  aria-label={`physical-name-${i}`}
                  value={col.physicalName}
                  onChange={(e) => updateColumn(i, { physicalName: e.target.value })}
                />
              </td>
              <td>
                <button type="button" onClick={() => setDomainPickerFor(i)}>
                  {col.dataType === 'UNKNOWN'
                    ? '도메인 지정'
                    : `${col.domainName ? `${col.domainName} · ` : ''}${formatDomainType({
                        data_type: col.dataType,
                        length: col.length,
                        precision: col.precision,
                        scale: col.scale,
                      })}`}
                </button>
              </td>
              <td>
                <input
                  type="checkbox"
                  aria-label={`is-pk-${i}`}
                  checked={col.isPk}
                  onChange={(e) => updateColumn(i, { isPk: e.target.checked })}
                />
              </td>
              <td>
                <input
                  aria-label={`note-${i}`}
                  value={col.note}
                  onChange={(e) => updateColumn(i, { note: e.target.value })}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {domainPickerFor !== null && (
        <DomainPickerModal
          onSelect={(domain) => applyDomainToColumn(domainPickerFor, domain)}
          onClose={() => setDomainPickerFor(null)}
        />
      )}

      {addTermTarget && (
        <AddTermModal
          term={addTermTarget.term}
          onRegistered={() => {
            const { columnIndex } = addTermTarget
            setAddTermTarget(null)
            refreshSuggestionForColumn(columnIndex)
          }}
          onClose={() => setAddTermTarget(null)}
        />
      )}
    </div>
  )
}
