import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { TableDesigner } from './TableDesigner'
import * as api from '../api/tableDesignerApi'

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
    expect(screen.getByLabelText('data-type-0')).toHaveValue('VARCHAR')
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
})
