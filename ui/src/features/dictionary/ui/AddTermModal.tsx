import { useEffect, useState } from 'react'
import { addTerm, checkTermExists, getAbbreviationSuggestions, getSplitCandidates } from '../api/dictionaryApi'
import type { AbbreviationSuggestion, SplitCandidate } from '../model/types'
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
  isDomainWord: boolean
  domain: Domain | null
  registered: boolean
  status: string | null
  suggestions: AbbreviationSuggestion[] | null
}

function toRowState(candidate: SplitCandidate): CandidateRowState {
  return {
    candidate,
    abbreviation: '',
    isDomainWord: false,
    domain: null,
    registered: candidate.exists,
    status: null,
    suggestions: null,
  }
}

// F-103 보완 흐름: 미등록 구간("외부URL" 등)을 문자종류 경계로 쪼갠 단어 후보별로
// 보여준다. 이미 사전에 있는 단어는 재사용하고, 없는 단어만 순서대로 등록하게 해서
// 통짜 복합어 하나로 등록되는 것을 막는다(그래야 "URL" 같은 단어가 다른 조합에도 재사용됨).
export function AddTermModal({ term, onRegistered, onClose }: Props) {
  const [rows, setRows] = useState<CandidateRowState[] | null>(null)
  const [manualSplitText, setManualSplitText] = useState('')
  const [pickingDomainFor, setPickingDomainFor] = useState<number | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    getSplitCandidates(term)
      .then((candidates) => {
        if (!cancelled) {
          setRows(candidates.map(toRowState))
          setManualSplitText(candidates.map((c) => c.term).join(' '))
        }
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

  // 미등록 후보마다 약어 추천을 조회한다("참조" -> RFRNC 같은 통계적 추천, 형태소 분석 아님).
  useEffect(() => {
    rows?.forEach((row, i) => {
      if (row.registered || row.suggestions !== null) return
      getAbbreviationSuggestions(row.candidate.term)
        .then((suggestions) => updateRow(i, { suggestions }))
        .catch(() => updateRow(i, { suggestions: [] }))
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rows])

  async function handleResplit() {
    const tokens = manualSplitText.split(/\s+/).filter(Boolean)
    if (tokens.length === 0) return
    setLoadError(null)
    try {
      const candidates = await Promise.all(tokens.map((t) => checkTermExists(t)))
      setRows(candidates.map(toRowState))
    } catch {
      setLoadError('단어 확인에 실패했습니다.')
    }
  }

  async function handleRegister(index: number) {
    const row = rows![index]
    if (!row.abbreviation.trim()) {
      updateRow(index, { status: '물리명(약어)을 입력해주세요.' })
      return
    }
    if (row.isDomainWord && !row.domain) {
      updateRow(index, { status: '도메인 단어는 도메인을 지정해주세요.' })
      return
    }
    try {
      await addTerm({
        term: row.candidate.term,
        abbreviation: row.abbreviation,
        is_domain_word: row.isDomainWord,
        data_type: row.isDomainWord && row.domain ? row.domain.data_type : 'UNKNOWN',
        length: row.isDomainWord ? (row.domain?.length ?? null) : null,
        precision: row.isDomainWord ? (row.domain?.precision ?? null) : null,
        scale: row.isDomainWord ? (row.domain?.scale ?? null) : null,
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
            × 닫기
          </button>
        </div>

        {loadError && <p className="add-term-modal__status">{loadError}</p>}

        <div className="add-term-modal__resplit">
          <label>
            직접 나누기 (띄어쓰기로 구분, 예: 외부 참조 키)
            <input
              aria-label="manual-split-input"
              value={manualSplitText}
              onChange={(e) => setManualSplitText(e.target.value)}
            />
          </label>
          <button type="button" onClick={handleResplit}>
            다시 나누기
          </button>
        </div>

        {rows?.map((row, i) => (
          <div key={`${row.candidate.term}-${i}`} className="add-term-modal__row">
            {row.registered ? (
              <p>
                {row.candidate.term}: {row.candidate.exists ? '이미 있음' : '등록됨'} —{' '}
                {row.candidate.exists ? row.candidate.abbreviation : row.abbreviation}
                {row.candidate.exists
                  ? row.candidate.is_domain_word
                    ? ` (${formatDomainType({
                        data_type: row.candidate.data_type ?? 'UNKNOWN',
                        length: row.candidate.length,
                        precision: row.candidate.precision,
                        scale: row.candidate.scale,
                      })})`
                    : ''
                  : row.isDomainWord && row.domain
                    ? ` (${formatDomainType(row.domain)})`
                    : ''}
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
                {row.suggestions && row.suggestions.length > 0 && (
                  <span className="add-term-modal__suggestions">
                    추천:{' '}
                    {row.suggestions.map((s) => (
                      <button
                        key={s.token}
                        type="button"
                        className="add-term-modal__suggestion-chip"
                        onClick={() => updateRow(i, { abbreviation: s.token })}
                      >
                        {s.token} ({s.count})
                      </button>
                    ))}
                  </span>
                )}
                <label className="add-term-modal__domain-word-toggle">
                  <input
                    type="checkbox"
                    aria-label={`is-domain-word-${i}`}
                    checked={row.isDomainWord}
                    onChange={(e) => updateRow(i, { isDomainWord: e.target.checked })}
                  />
                  도메인 단어
                </label>
                {row.isDomainWord && (
                  <>
                    <span>{row.domain ? formatDomainType(row.domain) : '도메인 미지정'}</span>
                    <button type="button" onClick={() => setPickingDomainFor(i)}>
                      도메인 선택
                    </button>
                  </>
                )}
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
