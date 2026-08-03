import { useEffect, useState } from 'react'
import { addTerm, getSplitCandidates } from '../api/dictionaryApi'
import type { SplitCandidate } from '../model/types'
import { DomainPickerModal } from '../../domains/ui/DomainPickerModal'
import { formatDomainType, type Domain } from '../../domains/model/types'
import './AddTermModal.css'

interface Props {
  term: string
  onRegistered: () => void
  onClose: () => void
}

interface CandidateRowState {
  candidate: SplitCandidate
  abbreviation: string
  domain: Domain | null
  registered: boolean
  status: string | null
}

function toRowState(candidate: SplitCandidate): CandidateRowState {
  return { candidate, abbreviation: '', domain: null, registered: candidate.exists, status: null }
}

// F-103 보완 흐름: 미등록 구간("외부URL" 등)을 문자종류 경계로 쪼갠 단어 후보별로
// 보여준다. 이미 사전에 있는 단어는 재사용하고, 없는 단어만 순서대로 등록하게 해서
// 통짜 복합어 하나로 등록되는 것을 막는다(그래야 "URL" 같은 단어가 다른 조합에도 재사용됨).
export function AddTermModal({ term, onRegistered, onClose }: Props) {
  const [rows, setRows] = useState<CandidateRowState[] | null>(null)
  const [pickingDomainFor, setPickingDomainFor] = useState<number | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    getSplitCandidates(term)
      .then((candidates) => {
        if (!cancelled) setRows(candidates.map(toRowState))
      })
      .catch(() => {
        if (!cancelled) setLoadError('단어 분리에 실패했습니다.')
      })
    return () => {
      cancelled = true
    }
  }, [term])

  const allResolved = rows !== null && rows.every((r) => r.registered)

  function updateRow(index: number, patch: Partial<CandidateRowState>) {
    setRows((prev) => prev!.map((r, i) => (i === index ? { ...r, ...patch } : r)))
  }

  async function handleRegister(index: number) {
    const row = rows![index]
    if (!row.abbreviation.trim() || !row.domain) {
      updateRow(index, { status: '물리명(약어)과 도메인을 모두 지정해주세요.' })
      return
    }
    try {
      await addTerm({
        term: row.candidate.term,
        abbreviation: row.abbreviation,
        data_type: row.domain.data_type,
        length: row.domain.length,
        precision: row.domain.precision,
        scale: row.domain.scale,
      })
      updateRow(index, { registered: true, status: null })
    } catch {
      updateRow(index, { status: '등록에 실패했습니다.' })
    }
  }

  return (
    <div className="add-term-overlay" role="dialog" aria-label="사전에 추가">
      <div className="add-term-modal">
        <div className="add-term-modal__header">
          <h3>사전에 추가: {term}</h3>
          <button aria-label="닫기" onClick={onClose}>
            ×
          </button>
        </div>

        {loadError && <p className="add-term-modal__status">{loadError}</p>}

        {rows?.map((row, i) => (
          <div key={`${row.candidate.term}-${i}`} className="add-term-modal__row">
            {row.registered ? (
              <p>
                {row.candidate.term}: {row.candidate.exists ? '이미 있음' : '등록됨'} —{' '}
                {row.candidate.exists
                  ? `${row.candidate.abbreviation} (${formatDomainType({
                      data_type: row.candidate.data_type ?? 'UNKNOWN',
                      length: row.candidate.length,
                      precision: row.candidate.precision,
                      scale: row.candidate.scale,
                    })})`
                  : row.abbreviation}
              </p>
            ) : (
              <>
                <span>{row.candidate.term}</span>
                <input
                  aria-label={`new-term-abbreviation-${i}`}
                  placeholder="물리명(약어)"
                  value={row.abbreviation}
                  onChange={(e) => updateRow(i, { abbreviation: e.target.value })}
                />
                <span>{row.domain ? formatDomainType(row.domain) : '도메인 미지정'}</span>
                <button type="button" onClick={() => setPickingDomainFor(i)}>
                  도메인 선택
                </button>
                <button type="button" onClick={() => handleRegister(i)}>
                  등록
                </button>
                {row.status && <p className="add-term-modal__status">{row.status}</p>}
              </>
            )}
          </div>
        ))}

        {allResolved && (
          <button
            onClick={() => {
              onRegistered()
            }}
          >
            완료
          </button>
        )}

        {pickingDomainFor !== null && (
          <DomainPickerModal
            onSelect={(domain) => {
              updateRow(pickingDomainFor, { domain })
              setPickingDomainFor(null)
            }}
            onClose={() => setPickingDomainFor(null)}
          />
        )}
      </div>
    </div>
  )
}
