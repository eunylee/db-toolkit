import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { TableDesigner } from './TableDesigner'
import * as api from '../api/tableDesignerApi'
import * as domainsApi from '../../domains/api/domainsApi'
import * as dictionaryApi from '../../dictionary/api/dictionaryApi'

describe('TableDesigner', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders one empty column row initially', () => {
    render(<TableDesigner />)

    expect(screen.getByLabelText('logical-name-0')).toHaveValue('')
  })

  it('adds a new column row', async () => {
    render(<TableDesigner />)
    const user = userEvent.setup()

    await user.click(screen.getByText('+ 컬럼'))

    expect(screen.getByLabelText('logical-name-1')).toBeInTheDocument()
  })

  it('fills physical name and data type when suggestion is fully matched', async () => {
    vi.spyOn(api, 'suggestColumns').mockResolvedValue([
      {
        logical_name: '고객명',
        physical_name_suggestion: 'CUST_NM',
        fully_matched: true,
        segments: [{ text: '고객명', matched: true, term: null }],
        data_type: 'VARCHAR',
        length: 100,
        precision: null,
        scale: null,
      },
    ])

    render(<TableDesigner />)
    const user = userEvent.setup()
    await user.type(screen.getByLabelText('logical-name-0'), '고객명')
    await user.click(screen.getByText('물리명 제안 적용'))

    await waitFor(() => expect(screen.getByLabelText('physical-name-0')).toHaveValue('CUST_NM'))
    expect(screen.getByText('VARCHAR(100)')).toBeInTheDocument()
  })

  it('shows unmatched segments as a warning without inventing a physical name', async () => {
    vi.spyOn(api, 'suggestColumns').mockResolvedValue([
      {
        logical_name: 'VIP고객명',
        physical_name_suggestion: null,
        fully_matched: false,
        segments: [
          { text: 'VIP', matched: false, term: null },
          { text: '고객명', matched: true, term: null },
        ],
        data_type: 'VARCHAR',
        length: 100,
        precision: null,
        scale: null,
      },
    ])

    render(<TableDesigner />)
    const user = userEvent.setup()
    await user.type(screen.getByLabelText('logical-name-0'), 'VIP고객명')
    await user.click(screen.getByText('물리명 제안 적용'))

    expect(await screen.findByText(/미등록: VIP/)).toBeInTheDocument()
    expect(screen.getByLabelText('physical-name-0')).toHaveValue('')
  })

  it('saves the table with the current draft payload', async () => {
    const saveSpy = vi
      .spyOn(api, 'saveTable')
      .mockResolvedValue({ logical_name: '고객', physical_name: 'CUSTOMER', columns: [] })

    render(<TableDesigner />)
    const user = userEvent.setup()

    await user.type(screen.getByPlaceholderText('테이블 논리명 (예: 고객)'), '고객')
    await user.type(screen.getByPlaceholderText('테이블 물리명 (예: CUSTOMER)'), 'CUSTOMER')
    await user.type(screen.getByLabelText('logical-name-0'), '고객번호')
    await user.type(screen.getByLabelText('physical-name-0'), 'CUST_NO')
    await user.click(screen.getByLabelText('is-pk-0'))
    await user.click(screen.getByText('테이블로 저장'))

    await waitFor(() => expect(saveSpy).toHaveBeenCalled())
    const payload = saveSpy.mock.calls[0][0]
    expect(payload.logical_name).toBe('고객')
    expect(payload.columns[0]).toMatchObject({ logical_name: '고객번호', physical_name: 'CUST_NO', is_pk: true })
    expect(await screen.findByText(/저장됨/)).toBeInTheDocument()
  })

  it('shows an error message when save fails', async () => {
    vi.spyOn(api, 'saveTable').mockRejectedValue(new Error('boom'))

    render(<TableDesigner />)
    const user = userEvent.setup()
    await user.click(screen.getByText('테이블로 저장'))

    expect(await screen.findByText(/저장에 실패/)).toBeInTheDocument()
  })

  it('opens the domain picker and applies the selected domain to the column', async () => {
    vi.spyOn(domainsApi, 'listDomains').mockResolvedValue([
      {
        id: 1,
        name: '명V100',
        data_type: 'VARCHAR',
        length: 100,
        precision: null,
        scale: null,
        source: 'standard',
        usage_count: 10,
      },
    ])

    render(<TableDesigner />)
    const user = userEvent.setup()

    await user.click(screen.getByText('도메인 지정'))
    await screen.findByRole('dialog', { name: '도메인 선택' })
    await user.click(screen.getByText('선택'))

    expect(screen.getByText('VARCHAR(100)')).toBeInTheDocument()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('registers an unmatched segment via the add-term modal and refreshes the suggestion', async () => {
    vi.spyOn(api, 'suggestColumns')
      .mockResolvedValueOnce([
        {
          logical_name: 'VIP고객명',
          physical_name_suggestion: null,
          fully_matched: false,
          segments: [
            { text: 'VIP', matched: false, term: null },
            { text: '고객명', matched: true, term: null },
          ],
          data_type: 'VARCHAR',
          length: 100,
          precision: null,
          scale: null,
        },
      ])
      .mockResolvedValueOnce([
        {
          logical_name: 'VIP고객명',
          physical_name_suggestion: 'VIP_CUST_NM',
          fully_matched: true,
          segments: [
            { text: 'VIP', matched: true, term: null },
            { text: '고객명', matched: true, term: null },
          ],
          data_type: 'VARCHAR',
          length: 100,
          precision: null,
          scale: null,
        },
      ])
    vi.spyOn(domainsApi, 'listDomains').mockResolvedValue([
      {
        id: 1,
        name: '명V100',
        data_type: 'VARCHAR',
        length: 100,
        precision: null,
        scale: null,
        source: 'standard',
        usage_count: 10,
      },
    ])
    const addTermSpy = vi.spyOn(dictionaryApi, 'addTerm').mockResolvedValue({
      term: 'VIP',
      abbreviation: 'VIP',
      data_type: 'VARCHAR',
      length: 100,
      precision: null,
      scale: null,
    })

    render(<TableDesigner />)
    const user = userEvent.setup()
    await user.type(screen.getByLabelText('logical-name-0'), 'VIP고객명')
    await user.click(screen.getByText('물리명 제안 적용'))
    await screen.findByText(/미등록: VIP/)

    await user.click(screen.getByText('사전에 추가'))
    await screen.findByRole('dialog', { name: '사전에 추가' })
    await user.type(screen.getByLabelText('new-term-abbreviation'), 'VIP')
    await user.click(screen.getByText('도메인 선택'))
    await screen.findByRole('dialog', { name: '도메인 선택' })
    await user.click(screen.getByText('선택'))
    await user.click(screen.getByText('등록'))

    await waitFor(() => expect(addTermSpy).toHaveBeenCalled())
    await waitFor(() => expect(screen.getByLabelText('physical-name-0')).toHaveValue('VIP_CUST_NM'))
    expect(screen.queryByText(/미등록: VIP/)).not.toBeInTheDocument()
  })
})
