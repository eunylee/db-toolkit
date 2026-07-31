import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ScrapbookGrid } from './ScrapbookGrid'
import * as scrapbookApi from '../api/scrapbookApi'

function pasteInto(input: HTMLElement, text: string) {
  fireEvent.paste(input, {
    clipboardData: { getData: () => text },
  })
}

describe('ScrapbookGrid', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders an initial empty grid', () => {
    render(<ScrapbookGrid />)

    expect(screen.getByLabelText('cell-0-0')).toHaveValue('')
    expect(screen.getByLabelText('cell-7-4')).toBeInTheDocument()
  })

  it('lets the user type directly into a cell', async () => {
    render(<ScrapbookGrid />)
    const user = userEvent.setup()

    await user.type(screen.getByLabelText('cell-0-0'), '고객명')

    expect(screen.getByLabelText('cell-0-0')).toHaveValue('고객명')
  })

  it('adds a row and a column via toolbar buttons', async () => {
    render(<ScrapbookGrid />)
    const user = userEvent.setup()

    await user.click(screen.getByText('+ 행'))
    await user.click(screen.getByText('+ 열'))

    expect(screen.getByLabelText('cell-8-5')).toBeInTheDocument()
  })

  it('parses multi-cell pasted text via the engine API and merges it at the focused cell', async () => {
    vi.spyOn(scrapbookApi, 'parseGridText').mockResolvedValue({
      rows: [
        ['고객명', 'CUST_NM'],
        ['주문일자', 'ORD_DT'],
      ],
      row_count: 2,
      column_count: 2,
    })

    render(<ScrapbookGrid />)
    pasteInto(screen.getByLabelText('cell-1-1'), '고객명\tCUST_NM\n주문일자\tORD_DT')

    await waitFor(() => expect(screen.getByLabelText('cell-1-1')).toHaveValue('고객명'))
    expect(screen.getByLabelText('cell-1-2')).toHaveValue('CUST_NM')
    expect(screen.getByLabelText('cell-2-1')).toHaveValue('주문일자')
    expect(scrapbookApi.parseGridText).toHaveBeenCalledWith('고객명\tCUST_NM\n주문일자\tORD_DT')
  })

  it('does not call the API for a plain single-cell paste', () => {
    const spy = vi.spyOn(scrapbookApi, 'parseGridText')

    render(<ScrapbookGrid />)
    pasteInto(screen.getByLabelText('cell-0-0'), '단일값')

    expect(spy).not.toHaveBeenCalled()
  })

  it('shows an error message when the parse API call fails', async () => {
    vi.spyOn(scrapbookApi, 'parseGridText').mockRejectedValue(new Error('network error'))

    render(<ScrapbookGrid />)
    pasteInto(screen.getByLabelText('cell-0-0'), 'a\tb')

    expect(await screen.findByText(/파싱에 실패/)).toBeInTheDocument()
  })
})
