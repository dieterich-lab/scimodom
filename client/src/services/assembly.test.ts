import { test, expect, vi, beforeEach } from 'vitest'
import { type Assembly, getAssembliesByTaxaId } from '@/services/assembly'
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

test('getAssembliesByTaxaId calls /catalogs/assemblies and returns the array', async () => {
  const expected: Assembly[] = [
    {
      id: 1,
      name: 'GRCh38',
      alt_name: 'hg38',
      taxa_id: 123,
      taxa_name: 'Homo sapiens',
      current: true,
      source: { provider: 'ensembl', release: 110, archive: 'jul2023' }
    }
  ]
  mockedHandle.mockResolvedValueOnce(expected)

  const result = await getAssembliesByTaxaId(123, dialogState)

  expect(mockedGet).toHaveBeenCalledWith('/catalogs/assemblies', {
    params: { taxaId: 123 }
  })
  expect(mockedHandle).toHaveBeenCalledWith(
    expect.anything(),
    'Failed to load Assembly: 123',
    dialogState
  )
  expect(result).toEqual(expected)
})

test('getAssemblieByTaxaId does not swallow failures', async () => {
  const error = new Error()
  mockedHandle.mockRejectedValueOnce(error)

  await expect(getAssembliesByTaxaId(123, dialogState)).rejects.toBe(error)
})
