import { test, expect, vi, beforeEach } from 'vitest'
import {
  getModifications,
  getModificationExportLink,
  getTargetSites,
  getGenomicContext,
  getSiteWiseInfo,
  type Modification
} from '@/services/modification'
import { getApiUrl, HTTP, handleRequestWithErrorReporting } from '@/services/API'
import { type SearchBy, type SearchParameters } from '@/utils/search'
import { type DialogStateStore } from '@/stores/DialogState'
import { type AxiosResponse } from 'axios'

// import type-checks a mock factory against the real module, per-export,
// so HTTP.get fails against the real AxiosInstance interface
// plain string avoids needing to fake unused axios methods
vi.mock('@/services/API', () => ({
  getApiUrl: (endpoint: string) => `/${endpoint}`,
  HTTP: { get: vi.fn().mockResolvedValue({} as AxiosResponse) },
  handleRequestWithErrorReporting: vi.fn()
}))

const mockedGet = vi.mocked(HTTP.get)
const mockedHandle = vi.mocked(handleRequestWithErrorReporting)
// cast empty stand-in passed through by reference for the Pinia store to avoid TS2322
const dialogState = {} as DialogStateStore

beforeEach(() => {
  // clears out call history, but keeps assigned mockResolvedValue
  mockedGet.mockClear(), mockedHandle.mockReset()
})

function makeSearchParameters(overrides: Partial<SearchParameters> = {}): SearchParameters {
  return {
    state: 'complete',
    rna_type: 'WTS',
    selections: [],
    taxa: {
      taxa_id: 123,
      taxa_name: 'name',
      taxa_sname: 'sname',
      domain: 'domain',
      kingdom: 'kingdom'
    },
    searchBy: 'Modification',
    ...overrides
  }
}

test.each<{ searchBy: SearchBy; expectedUrl: string }>([
  { searchBy: 'Modification', expectedUrl: '/modification/query' },
  { searchBy: 'Gene/Chrom', expectedUrl: '/modification/query/gene' }
])(
  'getModifications($searchBy) calls $expectedUrl and returns a response',
  async ({ searchBy, expectedUrl }) => {
    const expectedResponse = { records: [], totalRecords: 0 }
    mockedHandle.mockResolvedValueOnce(expectedResponse)

    const response = await getModifications(makeSearchParameters({ searchBy }), dialogState)
    expect(mockedGet).toHaveBeenCalledWith(
      expectedUrl,
      expect.objectContaining({ params: expect.objectContaining({ taxaId: 123, rnaType: 'WTS' }) })
    )
    expect(mockedHandle).toHaveBeenCalledWith(
      expect.anything(),
      'Failed to load features',
      dialogState
    )
    expect(response).toBe(expectedResponse)
  }
)

test('getModifications maps SearchParameters into the request', async () => {
  const searchParameters = makeSearchParameters({
    gene: 'abc',
    biotypes: ['b1', 'b2'],
    features: ['f1'],
    chrom: { chrom: '1', size: 1000 },
    chromStart: 1,
    chromEnd: 2,
    modificationType: { modification_id: 7, modomics_sname: 'm6A', rna_name: 'rRNA' },
    cto: {
      organism_id: 1,
      cto: 'cell-type',
      taxa_id: 123,
      taxa_name: 'name',
      taxa_sname: 'sname',
      domain: 'domain',
      kingdom: 'kingdom'
    },
    technologies: [
      { technology_id: 1, cls: 'c', meth: 'm', tech: 't1' },
      { technology_id: 2, cls: 'c', meth: 'm', tech: 't2' }
    ]
  })

  await getModifications(searchParameters, dialogState, 1, 10)
  expect(mockedGet.mock.calls[0][1]).toEqual({
    params: {
      modification: 7,
      organism: 1,
      technology: [1, 2],
      rnaType: 'WTS',
      taxaId: 123,
      geneName: 'abc',
      biotypes: ['b1', 'b2'],
      features: ['f1'],
      chrom: '1',
      chromStart: 1,
      chromEnd: 2,
      multiSort: [],
      firstRecord: 1,
      maxRecords: 10
    }
  })
})

test('getModifications does not swallow failures', async () => {
  const error = new Error()
  mockedHandle.mockRejectedValueOnce(error)

  await expect(getModifications(makeSearchParameters(), dialogState)).rejects.toBe(error)
})

test.each<{ searchBy: SearchBy; expected: string }>([
  { searchBy: 'Gene/Chrom', expected: '/modification/csv/gene?rnaType=WTS&taxaId=123' },
  { searchBy: 'Modification', expected: '/modification/csv?rnaType=WTS&taxaId=123' }
])('getModificationExportLink($searchBy)', ({ searchBy, expected }) => {
  expect(getModificationExportLink(makeSearchParameters({ searchBy }), [])).toBe(expected)
})

