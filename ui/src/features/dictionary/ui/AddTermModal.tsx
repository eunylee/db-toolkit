import { useState } from 'react'
import { addTerm } from '../api/dictionaryApi'
import { DomainPickerModal } from '../../domains/ui/DomainPickerModal'
import { formatDomainType, type Domain } from '../../domains/model/types'
import './AddTermModal.css'

interface Props {
  term: string
  onRegistered: () => void
  onClose: () => void
}

// F-103 보완 흐름: 세그먼터가 "미등록"으로 표시한 단어를 그 자리에서 바로
// 커스텀 사전에 등록할 수 있게 한다("자동 추천 + 사용자 확정"의 확정 경로).
export function AddTermModal({ term, onRegistered, onClose }: Props) {
  const [abbreviation, setAbbreviation] = useState('')
  const [domain, setDomain] = useState<Domain | null>(null)
  const [pickingDomain, setPickingDomain] = useState(false)
  const [status, setStatus] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function handleSubmit() {
    if (!abbreviation.trim() || !domain) {
      setStatus('물리명(약어)과 도메인을 모두 지정해주세요.')
      return
    }
    setBusy(true)
    setStatus(null)
    try {
      await addTerm({
        term,
        abbreviation,
        data_type: domain.data_type,
        length: domain.length,
        precision: domain.precision,
        scale: domain.scale,
      })
      onRegistered()
    } catch {
      setStatus('사전 등록에 실패했습니다.')
    } finally {
      setBusy(false)
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

        <label>
          물리명(약어)
          <input
            aria-label="new-term-abbreviation"
            value={abbreviation}
            onChange={(e) => setAbbreviation(e.target.value)}
          />
        </label>

        <div>
          도메인:{' '}
          {domain ? (
            formatDomainType(domain)
          ) : (
            <span className="add-term-modal__empty">지정 안 됨</span>
          )}{' '}
          <button type="button" onClick={() => setPickingDomain(true)}>
            도메인 선택
          </button>
        </div>

        {status && <p className="add-term-modal__status">{status}</p>}

        <button onClick={handleSubmit} disabled={busy}>
          등록
        </button>

        {pickingDomain && (
          <DomainPickerModal
            onSelect={(d) => {
              setDomain(d)
              setPickingDomain(false)
            }}
            onClose={() => setPickingDomain(false)}
          />
        )}
      </div>
    </div>
  )
}
