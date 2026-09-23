import { test, expect, vi, beforeEach } from 'vitest'
import { getBioTypes } from '@/services/biotype'
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

test('getBioTypes calls /catalogs/rna-type/<rnaType>/biotypes and returns the array', async () => {
  const expected = ['protein_coding', 'lncRNA']
  mockedHandle.mockResolvedValueOnce({ biotypes: expected })

  const result = await getBioTypes('RNA', dialogState)

  expect(mockedGet).toHaveBeenCalledWith('/catalogs/rna-types/RNA/biotypes')
  expect(mockedHandle).toHaveBeenCalledWith(
    expect.anything(),
    'Failed to load BiotypesResponse: RNA)',
    dialogState
  )
  expect(result).toEqual(expected)
})

test('getBioTypes does not swallow failures', async () => {
  const error = new Error()
  mockedHandle.mockRejectedValueOnce(error)

  await expect(getBioTypes('RNA', dialogState)).rejects.toBe(error)
})
