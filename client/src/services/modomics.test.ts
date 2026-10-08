import { test, expect, vi, beforeEach } from 'vitest'
import { type Modomics, modomicsCache } from '@/services/modomics'
import { HTTP } from '@/services/API'
import { type AxiosResponse } from 'axios'

vi.mock('@/services/API', () => ({
  HTTP: { get: vi.fn().mockResolvedValue({} as AxiosResponse) }
}))

const mockedGet = vi.mocked(HTTP.get)

beforeEach(() => {
  mockedGet.mockReset()
})

const modomics: Modomics[] = [{ id: '123', modomics_short_name: 'short_name' }]

test('getPromise calls /catalogs/modomics and returns the response', async () => {
  mockedGet.mockResolvedValueOnce({ data: modomics } as AxiosResponse)

  const result = await modomicsCache.getPromise()

  expect(mockedGet).toHaveBeenCalledWith('/catalogs/modomics')
  expect(result).toEqual(modomics)
})

test('getPromise does not swallow failures', async () => {
  const error = new Error()
  mockedGet.mockRejectedValueOnce(error)

  await expect(modomicsCache.getPromise()).rejects.toBe(error)
})

test('getPromise propagates error on failure', async () => {
  const error = new Error()
  mockedGet.mockRejectedValueOnce(error)

  await expect(modomicsCache.getPromise()).rejects.toBe(error)
})
