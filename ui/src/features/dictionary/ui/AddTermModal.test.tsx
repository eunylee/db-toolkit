import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AddTermModal } from './AddTermModal'
import * as dictionaryApi from '../api/dictionaryApi'
import * as domainsApi from '../../domains/api/domainsApi'
import type { Domain } from '../../domains/model/types'

const DOMAIN: Domain = {
  name: '명V100',
  data_type: 'VARCHAR',
  length: 100,
  precision: null,
  scale: null,
  source: 'standard',
  usage_count: 10,
}

async function markAsDomainWord(index: number) {
  const user = userEvent.setup()
  await user.click(screen.getByLabelText(`is-domain-word-${index}`))
  return user
}

describe('AddTermModal', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('splits the unmatched blob into word candidates and shows existing ones as already registered', async () => {
    vi.spyOn(dictionaryApi, 'getSplitCandidates').mockResolvedValue([
      {
        term: '외부',
        exists: true,
        is_domain_word: false,
        abbreviation: 'EXT',
        data_type: 'VARCHAR',
        length: 50,
        precision: null,
        scale: null,
      },
      { term: 'URL', exists: false, is_domain_word: false, abbreviation: null, data_type: null, length: null, precision: null, scale: null },
    ])

    render(<AddTermModal term="외부URL" onRegistered={() => {}} onClose={() => {}} />)

    expect(await screen.findByText(/외부: 이미 있음/)).toBeInTheDocument()
    expect(screen.getByText('URL')).toBeInTheDocument()
    expect(screen.getByLabelText('new-term-abbreviation-1')).toBeInTheDocument()
  })

  it('registers a non-domain word with just an abbreviation, no domain required', async () => {
    vi.spyOn(dictionaryApi, 'getSplitCandidates').mockResolvedValue([
      { term: 'URL', exists: false, is_domain_word: false, abbreviation: null, data_type: null, length: null, precision: null, scale: null },
    ])
    const addTermSpy = vi.spyOn(dictionaryApi, 'addTerm').mockResolvedValue({
      term: 'URL',
      abbreviation: 'URL',
      is_domain_word: false,
      data_type: 'UNKNOWN',
      length: null,
      precision: null,
      scale: null,
    })

    render(<AddTermModal term="URL" onRegistered={() => {}} onClose={() => {}} />)
    const user = userEvent.setup()

    await user.type(await screen.findByLabelText('new-term-abbreviation-0'), 'URL')
    await user.click(screen.getByText('등록'))

    await waitFor(() =>
      expect(addTermSpy).toHaveBeenCalledWith({
        term: 'URL',
        abbreviation: 'URL',
        is_domain_word: false,
        data_type: 'UNKNOWN',
        length: null,
        precision: null,
        scale: null,
      }),
    )
  })

  it('requires a domain when the domain-word checkbox is checked', async () => {
    vi.spyOn(dictionaryApi, 'getSplitCandidates').mockResolvedValue([
      { term: '외부', exists: true, is_domain_word: false, abbreviation: 'EXT', data_type: 'VARCHAR', length: 50, precision: null, scale: null },
      { term: 'URL', exists: false, is_domain_word: false, abbreviation: null, data_type: null, length: null, precision: null, scale: null },
    ])
    vi.spyOn(domainsApi, 'listDomains').mockResolvedValue([DOMAIN])
    const addTermSpy = vi.spyOn(dictionaryApi, 'addTerm').mockResolvedValue({
      term: 'URL',
      abbreviation: 'URL',
      is_domain_word: true,
      data_type: 'VARCHAR',
      length: 100,
      precision: null,
      scale: null,
    })

    render(<AddTermModal term="외부URL" onRegistered={() => {}} onClose={() => {}} />)
    const user = userEvent.setup()

    await screen.findByLabelText('new-term-abbreviation-1')
    await user.type(screen.getByLabelText('new-term-abbreviation-1'), 'URL')
    await user.click(screen.getByLabelText('is-domain-word-1'))
    await user.click(screen.getByText('도메인 선택'))
    await screen.findByRole('dialog', { name: '도메인 선택' })
    await user.click(screen.getByText('선택'))
    await user.click(screen.getByText('등록'))

    await waitFor(() =>
      expect(addTermSpy).toHaveBeenCalledWith({
        term: 'URL',
        abbreviation: 'URL',
        is_domain_word: true,
        data_type: 'VARCHAR',
        length: 100,
        precision: null,
        scale: null,
      }),
    )
    // '외부'는 이미 존재하던 단어라 addTerm이 그 값으로 다시 호출되지 않아야 한다
    expect(addTermSpy).toHaveBeenCalledTimes(1)
    // 방금 선택한 도메인이 등록 직후 표시에도 반영되어야 한다(등록 전 후보 데이터의 stale UNKNOWN이 아니라)
    expect(await screen.findByText(/URL: 등록됨 — URL \(VARCHAR\(100\)\)/)).toBeInTheDocument()
  })

  it('shows 완료 button only once every candidate is resolved', async () => {
    vi.spyOn(dictionaryApi, 'getSplitCandidates').mockResolvedValue([
      { term: '외부', exists: true, is_domain_word: false, abbreviation: 'EXT', data_type: 'VARCHAR', length: 50, precision: null, scale: null },
      { term: 'URL', exists: false, is_domain_word: false, abbreviation: null, data_type: null, length: null, precision: null, scale: null },
    ])
    vi.spyOn(dictionaryApi, 'addTerm').mockResolvedValue({
      term: 'URL',
      abbreviation: 'URL',
      is_domain_word: false,
      data_type: 'UNKNOWN',
      length: null,
      precision: null,
      scale: null,
    })
    const onRegistered = vi.fn()

    render(<AddTermModal term="외부URL" onRegistered={onRegistered} onClose={() => {}} />)
    const user = userEvent.setup()

    await screen.findByLabelText('new-term-abbreviation-1')
    expect(screen.queryByText('완료')).not.toBeInTheDocument()

    await user.type(screen.getByLabelText('new-term-abbreviation-1'), 'URL')
    await user.click(screen.getByText('등록'))

    await screen.findByText('완료')
    await user.click(screen.getByText('완료'))

    expect(onRegistered).toHaveBeenCalled()
  })

  it('shows a per-row error message when registration fails', async () => {
    vi.spyOn(dictionaryApi, 'getSplitCandidates').mockResolvedValue([
      { term: 'URL', exists: false, is_domain_word: false, abbreviation: null, data_type: null, length: null, precision: null, scale: null },
    ])
    vi.spyOn(dictionaryApi, 'addTerm').mockRejectedValue(new Error('boom'))

    render(<AddTermModal term="URL" onRegistered={() => {}} onClose={() => {}} />)
    const user = userEvent.setup()

    await user.type(await screen.findByLabelText('new-term-abbreviation-0'), 'URL')
    await user.click(screen.getByText('등록'))

    expect(await screen.findByText(/등록에 실패/)).toBeInTheDocument()
  })

  it('requires an abbreviation before allowing registration', async () => {
    vi.spyOn(dictionaryApi, 'getSplitCandidates').mockResolvedValue([
      { term: 'URL', exists: false, is_domain_word: false, abbreviation: null, data_type: null, length: null, precision: null, scale: null },
    ])
    const addTermSpy = vi.spyOn(dictionaryApi, 'addTerm')

    render(<AddTermModal term="URL" onRegistered={() => {}} onClose={() => {}} />)
    const user = userEvent.setup()

    await user.click(await screen.findByText('등록'))

    expect(await screen.findByText(/물리명\(약어\)을 입력해주세요/)).toBeInTheDocument()
    expect(addTermSpy).not.toHaveBeenCalled()
  })

  it('requires a domain once marked as a domain word, even with an abbreviation filled in', async () => {
    vi.spyOn(dictionaryApi, 'getSplitCandidates').mockResolvedValue([
      { term: 'URL', exists: false, is_domain_word: false, abbreviation: null, data_type: null, length: null, precision: null, scale: null },
    ])
    const addTermSpy = vi.spyOn(dictionaryApi, 'addTerm')

    render(<AddTermModal term="URL" onRegistered={() => {}} onClose={() => {}} />)
    const user = userEvent.setup()

    await user.type(await screen.findByLabelText('new-term-abbreviation-0'), 'URL')
    await user.click(screen.getByLabelText('is-domain-word-0'))
    await user.click(screen.getByText('등록'))

    expect(await screen.findByText(/도메인 단어는 도메인을 지정해주세요/)).toBeInTheDocument()
    expect(addTermSpy).not.toHaveBeenCalled()
  })

  it('lets the user manually re-split a pure-Hangul blob that the tokenizer could not split', async () => {
    // "외부참조키"는 문자종류 경계가 없어 자동분리로는 한 덩어리로만 나온다
    vi.spyOn(dictionaryApi, 'getSplitCandidates').mockResolvedValue([
      {
        term: '외부참조키',
        exists: false,
        is_domain_word: false,
        abbreviation: null,
        data_type: null,
        length: null,
        precision: null,
        scale: null,
      },
    ])
    const checkSpy = vi
      .spyOn(dictionaryApi, 'checkTermExists')
      .mockImplementation(async (term: string) =>
        term === '참조'
          ? {
              term,
              exists: true,
              is_domain_word: false,
              abbreviation: 'REF',
              data_type: 'VARCHAR',
              length: 20,
              precision: null,
              scale: null,
            }
          : { term, exists: false, is_domain_word: false, abbreviation: null, data_type: null, length: null, precision: null, scale: null },
      )

    render(<AddTermModal term="외부참조키" onRegistered={() => {}} onClose={() => {}} />)
    const user = userEvent.setup()

    const input = await screen.findByLabelText('manual-split-input')
    expect(input).toHaveValue('외부참조키')

    await user.clear(input)
    await user.type(input, '외부 참조 키')
    await user.click(screen.getByText('다시 나누기'))

    await waitFor(() => expect(checkSpy).toHaveBeenCalledWith('외부'))
    expect(checkSpy).toHaveBeenCalledWith('참조')
    expect(checkSpy).toHaveBeenCalledWith('키')
    expect(await screen.findByText(/참조: 이미 있음/)).toBeInTheDocument()
    expect(screen.getByLabelText('new-term-abbreviation-0')).toBeInTheDocument()
    expect(screen.getByLabelText('new-term-abbreviation-2')).toBeInTheDocument()
  })

  it('shows abbreviation suggestion chips and fills the field on click', async () => {
    vi.spyOn(dictionaryApi, 'getSplitCandidates').mockResolvedValue([
      { term: '참조', exists: false, is_domain_word: false, abbreviation: null, data_type: null, length: null, precision: null, scale: null },
    ])
    vi.spyOn(dictionaryApi, 'getAbbreviationSuggestions').mockResolvedValue([
      { token: 'RFRNC', count: 8 },
      { token: 'REF', count: 1 },
    ])

    render(<AddTermModal term="참조" onRegistered={() => {}} onClose={() => {}} />)
    const user = userEvent.setup()

    await screen.findByLabelText('new-term-abbreviation-0')
    const chip = await screen.findByText('RFRNC (8)')
    await user.click(chip)

    expect(screen.getByLabelText('new-term-abbreviation-0')).toHaveValue('RFRNC')
  })

  it('does not show a suggestion section when there are no suggestions', async () => {
    vi.spyOn(dictionaryApi, 'getSplitCandidates').mockResolvedValue([
      { term: '완전히새단어', exists: false, is_domain_word: false, abbreviation: null, data_type: null, length: null, precision: null, scale: null },
    ])
    vi.spyOn(dictionaryApi, 'getAbbreviationSuggestions').mockResolvedValue([])

    render(<AddTermModal term="완전히새단어" onRegistered={() => {}} onClose={() => {}} />)

    await screen.findByLabelText('new-term-abbreviation-0')
    expect(screen.queryByText(/추천:/)).not.toBeInTheDocument()
  })

  it('does not show domain selection UI until marked as a domain word', async () => {
    vi.spyOn(dictionaryApi, 'getSplitCandidates').mockResolvedValue([
      { term: 'URL', exists: false, is_domain_word: false, abbreviation: null, data_type: null, length: null, precision: null, scale: null },
    ])

    render(<AddTermModal term="URL" onRegistered={() => {}} onClose={() => {}} />)
    await screen.findByLabelText('new-term-abbreviation-0')

    expect(screen.queryByText('도메인 선택')).not.toBeInTheDocument()

    await markAsDomainWord(0)

    expect(screen.getByText('도메인 선택')).toBeInTheDocument()
  })
})
