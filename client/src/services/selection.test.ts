import { test, expect, vi, beforeEach } from 'vitest'
import {
  // SelectionCache,
  selectionsCache,
  modificationTypeSelectionCache,
  ctoSelectionCache,
  technologySelectionCache,
  getCtosByModificationIds,
  getTechnologiesByModificationIdsAndOrganismId,
  getSelectionsByIds,
  getSelectionsByTaxaId,
  getTechnologiesByIds,
  getModificationTypesByRnaName,
  type Selection
} from '@/services/selection'
import { HTTP } from '@/services/API'
import { type AxiosResponse } from 'axios'

vi.mock('@/services/API', () => ({
  HTTP: { get: vi.fn().mockResolvedValue({} as AxiosResponse) }
}))

const mockedGet = vi.mocked(HTTP.get)

beforeEach(() => {
  mockedGet.mockReset()
})

const selection: Selection[] = [
  {
    selection_id: 1,
    modification_id: 5,
    modomics_sname: 'm6A',
    rna_name: 'WTS',
    organism_id: 1,
    cto: 'HeLa',
    taxa_id: 9606,
    taxa_name: 'Homo sapiens',
    taxa_sname: 'H. sapiens',
    domain: 'Eukaryota',
    kingdom: 'Animalia',
    technology_id: 1,
    cls: 'c1',
    meth: 'm1',
    tech: 't1'
  },
  {
    selection_id: 2,
    modification_id: 6,
    modomics_sname: 'm5C',
    rna_name: 'WTS',
    organism_id: 2,
    cto: 'HEK293T',
    taxa_id: 9606,
    taxa_name: 'Homo sapiens',
    taxa_sname: 'H. sapiens',
    domain: 'Eukaryota',
    kingdom: 'Animalia',
    technology_id: 2,
    cls: 'c2',
    meth: 'm2',
    tech: 't2'
  },
  {
    selection_id: 3,
    modification_id: 5,
    modomics_sname: 'm6A',
    rna_name: 'RNA',
    organism_id: 3,
    cto: 'Heart',
    taxa_id: 10090,
    taxa_name: 'Mus musculus',
    taxa_sname: 'M. musculus',
    domain: 'Eukaryota',
    kingdom: 'Animalia',
    technology_id: 3,
    cls: 'c3',
    meth: 'm3',
    tech: 't3'
  },
  {
    selection_id: 4,
    modification_id: 7,
    modomics_sname: 'm1A',
    rna_name: 'RNA',
    organism_id: 3,
    cto: 'Heart',
    taxa_id: 10090,
    taxa_name: 'Mus musculus',
    taxa_sname: 'M. musculus',
    domain: 'Eukaryota',
    kingdom: 'Animalia',
    technology_id: 4,
    cls: 'c4',
    meth: 'm4',
    tech: 't4'
  }
]

function mockResponse(data: unknown): void {
  mockedGet.mockResolvedValueOnce({ data } as AxiosResponse)
}

// It does not matter whether a test triggers the fetch or reads the cache,
// as long as e.g. we do not assert mockedGet.toHaveBeenCalledTimes, etc.
// In such case the order may matter, unless we reset the cache or
// refactor selection.ts to inject it.

test('getPromise calls /catalogs/selections and returns the response', async () => {
  mockResponse(selection)

  const result = await selectionsCache.getPromise()

  expect(mockedGet).toHaveBeenCalledWith('/catalogs/selections')
  expect(result).toEqual(selection)
})

test('getPromise does not swallow failures', async () => {
  const error = new Error()
  mockedGet.mockRejectedValueOnce(error)

  await expect(selectionsCache.getPromise()).rejects.toBe(error)
})

test('getPromise logs and rethrows on failure', async () => {
  const error = new Error()
  const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
  mockedGet.mockRejectedValueOnce(error)

  await expect(selectionsCache.getPromise()).rejects.toBe(error)
  expect(consoleSpy).toHaveBeenCalledWith(
    expect.stringContaining('Failed to fetch /catalogs/selections:')
  )
  consoleSpy.mockRestore()
})

test('getCtosByModificationIds', async () => {
  mockResponse(selection)

  const ctos = await getCtosByModificationIds([5, 7])

  expect(ctos.map((c) => c.organism_id).sort()).toEqual([1, 3])
  expect(ctos.map((c) => c.cto).sort()).toEqual(['HeLa', 'Heart'])
})

test('getTechnologiesByModificationIdsAndOrganismId', async () => {
  mockResponse(selection)

  const techs = await getTechnologiesByModificationIdsAndOrganismId([5, 7], 1)
  expect(techs.map((t) => t.technology_id)).toEqual([1])
})

test('getSelectionsByIds', async () => {
  mockResponse(selection)

  const result = await getSelectionsByIds(5, 3, [3, 4])

  expect(result).toHaveLength(1)
  expect(result[0].selection_id).toBe(3)
})

test('getSelectionsByTaxaId', async () => {
  mockResponse(selection)

  const humanSelections = await getSelectionsByTaxaId(9606)

  expect(humanSelections.map((s) => s.selection_id).sort()).toEqual([1, 2])
})

test('getTechnologiesByIds', async () => {
  mockResponse(selection)

  const techs = await getTechnologiesByIds([1, 2])

  expect(techs.map((t) => t.technology_id).sort()).toEqual([1, 2])
})

// all other functions return empty...
test('getTechnologiesByIds throws an error', async () => {
  mockResponse(selection)

  await expect(getTechnologiesByIds([5, 6])).rejects.toThrow(/Technologies '5,6' not found/)
})

test('getModificationTypesByRnaName', async () => {
  mockResponse(selection)

  const mods = await getModificationTypesByRnaName('WTS')

  expect(mods).toHaveLength(2)
  expect(mods.map((m) => m.modification_id).sort()).toEqual([5, 6])
})
