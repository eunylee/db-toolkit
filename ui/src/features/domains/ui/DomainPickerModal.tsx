import { useState } from 'react'
import { createDomain } from '../api/domainsApi'
import type { Domain, DomainDraft } from '../model/types'
import { DomainForm } from './DomainForm'
import { DomainList } from './DomainList'
import { useDomainSearch } from './useDomainSearch'
import './domains.css'

interface Props {
  onSelect: (domain: Domain) => void
  onClose: () => void
}

// 테이블 설계 화면에서 컬럼의 도메인을 지정할 때 뜨는 팝업. 기존 도메인 검색/선택 +
// 맞는 게 없으면 그 자리에서 새 도메인을 만들어 바로 선택까지 이어준다.
export function DomainPickerModal({ onSelect, onClose }: Props) {
  const [query, setQuery] = useState('')
  const { domains, refresh } = useDomainSearch(query)
  const [creating, setCreating] = useState(false)
  const [status, setStatus] = useState<string | null>(null)

  async function handleCreate(draft: DomainDraft) {
    try {
      const created = await createDomain(draft)
      refresh()
      onSelect(created)
    } catch {
      setStatus('도메인 생성에 실패했습니다.')
    }
  }

  return (
    <div className="domain-picker-overlay" role="dialog" aria-label="도메인 선택">
      <div className="domain-picker">
        <div className="domain-picker__header">
          <h3>도메인 선택</h3>
          <button aria-label="닫기" onClick={onClose}>
            ×
          </button>
        </div>
        <input placeholder="도메인 검색 (예: 명V100, 이메일)" value={query} onChange={(e) => setQuery(e.target.value)} />
        {status && <p className="domain-manager__status">{status}</p>}
        <DomainList domains={domains} onSelect={onSelect} />
        {creating ? (
          <DomainForm onSubmit={handleCreate} onCancel={() => setCreating(false)} submitLabel="만들고 선택" />
        ) : (
          <button onClick={() => setCreating(true)}>+ 새 도메인 만들기</button>
        )}
      </div>
    </div>
  )
}
