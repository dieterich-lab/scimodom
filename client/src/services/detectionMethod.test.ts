import { test, expect, vi, beforeEach } from 'vitest'
import { type DetectionMethod, detectionMethodCache } from '@/services/detectionMethod'
import { HTTP } from '@/services/API'
import { type AxiosResponse } from 'axios'

vi.mock('@/services/API', () => ({
  HTTP: { get: vi.fn().mockResolvedValue({} as AxiosResponse) }
}))

const mockedGet = vi.mocked(HTTP.get)

beforeEach(() => {
  mockedGet.mockReset()
})

const methods: DetectionMethod[] = [{ id: '123', cls: 'class', meth: 'method' }]

test('getPromise calls /catalogs/methods and returns the response', async () => {
  mockedGet.mockResolvedValueOnce({ data: methods } as AxiosResponse)

  const result = await detectionMethodCache.getPromise()

  expect(mockedGet).toHaveBeenCalledWith('/catalogs/methods')
  expect(result).toEqual(methods)
})

test('getPromise does not swallow failures', async () => {
  const error = new Error()
  mockedGet.mockRejectedValueOnce(error)

  await expect(detectionMethodCache.getPromise()).rejects.toBe(error)
})

test('getPromise logs and rethrows on failure', async () => {
  const error = new Error()
  const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
  mockedGet.mockRejectedValueOnce(error)

  await expect(detectionMethodCache.getPromise()).rejects.toBe(error)
  expect(consoleSpy).toHaveBeenCalledWith(
    expect.stringContaining('Failed to fetch /catalogs/methods:')
  )
  consoleSpy.mockRestore()
})
