import { test, expect, vi, beforeEach } from 'vitest'
import { type Taxa, taxaCache } from '@/services/taxa'
import { HTTP } from '@/services/API'
import { type AxiosResponse } from 'axios'

vi.mock('@/services/API', () => ({
  HTTP: { get: vi.fn().mockResolvedValue({} as AxiosResponse) }
}))

const mockedGet = vi.mocked(HTTP.get)

beforeEach(() => {
  mockedGet.mockReset()
})

const taxa: Taxa[] = [
  { domain: 'domain', kingdom: 'kingdom', taxa_id: 123, taxa_name: 'name', taxa_sname: 'sname' }
]

test('getPromise calls /catalogs/taxa and returns the response', async () => {
  mockedGet.mockResolvedValueOnce({ data: taxa } as AxiosResponse)

  const result = await taxaCache.getPromise()

  expect(mockedGet).toHaveBeenCalledWith('/catalogs/taxa')
  expect(result).toEqual(taxa)
})

test('getPromise does not swallow failures', async () => {
  const error = new Error()
  mockedGet.mockRejectedValueOnce(error)

  await expect(taxaCache.getPromise()).rejects.toBe(error)
})

test('getPromise logs and rethrows on failure', async () => {
  const error = new Error()
  const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
  mockedGet.mockRejectedValueOnce(error)

  await expect(taxaCache.getPromise()).rejects.toBe(error)
  expect(consoleSpy).toHaveBeenCalledWith(
    expect.stringContaining('Failed to fetch /catalogs/taxa:')
  )
  consoleSpy.mockRestore()
})
