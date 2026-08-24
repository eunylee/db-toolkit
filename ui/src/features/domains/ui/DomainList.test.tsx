import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { DomainList } from './DomainList'
import type { Domain } from '../model/types'

const STANDARD: Domain = {
  name: '명V100',
  data_type: 'VARCHAR',
  length: 100,
  precision: null,
  scale: null,
  source: 'standard',
  usage_count: 1117,
}

const CUSTOM: Domain = {
  name: '이메일주소',
  data_type: 'VARCHAR',
  length: 255,
  precision: null,
  scale: null,
  source: 'custom',
  usage_count: 0,
}

describe('DomainList', () => {
  it('renders domain rows with formatted type', () => {
    render(<DomainList domains={[STANDARD]} />)

    expect(screen.getByText('명V100')).toBeInTheDocument()
    expect(screen.getByText('VARCHAR(100)')).toBeInTheDocument()
    expect(screen.getByText('표준')).toBeInTheDocument()
  })

  it('only shows edit/delete for custom domains', () => {
    render(<DomainList domains={[STANDARD, CUSTOM]} onEdit={() => {}} onDelete={() => {}} />)

    expect(screen.getAllByText('수정')).toHaveLength(1)
    expect(screen.getAllByText('삭제')).toHaveLength(1)
  })

  it('calls onSelect when clicked', async () => {
    const onSelect = vi.fn()
    render(<DomainList domains={[STANDARD]} onSelect={onSelect} />)
    const user = userEvent.setup()

    await user.click(screen.getByText('선택'))

    expect(onSelect).toHaveBeenCalledWith(STANDARD)
  })
})
