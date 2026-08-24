import { formatDomainType, type Domain } from '../model/types'

interface Props {
  domains: Domain[]
  onSelect?: (domain: Domain) => void
  onEdit?: (domain: Domain) => void
  onDelete?: (domain: Domain) => void
}

export function DomainList({ domains, onSelect, onEdit, onDelete }: Props) {
  return (
    <table className="domain-list">
      <thead>
        <tr>
          <th>이름</th>
          <th>타입</th>
          <th>출처</th>
          <th>사용횟수</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {domains.map((d) => (
          <tr key={`${d.source}-${d.name}`}>
            <td>{d.name}</td>
            <td>{formatDomainType(d)}</td>
            <td>{d.source === 'standard' ? '표준' : '커스텀'}</td>
            <td>{d.usage_count}</td>
            <td>
              {onSelect && <button onClick={() => onSelect(d)}>선택</button>}
              {onEdit && d.source === 'custom' && <button onClick={() => onEdit(d)}>수정</button>}
              {onDelete && d.source === 'custom' && <button onClick={() => onDelete(d)}>삭제</button>}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
