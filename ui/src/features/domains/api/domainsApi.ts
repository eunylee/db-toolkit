import { api } from '../../../shared/api/client'
import type { Domain, DomainDraft } from '../model/types'

export function listDomains(query?: string): Promise<Domain[]> {
  const qs = query ? `?query=${encodeURIComponent(query)}` : ''
  return api.get<Domain[]>(`/domains${qs}`)
}

export function createDomain(draft: DomainDraft): Promise<Domain> {
  return api.post<Domain>('/domains', draft)
}

export function updateDomain(name: string, draft: DomainDraft): Promise<Domain> {
  return api.put<Domain>(`/domains/${encodeURIComponent(name)}`, draft)
}

export function deleteDomain(name: string): Promise<void> {
  return api.delete<void>(`/domains/${encodeURIComponent(name)}`)
}
