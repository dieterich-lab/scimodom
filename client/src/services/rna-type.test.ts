import { test, expect, vi, beforeEach } from 'vitest'
import { rnaTypeCache, type RnaType } from '@/services/rna-type'
import { HTTP } from '@/services/API'
import { type AxiosResponse } from 'axios'

vi.mock('@/services/API', () => ({
  HTTP: { get: vi.fn().mockResolvedValue({} as AxiosResponse) }
}))

const mockedGet = vi.mocked(HTTP.get)

beforeEach(() => {
  mockedGet.mockReset()
})

const rna: RnaType[] = [{ id: 'WTS', name: 'Wild type' }]

test('getPromise calls /catalogs/rna-types and returns the response', async () => {
  mockedGet.mockResolvedValueOnce({ data: rna } as AxiosResponse)

  const result = await rnaTypeCache.getPromise()

  expect(mockedGet).toHaveBeenCalledWith('/catalogs/rna-types')
  expect(result).toEqual(rna)
})

test('getPromise does not swallow failures', async () => {
  const error = new Error()
  mockedGet.mockRejectedValueOnce(error)

  await expect(rnaTypeCache.getPromise()).rejects.toBe(error)
})

test('getPromise propagates error on failure', async () => {
  const error = new Error()
  mockedGet.mockRejectedValueOnce(error)

  await expect(rnaTypeCache.getPromise()).rejects.toBe(error)
})
