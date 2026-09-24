import { test, expect, vi, beforeEach } from 'vitest'
import {
  allDatasetsCache,
  allDatasetsByIdCache,
  myDatasetsCache,
  getDatasetsByTaxaId,
  type Dataset
} from '@/services/dataset'
import { HTTP, HTTPSecure } from '@/services/API'
import { type AxiosResponse } from 'axios'

vi.mock('@/services/API', () => ({
  HTTP: { get: vi.fn().mockResolvedValue({} as AxiosResponse) },
  HTTPSecure: { get: vi.fn().mockResolvedValue({} as AxiosResponse) }
}))

const mockedGet = vi.mocked(HTTP.get)
const mockedSecureGet = vi.mocked(HTTPSecure.get)

beforeEach(() => {
  mockedGet.mockReset()
  mockedSecureGet.mockReset()
})

const dataset: Dataset[] = [
  {
    project_id: 'p1',
    dataset_id: 'd1',
    dataset_title: 'Dataset 1',
    sequencing_platform: null,
    basecalling: null,
    bioinformatics_workflow: null,
    experiment: null,
    project_title: 'Project 1',
    project_summary: 'Summary 1',
    doi: '10.1234/x',
    pmid: 12345,
    rna: 'WTS',
    modomics_sname: 'm6A',
    tech: 'GLORI',
    taxa_sname: 'H. sapiens',
    taxa_id: 9606,
    cto: 'HeLa'
  },
  {
    project_id: 'p1',
    dataset_id: 'd2',
    dataset_title: 'Dataset 2',
    sequencing_platform: 'Illumina',
    basecalling: 'guppy',
    bioinformatics_workflow: 'nf-core',
    experiment: 'exp',
    project_title: 'Project 1',
    project_summary: 'Summary 1',
    rna: 'WTS',
    modomics_sname: 'm6A',
    tech: 'xPore',
    taxa_sname: 'H. sapiens',
    taxa_id: 9606,
    cto: 'HEK293T'
  },
  {
    project_id: 'p2',
    dataset_id: 'd3',
    dataset_title: 'Dataset 3',
    sequencing_platform: null,
    basecalling: null,
    bioinformatics_workflow: null,
    experiment: null,
    project_title: 'Project 2',
    project_summary: 'Summary 2',
    rna: 'RNA',
    modomics_sname: 'm5C',
    tech: 'UBS-seq',
    taxa_sname: 'M. musculus',
    taxa_id: 10090,
    cto: 'mESC'
  }
]

function mockGet(data: unknown): void {
  mockedGet.mockResolvedValueOnce({ data } as AxiosResponse)
}

function mockSecureGet(data: unknown): void {
  mockedSecureGet.mockResolvedValueOnce({ data } as AxiosResponse)
}

// Tests the exported instances, not their classes, cf. e.g. selection.test.ts
// The first test fetches, the others use the cache

test('allDatasetsCache fetches /datasets', async () => {
  mockGet(dataset)

  const result = await allDatasetsCache.getData()

  expect(mockedGet).toHaveBeenCalledWith('/datasets')
  expect(result).toEqual(dataset)
})

test('myDatasetsCache fetches /users/me/datasets', async () => {
  mockSecureGet(dataset)

  const result = await myDatasetsCache.getData()

  expect(mockedSecureGet).toHaveBeenCalledWith('/users/me/datasets')
  expect(mockedGet).not.toHaveBeenCalled()
  expect(result).toEqual(dataset)
})

test('allDatasetsByIdCache', async () => {
  mockGet(dataset)

  const map = await allDatasetsByIdCache.getData(true)

  expect([...map.keys()].sort()).toEqual(['d1', 'd2', 'd3'])
})

// this returns an empty array when no match
test('getDatasetsByTaxaId', async () => {
  mockGet(dataset)

  const human = await getDatasetsByTaxaId(9606)

  expect(human.map((d) => d.dataset_id).sort()).toEqual(['d1', 'd2'])
})
