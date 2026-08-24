import { api } from '../../../shared/api/client'
import type { ErdTable } from '../model/types'

export function listTables(): Promise<ErdTable[]> {
  return api.get<ErdTable[]>('/tables')
}