function makeModification(overrides: Partial<Modification> = {}): Modification {
  return {
    id: 15,
    chrom: '1',
    start: 1,
    end: 2,
    name: 'm6A',
    score: 0,
    strand: '+',
    coverage: 10,
    frequency: 50,
    dataset_id: 'd1',
    feature: 'exon',
    gene_id: 'ENSG1',
    gene_name: 'GENE1',
    tech: 'tech',
    taxa_id: 9606,
    cto: 'cell-type',
    ...overrides
  }
}

test("getTargetSites calls '/modification/target' and returns records", async () => {
  const expectedRecords = [{ chrom: '1', start: 1, end: 2, name: 'x', score: 0, strand: '+' }]
  mockedHandle.mockResolvedValueOnce({ records: expectedRecords })
  const modification = makeModification()

  const records = await getTargetSites(modification, 'TARGET', dialogState)
  expect(mockedGet.mock.calls[0]).toEqual([
    '/modification/target/TARGET',
    {
      params: {
        id: 15,
        chrom: '1',
        start: 1,
        end: 2,
        name: 'm6A',
        score: 0,
        strand: '+',
        coverage: 10,
        frequency: 50,
        dataset_id: 'd1',
        feature: 'exon',
        gene_id: 'ENSG1',
        gene_name: 'GENE1',
        tech: 'tech',
        taxa_id: 9606,
        cto: 'cell-type',
        taxaId: modification.taxa_id
      },
      paramsSerializer: { indexes: null }
    }
  ])
  expect(mockedHandle).toHaveBeenCalledWith(
    expect.anything(),
    "Failed to load sites for target 'TARGET' for modification 15",
    dialogState
  )
  expect(records).toBe(expectedRecords)
})

test('getTargetSites does not swallow failures', async () => {
  const error = new Error()
  mockedHandle.mockRejectedValueOnce(error)

  await expect(getTargetSites(makeModification(), '', dialogState)).rejects.toBe(error)
})

test("getGenomicContext calls '/modification/genomic-context' and returns a string", async () => {
  const expectedContext = 'ACGTACGT'
  mockedHandle.mockResolvedValueOnce({ context: expectedContext })
  const modification = makeModification()

  const context = await getGenomicContext(modification, 5, dialogState)
  expect(mockedGet.mock.calls[0]).toEqual([
    '/modification/genomic-context/5',
    {
      params: {
        id: 15,
        chrom: '1',
        start: 1,
        end: 2,
        name: 'm6A',
        score: 0,
        strand: '+',
        coverage: 10,
        frequency: 50,
        dataset_id: 'd1',
        feature: 'exon',
        gene_id: 'ENSG1',
        gene_name: 'GENE1',
        tech: 'tech',
        taxa_id: 9606,
        cto: 'cell-type',
        taxaId: modification.taxa_id
      },
      paramsSerializer: { indexes: null }
    }
  ])
  expect(mockedHandle).toHaveBeenCalledWith(
    expect.anything(),
    "Failed to get context '5' for modification 15",
    dialogState
  )
  expect(context).toBe(expectedContext)
})

test('getGenomicContext does not swallow failures', async () => {
  const error = new Error()
  mockedHandle.mockRejectedValueOnce(error)

  await expect(getGenomicContext(makeModification(), 1, dialogState)).rejects.toBe(error)
})

test("getSiteWiseInfo calls '/modification/sitewise' and returns records", async () => {
  const expectedRecords = [
    {
      chrom: '1',
      start: 1,
      end: 2,
      name: 'x',
      score: 0,
      strand: '+',
      dataset_id: 'd1',
      modification_id: 15,
      rna: 'WTS',
      short_name: 'sname',
      cto: 'cell-type',
      tech: 'tech',
      coverage: 10,
      frequency: 50
    }
  ]
  mockedHandle.mockResolvedValueOnce({ records: expectedRecords })
  const modification = makeModification()

  const records = await getSiteWiseInfo(modification, dialogState)
  expect(mockedGet.mock.calls[0]).toEqual([
    '/modification/sitewise',
    {
      params: {
        id: 15,
        chrom: '1',
        start: 1,
        end: 2,
        name: 'm6A',
        score: 0,
        strand: '+',
        coverage: 10,
        frequency: 50,
        dataset_id: 'd1',
        feature: 'exon',
        gene_id: 'ENSG1',
        gene_name: 'GENE1',
        tech: 'tech',
        taxa_id: 9606,
        cto: 'cell-type',
        taxaId: modification.taxa_id
      },
      paramsSerializer: { indexes: null }
    }
  ])
  expect(mockedHandle).toHaveBeenCalledWith(
    expect.anything(),
    'Failed to get site info for modification 15',
    dialogState
  )
  expect(records).toBe(expectedRecords)
})

test('getSiteWiseInfo does not swallow failures', async () => {
  const error = new Error()
  mockedHandle.mockRejectedValueOnce(error)

  await expect(getSiteWiseInfo(makeModification(), dialogState)).rejects.toBe(error)
})
