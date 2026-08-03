import { useState } from 'react'
import { createEmptyDomainDraft, type DataType, type DomainDraft } from '../model/types'

interface Props {
  initial?: DomainDraft
  onSubmit: (draft: DomainDraft) => void
  onCancel?: () => void
  submitLabel?: string
}

export function DomainForm({ initial, onSubmit, onCancel, submitLabel = '저장' }: Props) {
  const [draft, setDraft] = useState<DomainDraft>(initial ?? createEmptyDomainDraft())

  return (
    <div className="domain-form">
      <input
        aria-label="domain-name"
        placeholder="도메인 이름 (예: 이메일주소)"
        value={draft.name}
        onChange={(e) => setDraft({ ...draft, name: e.target.value })}
      />
      <select
        aria-label="domain-data-type"
        value={draft.data_type}
        onChange={(e) => setDraft({ ...draft, data_type: e.target.value as DataType })}
      >
        <option value="VARCHAR">VARCHAR</option>
        <option value="CHAR">CHAR</option>
        <option value="NUMBER">NUMBER</option>
        <option value="DATE">DATE</option>
      </select>
      <input
        aria-label="domain-length"
        type="number"
        placeholder="길이"
        value={draft.length ?? ''}
        onChange={(e) => setDraft({ ...draft, length: e.target.value ? Number(e.target.value) : null })}
      />
      <input
        aria-label="domain-precision"
        type="number"
        placeholder="정밀도"
        value={draft.precision ?? ''}
        onChange={(e) => setDraft({ ...draft, precision: e.target.value ? Number(e.target.value) : null })}
      />
      <input
        aria-label="domain-scale"
        type="number"
        placeholder="스케일"
        value={draft.scale ?? ''}
        onChange={(e) => setDraft({ ...draft, scale: e.target.value ? Number(e.target.value) : null })}
      />
      <button onClick={() => onSubmit(draft)}>{submitLabel}</button>
      {onCancel && <button onClick={onCancel}>취소</button>}
    </div>
  )
}
