import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AddTermModal } from './AddTermModal'
import * as dictionaryApi from '../api/dictionaryApi'
import * as domainsApi from '../../domains/api/domainsApi'
import type { Domain } from '../../domains/model/types'

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

describe('AddTermModal', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('requires abbreviation and domain before submitting', async () => {
    const addTermSpy = vi.spyOn(dictionaryApi, 'addTerm')
    render(<AddTermModal term="VIP" onRegistered={() => {}} onClose={() => {}} />)
    const user = userEvent.setup()

    await user.click(screen.getByText('등록'))

    expect(await screen.findByText(/모두 지정해주세요/)).toBeInTheDocument()
    expect(addTermSpy).not.toHaveBeenCalled()
  })

  it('registers the term with chosen domain and calls onRegistered', async () => {
    vi.spyOn(domainsApi, 'listDomains').mockResolvedValue([DOMAIN])
    const addTermSpy = vi.spyOn(dictionaryApi, 'addTerm').mockResolvedValue({
      term: 'VIP',
      abbreviation: 'VIP',
      data_type: 'VARCHAR',
      length: 100,
      precision: null,
      scale: null,
    })
    const onRegistered = vi.fn()

    render(<AddTermModal term="VIP" onRegistered={onRegistered} onClose={() => {}} />)
    const user = userEvent.setup()

    await user.type(screen.getByLabelText('new-term-abbreviation'), 'VIP')
    await user.click(screen.getByText('도메인 선택'))
    await screen.findByRole('dialog', { name: '도메인 선택' })
    await user.click(screen.getByText('선택'))
    await user.click(screen.getByText('등록'))

    await waitFor(() =>
      expect(addTermSpy).toHaveBeenCalledWith({
        term: 'VIP',
        abbreviation: 'VIP',
        data_type: 'VARCHAR',
        length: 100,
        precision: null,
        scale: null,
      }),
    )
    expect(onRegistered).toHaveBeenCalled()
  })

  it('shows an error message when registration fails', async () => {
    vi.spyOn(domainsApi, 'listDomains').mockResolvedValue([DOMAIN])
    vi.spyOn(dictionaryApi, 'addTerm').mockRejectedValue(new Error('boom'))

    render(<AddTermModal term="VIP" onRegistered={() => {}} onClose={() => {}} />)
    const user = userEvent.setup()

    await user.type(screen.getByLabelText('new-term-abbreviation'), 'VIP')
    await user.click(screen.getByText('도메인 선택'))
    await screen.findByRole('dialog', { name: '도메인 선택' })
    await user.click(screen.getByText('선택'))
    await user.click(screen.getByText('등록'))

    expect(await screen.findByText(/등록에 실패/)).toBeInTheDocument()
  })
})
