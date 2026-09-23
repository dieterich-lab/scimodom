import { test, expect, vi, beforeEach } from 'vitest'
import { getFeaturesByRnaType } from '@/services/feature'
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

test('getFeaturesByRnaType calls /catalogs/rna-type/<rnaType>/features and returns the array', async () => {
  const expected = ['cds', 'exon']
  mockedHandle.mockResolvedValueOnce({ features: expected })

  const result = await getFeaturesByRnaType('RNA', dialogState)

  expect(mockedGet).toHaveBeenCalledWith('/catalogs/rna-types/RNA/features')
  expect(mockedHandle).toHaveBeenCalledWith(
    expect.anything(),
    'Failed to load FeaturesResponse: RNA)',
    dialogState
  )
  expect(result).toEqual(expected)
})

test('getFeaturesByRnaType does not swallow failures', async () => {
  const error = new Error()
  mockedHandle.mockRejectedValueOnce(error)

  await expect(getFeaturesByRnaType('RNA', dialogState)).rejects.toBe(error)
})
