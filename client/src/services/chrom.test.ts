import { test, expect, vi, beforeEach } from 'vitest'
import { type Chrom, getChromsByTaxaId } from '@/services/chrom'
import { handleRequestWithErrorReporting, HTTP } from '@/services/API'
import { type DialogStateStore } from '@/stores/DialogState'
import { type AxiosResponse } from 'axios'

vi.mock('@/services/API', () => ({
  HTTP: { get: vi.fn().mockResolvedValue({} as AxiosResponse) },
  handleRequestWithErrorReporting: vi.fn()
}))

const mockedGet = vi.mocked(HTTP.get)
const mockedHandle = vi.mocked(handleRequestWithErrorReporting)
const dialogState = {} as DialogStateStore

beforeEach(() => {
  mockedGet.mockClear()
  mockedHandle.mockReset()
})

test('getChromsByTaxaId calls /catalogs/taxa/<taxaId>/chromosomes and returns the array', async () => {
  const expected = [{ chrom: 1, size: 1 }]
  mockedHandle.mockResolvedValueOnce(expected)

  const result = await getChromsByTaxaId(123, dialogState)

  expect(mockedGet).toHaveBeenCalledWith('/catalogs/taxa/123/chromosomes')
  expect(mockedHandle).toHaveBeenCalledWith(
    expect.anything(),
    'Failed to load Chrom: 123',
    dialogState
  )
  expect(result).toEqual(expected)
})

test('getChromsByTaxaId does not swallow failures', async () => {
  const error = new Error()
  mockedHandle.mockRejectedValueOnce(error)

  await expect(getChromsByTaxaId(123, dialogState)).rejects.toBe(error)
})
