import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { DomainPickerModal } from './DomainPickerModal'
import * as api from '../api/domainsApi'
import type { Domain } from '../model/types'

const DOMAIN: Domain = {
  id: 1,
  name: '명V100',
  data_type: 'VARCHAR',
  length: 100,
  precision: null,
  scale: null,
  source: 'standard',
  usage_count: 10,
}

describe('DomainPickerModal', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('lists domains and selects one', async () => {
    vi.spyOn(api, 'listDomains').mockResolvedValue([DOMAIN])
    const onSelect = vi.fn()
    render(<DomainPickerModal onSelect={onSelect} onClose={() => {}} />)
    const user = userEvent.setup()

    await screen.findByText('명V100')
    await user.click(screen.getByText('선택'))

    expect(onSelect).toHaveBeenCalledWith(DOMAIN)
  })

  it('creates a new domain and selects it immediately', async () => {
    vi.spyOn(api, 'listDomains').mockResolvedValue([])
    const created: Domain = { ...DOMAIN, id: 2, name: '이메일주소', source: 'custom', usage_count: 0 }
    vi.spyOn(api, 'createDomain').mockResolvedValue(created)
    const onSelect = vi.fn()

    render(<DomainPickerModal onSelect={onSelect} onClose={() => {}} />)
    const user = userEvent.setup()

    await user.click(screen.getByText('+ 새 도메인 만들기'))
    await user.type(screen.getByLabelText('domain-name'), '이메일주소')
    await user.click(screen.getByText('만들고 선택'))

    await waitFor(() => expect(onSelect).toHaveBeenCalledWith(created))
  })

  it('calls onClose when the close button is clicked', async () => {
    vi.spyOn(api, 'listDomains').mockResolvedValue([])
    const onClose = vi.fn()
    render(<DomainPickerModal onSelect={() => {}} onClose={onClose} />)
    const user = userEvent.setup()

    await user.click(screen.getByLabelText('닫기'))

    expect(onClose).toHaveBeenCalled()
  })
})
