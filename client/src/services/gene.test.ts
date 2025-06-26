import { test, expect, vi, beforeEach } from 'vitest'
import { getGenesForSelectionIds } from '@/services/gene'
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

test('getGenesForSelectionIds calls /catalogs/genes and returns the array', async () => {
  const expected = ['G1', 'G2']
  mockedHandle.mockResolvedValueOnce(expected)

  const result = await getGenesForSelectionIds([1, 2], dialogState)

  expect(mockedGet).toHaveBeenCalledWith(
    '/catalogs/genes',
    expect.objectContaining({ params: { selection: [1, 2] } })
  )
  expect(mockedHandle).toHaveBeenCalledWith(expect.anything(), 'Failed to load genes', dialogState)
  expect(result).toEqual(expected)
})

test('getGenesForSelectionIds does not swallow failures', async () => {
  const error = new Error()
  mockedHandle.mockRejectedValueOnce(error)

  await expect(getGenesForSelectionIds([1], dialogState)).rejects.toBe(error)
})
