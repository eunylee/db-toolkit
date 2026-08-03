import { useState } from 'react'
import { createDomain, deleteDomain, updateDomain } from '../api/domainsApi'
import type { Domain, DomainDraft } from '../model/types'
import { DomainForm } from './DomainForm'
import { DomainList } from './DomainList'
import { useDomainSearch } from './useDomainSearch'
import './domains.css'

export function DomainManagerPage() {
  const [query, setQuery] = useState('')
  const { domains, refresh } = useDomainSearch(query)
  const [editing, setEditing] = useState<Domain | null>(null)
  const [creating, setCreating] = useState(false)
  const [status, setStatus] = useState<string | null>(null)

  async function handleCreate(draft: DomainDraft) {
    try {
      await createDomain(draft)
      setCreating(false)
      setStatus(null)
      refresh()
    } catch {
      setStatus('도메인 생성에 실패했습니다.')
    }
  }

  async function handleUpdate(draft: DomainDraft) {
    if (editing?.id == null) return
    try {
      await updateDomain(editing.id, draft)
      setEditing(null)
      setStatus(null)
      refresh()
    } catch {
      setStatus('도메인 수정에 실패했습니다. (표준 도메인은 수정할 수 없습니다)')
    }
  }

  async function handleDelete(domain: Domain) {
    if (domain.id == null) return
    try {
      await deleteDomain(domain.id)
      refresh()
    } catch {
      setStatus('도메인 삭제에 실패했습니다. (표준 도메인은 삭제할 수 없습니다)')
    }
  }

  return (
    <div className="domain-manager">
      <input placeholder="도메인 검색 (예: 명V100, 이메일)" value={query} onChange={(e) => setQuery(e.target.value)} />
      {status && <p className="domain-manager__status">{status}</p>}

      <DomainList domains={domains} onEdit={setEditing} onDelete={handleDelete} />

      {editing && (
        <DomainForm initial={editing} onSubmit={handleUpdate} onCancel={() => setEditing(null)} submitLabel="수정 저장" />
      )}

      {creating ? (
        <DomainForm onSubmit={handleCreate} onCancel={() => setCreating(false)} submitLabel="만들기" />
      ) : (
        <button onClick={() => setCreating(true)}>+ 새 도메인 만들기</button>
      )}
    </div>
  )
}
