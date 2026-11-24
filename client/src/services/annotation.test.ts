import { test, expect, vi, beforeEach } from 'vitest'
import { type Annotation, annotationCache, getEnsemblBrowseUrl } from '@/services/annotation'
import { HTTP, RequestError, trashRequestErrors } from '@/services/API'
import { type AxiosResponse } from 'axios'

vi.mock('@/services/API', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/services/API')>()),
  HTTP: { get: vi.fn() }
}))

const mockedGet = vi.mocked(HTTP.get)

const HUMAN: Annotation = {
  id: 1,
  source: 'ensembl',
  release: 110,
  archive: 'jul2023',
  browse_url: 'https://jul2023.archive.ensembl.org/Homo_sapiens',
  assembly_id: 1,
  assembly_name: 'GRCh38',
  taxa_id: 9606,
  taxa_name: 'Homo sapiens'
}

const HUMAN_TRNA: Annotation = {
  ...HUMAN,
  id: 2,
  source: 'gtrnadb',
  release: 19,
  archive: null,
  browse_url: null
}

const MOUSE: Annotation = {
  ...HUMAN,
  id: 3,
  browse_url: 'https://jul2023.archive.ensembl.org/Mus_musculus',
  assembly_id: 2,
  assembly_name: 'GRCm39',
  taxa_id: 10090,
  taxa_name: 'Mus musculus'
}

beforeEach(() => {
  mockedGet.mockReset()
  mockedGet.mockResolvedValue({ status: 200, data: [HUMAN, HUMAN_TRNA, MOUSE] } as AxiosResponse)
  // the cache lives for the lifetime of the module
  annotationCache.getData(true)
})

test('annotationCache calls /catalogs/annotations', async () => {
  const data = await annotationCache.getData(true)
  expect(mockedGet).toHaveBeenCalledWith('/catalogs/annotations')
  expect(data).toEqual([HUMAN, HUMAN_TRNA, MOUSE])
})

test('annotationCache fetches once and is then served from memory', async () => {
  await annotationCache.getData(true)
  mockedGet.mockClear()
  await annotationCache.getData()
  await annotationCache.getData()
  expect(mockedGet).not.toHaveBeenCalled()
})

test('getEnsemblBrowseUrl returns the url the server built', async () => {
  // no archive and no release is spelled out in the client
  expect(await getEnsemblBrowseUrl(9606)).toBe('https://jul2023.archive.ensembl.org/Homo_sapiens')
  expect(await getEnsemblBrowseUrl(10090)).toBe('https://jul2023.archive.ensembl.org/Mus_musculus')
})

test('getEnsemblBrowseUrl ignores another source of the same organism', async () => {
  // the cache holds every source; the Ensembl row is the one that
  // answers for an Ensembl page
  mockedGet.mockResolvedValue({ status: 200, data: [HUMAN_TRNA] } as AxiosResponse)
  await annotationCache.getData(true)
  expect(await getEnsemblBrowseUrl(9606)).toBeNull()
})

test('getEnsemblBrowseUrl returns null for an organism without an annotation', async () => {
  expect(await getEnsemblBrowseUrl(7227)).toBeNull()
})

test('getEnsemblBrowseUrl follows the installed release', async () => {
  // an annotation upgrade moves the archive: nothing in the client
  // has to change with it
  mockedGet.mockResolvedValue({
    status: 200,
    data: [
      {
        ...HUMAN,
        release: 112,
        archive: 'may2024',
        browse_url: 'https://may2024.archive.ensembl.org/Homo_sapiens'
      }
    ]
  } as AxiosResponse)
  await annotationCache.getData(true)
  expect(await getEnsemblBrowseUrl(9606)).toBe('https://may2024.archive.ensembl.org/Homo_sapiens')
})

test('a failure is a RequestError, which trashRequestErrors swallows', async () => {
  // consumers that can do without the annotations catch with
  // trashRequestErrors, which only recognises RequestError
  mockedGet.mockRejectedValue(new Error('Network Error'))
  await expect(annotationCache.getData(true)).rejects.toBeInstanceOf(RequestError)
  await expect(
    annotationCache.getData(true).catch((e) => trashRequestErrors(e))
  ).resolves.toBeUndefined()
})
