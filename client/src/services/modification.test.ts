import { test, expect } from 'vitest'
import { getModificationExportLink } from '@/services/modification'
import { type SearchBy } from '@/utils/search'

test.each<{ searchBy: SearchBy; apiBaseUrl: string; expected: string }>([
  {
    searchBy: 'Gene/Chrom',
    apiBaseUrl: 'http://localhost:1234/',
    expected: 'http://localhost:1234/modification/csv/gene?rnaType=WTS&taxaId=123'
  },
  {
    searchBy: 'Modification',
    apiBaseUrl: 'http://localhost:1234/',
    expected: 'http://localhost:1234/modification/csv?rnaType=WTS&taxaId=123'
  },
  {
    searchBy: 'Modification',
    apiBaseUrl: '/',
    expected: '/modification/csv?rnaType=WTS&taxaId=123'
  }
])('getModificationExportLink(%s)', ({ searchBy, apiBaseUrl, expected }) => {
  function getApiUrlCb(endpoint: string): string {
    return `${apiBaseUrl}${endpoint}`
  }

  expect(
    getModificationExportLink(
      {
        rna_type: 'WTS',
        selections: [],
        state: 'complete',
        taxa: { taxa_id: 123, taxa_name: 'xxx', taxa_sname: 'x', domain: 'd', kingdom: 'k' },
        searchBy
      },
      [],
      getApiUrlCb
    )
  ).toBe(expected)
})
