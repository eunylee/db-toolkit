import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { DomainManagerPage } from './DomainManagerPage'
import * as api from '../api/domainsApi'
import type { Domain } from '../model/types'

const CUSTOM: Domain = {
  id: 2,
  name: '이메일주소',
  data_type: 'VARCHAR',
  length: 255,
  precision: null,
  scale: null,
  source: 'custom',
  usage_count: 0,
}

describe('DomainManagerPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('creates a new domain', async () => {
    vi.spyOn(api, 'listDomains').mockResolvedValue([])
    const createSpy = vi.spyOn(api, 'createDomain').mockResolvedValue(CUSTOM)

    render(<DomainManagerPage />)
    const user = userEvent.setup()

    await user.click(screen.getByText('+ 새 도메인 만들기'))
    await user.type(screen.getByLabelText('domain-name'), '이메일주소')
    await user.click(screen.getByText('만들기'))

    await waitFor(() => expect(createSpy).toHaveBeenCalled())
  })

  it('edits an existing custom domain', async () => {
    vi.spyOn(api, 'listDomains').mockResolvedValue([CUSTOM])
    const updateSpy = vi.spyOn(api, 'updateDomain').mockResolvedValue({ ...CUSTOM, length: 320 })

    render(<DomainManagerPage />)
    const user = userEvent.setup()

    await screen.findByText('이메일주소')
    await user.click(screen.getByText('수정'))
    await user.click(screen.getByText('수정 저장'))

    await waitFor(() => expect(updateSpy).toHaveBeenCalledWith(2, expect.objectContaining({ name: '이메일주소' })))
  })

  it('deletes a custom domain', async () => {
    vi.spyOn(api, 'listDomains').mockResolvedValue([CUSTOM])
    const deleteSpy = vi.spyOn(api, 'deleteDomain').mockResolvedValue(undefined)

    render(<DomainManagerPage />)
    const user = userEvent.setup()

    await screen.findByText('이메일주소')
    await user.click(screen.getByText('삭제'))

    await waitFor(() => expect(deleteSpy).toHaveBeenCalledWith(2))
  })

  it('shows an error message when deleting a standard domain fails', async () => {
    const standard: Domain = { ...CUSTOM, source: 'custom' }
    vi.spyOn(api, 'listDomains').mockResolvedValue([standard])
    vi.spyOn(api, 'deleteDomain').mockRejectedValue(new Error('표준 도메인은 삭제 불가'))

    render(<DomainManagerPage />)
    const user = userEvent.setup()

    await screen.findByText('이메일주소')
    await user.click(screen.getByText('삭제'))

    expect(await screen.findByText(/삭제에 실패/)).toBeInTheDocument()
  })
})
