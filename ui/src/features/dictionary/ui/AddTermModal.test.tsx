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

  it('splits the unmatched blob into word candidates and shows existing ones as already registered', async () => {
    vi.spyOn(dictionaryApi, 'getSplitCandidates').mockResolvedValue([
      { term: '외부', exists: true, abbreviation: 'EXT', data_type: 'VARCHAR', length: 50, precision: null, scale: null },
      { term: 'URL', exists: false, abbreviation: null, data_type: null, length: null, precision: null, scale: null },
    ])

    render(<AddTermModal term="외부URL" onRegistered={() => {}} onClose={() => {}} />)

    expect(await screen.findByText(/외부: 이미 있음/)).toBeInTheDocument()
    expect(screen.getByText('URL')).toBeInTheDocument()
    expect(screen.getByLabelText('new-term-abbreviation-1')).toBeInTheDocument()
  })

  it('registers only the missing candidate and does not touch the already-existing one', async () => {
    vi.spyOn(dictionaryApi, 'getSplitCandidates').mockResolvedValue([
      { term: '외부', exists: true, abbreviation: 'EXT', data_type: 'VARCHAR', length: 50, precision: null, scale: null },
      { term: 'URL', exists: false, abbreviation: null, data_type: null, length: null, precision: null, scale: null },
    ])
    vi.spyOn(domainsApi, 'listDomains').mockResolvedValue([DOMAIN])
    const addTermSpy = vi.spyOn(dictionaryApi, 'addTerm').mockResolvedValue({
      term: 'URL',
      abbreviation: 'URL',
      data_type: 'VARCHAR',
      length: 100,
      precision: null,
      scale: null,
    })

    render(<AddTermModal term="외부URL" onRegistered={() => {}} onClose={() => {}} />)
    const user = userEvent.setup()

    await screen.findByLabelText('new-term-abbreviation-1')
    await user.type(screen.getByLabelText('new-term-abbreviation-1'), 'URL')
    await user.click(screen.getByText('도메인 선택'))
    await screen.findByRole('dialog', { name: '도메인 선택' })
    await user.click(screen.getByText('선택'))
    await user.click(screen.getByText('등록'))

    await waitFor(() =>
      expect(addTermSpy).toHaveBeenCalledWith({
        term: 'URL',
        abbreviation: 'URL',
        data_type: 'VARCHAR',
        length: 100,
        precision: null,
        scale: null,
      }),
    )
    // '외부'는 이미 존재하던 단어라 addTerm이 그 값으로 다시 호출되지 않아야 한다
    expect(addTermSpy).toHaveBeenCalledTimes(1)
  })

  it('shows 완료 button only once every candidate is resolved', async () => {
    vi.spyOn(dictionaryApi, 'getSplitCandidates').mockResolvedValue([
      { term: '외부', exists: true, abbreviation: 'EXT', data_type: 'VARCHAR', length: 50, precision: null, scale: null },
      { term: 'URL', exists: false, abbreviation: null, data_type: null, length: null, precision: null, scale: null },
    ])
    vi.spyOn(domainsApi, 'listDomains').mockResolvedValue([DOMAIN])
    vi.spyOn(dictionaryApi, 'addTerm').mockResolvedValue({
      term: 'URL',
      abbreviation: 'URL',
      data_type: 'VARCHAR',
      length: 100,
      precision: null,
      scale: null,
    })
    const onRegistered = vi.fn()

    render(<AddTermModal term="외부URL" onRegistered={onRegistered} onClose={() => {}} />)
    const user = userEvent.setup()

    await screen.findByLabelText('new-term-abbreviation-1')
    expect(screen.queryByText('완료')).not.toBeInTheDocument()

    await user.type(screen.getByLabelText('new-term-abbreviation-1'), 'URL')
    await user.click(screen.getByText('도메인 선택'))
    await screen.findByRole('dialog', { name: '도메인 선택' })
    await user.click(screen.getByText('선택'))
    await user.click(screen.getByText('등록'))

    await screen.findByText('완료')
    await user.click(screen.getByText('완료'))

    expect(onRegistered).toHaveBeenCalled()
  })

  it('shows a per-row error message when registration fails', async () => {
    vi.spyOn(dictionaryApi, 'getSplitCandidates').mockResolvedValue([
      { term: 'URL', exists: false, abbreviation: null, data_type: null, length: null, precision: null, scale: null },
    ])
    vi.spyOn(domainsApi, 'listDomains').mockResolvedValue([DOMAIN])
    vi.spyOn(dictionaryApi, 'addTerm').mockRejectedValue(new Error('boom'))

    render(<AddTermModal term="URL" onRegistered={() => {}} onClose={() => {}} />)
    const user = userEvent.setup()

    await user.type(await screen.findByLabelText('new-term-abbreviation-0'), 'URL')
    await user.click(screen.getByText('도메인 선택'))
    await screen.findByRole('dialog', { name: '도메인 선택' })
    await user.click(screen.getByText('선택'))
    await user.click(screen.getByText('등록'))

    expect(await screen.findByText(/등록에 실패/)).toBeInTheDocument()
  })

  it('requires abbreviation and domain before allowing registration', async () => {
    vi.spyOn(dictionaryApi, 'getSplitCandidates').mockResolvedValue([
      { term: 'URL', exists: false, abbreviation: null, data_type: null, length: null, precision: null, scale: null },
    ])
    const addTermSpy = vi.spyOn(dictionaryApi, 'addTerm')

    render(<AddTermModal term="URL" onRegistered={() => {}} onClose={() => {}} />)
    const user = userEvent.setup()

    await user.click(await screen.findByText('등록'))

    expect(await screen.findByText(/모두 지정해주세요/)).toBeInTheDocument()
    expect(addTermSpy).not.toHaveBeenCalled()
  })
})
