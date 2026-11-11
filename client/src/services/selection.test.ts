import { test, expect, vi, beforeEach } from 'vitest'
import {
  selectionsCache,
  modificationTypeSelectionCache,
  getSelectionsByIds,
  getSelectionsByTaxaId,
  getModificationTypesByRnaType,
  getCtos,
  getCtosByModificationIds,
  getTechnologiesByModificationIdsAndOrganismId,
  resolveSelections,
  getProjectSelections,
  type Selection,
  type ProjectSelection
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
    modomics_short_name: 'm6A',
    rna_type: 'WTS',
    rna_type_name: 'whole transcriptome',
    organism_id: 1,
    cto: 'HeLa',
    taxa_id: 9606,
    taxa_name: 'Homo sapiens',
    taxa_short_name: 'H. sapiens',
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
    modomics_short_name: 'm5C',
    rna_type: 'WTS',
    rna_type_name: 'whole transcriptome',
    organism_id: 2,
    cto: 'HEK293T',
    taxa_id: 9606,
    taxa_name: 'Homo sapiens',
    taxa_short_name: 'H. sapiens',
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
    modomics_short_name: 'm6A',
    rna_type: 'RNA',
    rna_type_name: 'whole transcriptome',
    organism_id: 3,
    cto: 'Heart',
    taxa_id: 10090,
    taxa_name: 'Mus musculus',
    taxa_short_name: 'M. musculus',
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
    modomics_short_name: 'm1A',
    rna_type: 'RNA',
    rna_type_name: 'whole transcriptome',
    organism_id: 3,
    cto: 'Heart',
    taxa_id: 10090,
    taxa_name: 'Mus musculus',
    taxa_short_name: 'M. musculus',
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

test('getPromise propagates error on failure', async () => {
  const error = new Error()
  mockedGet.mockRejectedValueOnce(error)

  await expect(selectionsCache.getPromise()).rejects.toBe(error)
})

test('getCtosByModificationIds (all selections)', async () => {
  mockResponse(selection)

  const ctos = getCtosByModificationIds(await resolveSelections(), [5, 7])

  expect(ctos.map((c) => c.organism_id).sort()).toEqual([1, 3])
  expect(ctos.map((c) => c.cto).sort()).toEqual(['HeLa', 'Heart'])
})

test('getTechnologiesByModificationIdsAndOrganismId (all selections)', async () => {
  mockResponse(selection)

  const techs = getTechnologiesByModificationIdsAndOrganismId(await resolveSelections(), [5, 7], 1)
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

test('getModificationTypesByRnaType (all selections)', async () => {
  mockResponse(selection)

  const mods = getModificationTypesByRnaType(await resolveSelections(), 'WTS')

  expect(mods).toHaveLength(2)
  expect(mods.map((m) => m.modification_id).sort()).toEqual([5, 6])
})

// selections of a project
const projectSelections: ProjectSelection[] = [
  { ...selection[0], selection_id: null },
  selection[3]
]

test('selection functions only use the given selections', () => {
  expect(
    getModificationTypesByRnaType(projectSelections, 'WTS').map((m) => m.modification_id)
  ).toEqual([5])
  expect(
    getModificationTypesByRnaType(projectSelections, 'RNA').map((m) => m.modification_id)
  ).toEqual([7])
  expect(getCtos(projectSelections).map((c) => c.organism_id)).toEqual([1, 3])
  expect(getCtosByModificationIds(projectSelections, [5]).map((c) => c.organism_id)).toEqual([1])
  expect(getCtosByModificationIds(projectSelections, [])).toEqual([])
  expect(
    getTechnologiesByModificationIdsAndOrganismId(projectSelections, [5], 1).map(
      (t) => t.technology_id
    )
  ).toEqual([1])
  expect(getTechnologiesByModificationIdsAndOrganismId(projectSelections, [5], 3)).toEqual([])
})

test('resolveSelections uses the given selections, even if empty', async () => {
  mockResponse(selection)

  expect(await resolveSelections(projectSelections)).toBe(projectSelections)
  expect(await resolveSelections([])).toEqual([])
  expect(mockedGet).not.toHaveBeenCalled()
  expect(await resolveSelections()).toEqual(selection)
})

test('getProjectSelections', async () => {
  mockedGet.mockResolvedValueOnce({ data: projectSelections } as AxiosResponse)

  const data = await getProjectSelections('12345678')

  expect(mockedGet).toHaveBeenCalledWith('/projects/12345678/selections')
  expect(data).toEqual(projectSelections)
  expect(data[0].selection_id).toBeNull()
})
