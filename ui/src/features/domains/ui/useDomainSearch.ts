import { useEffect, useState } from 'react'
import { listDomains } from '../api/domainsApi'
import type { Domain } from '../model/types'

export function useDomainSearch(query: string) {
  const [domains, setDomains] = useState<Domain[]>([])
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    let cancelled = false
    listDomains(query || undefined).then((result) => {
      if (!cancelled) setDomains(result)
    })
    return () => {
      cancelled = true
    }
  }, [query, refreshKey])

  return { domains, refresh: () => setRefreshKey((k) => k + 1) }
}
