import { test, expect, vi, beforeEach } from 'vitest'
import { subtract, intersect, closest, type ComparisonParams } from '@/services/comparison'
import { handleRequestWithErrorReporting, HTTP } from '@/services/API'
import { type DialogStateStore } from '@/stores/DialogState'

vi.mock('@/services/API', () => ({
  HTTP: { get: vi.fn().mockResolvedValue({}) },
  handleRequestWithErrorReporting: vi.fn()
}))

const mockedGet = vi.mocked(HTTP.get)
const mockedHandle = vi.mocked(handleRequestWithErrorReporting)
const dialogState = {} as DialogStateStore

beforeEach(() => {
  mockedGet.mockClear()
  mockedHandle.mockReset()
})

function makeParams(overrides: Partial<ComparisonParams> = {}): ComparisonParams {
  return {
    reference: ['d1'],
    comparison: ['d2', 'd3'],
    strand: true,
    ...overrides
  }
}

const subtractRecords = [
  { chrom: '1', start: 1, end: 2, name: 'x', score: 0, strand: '+', eufid: 'd1' }
]
const intersectRecords = [
  {
    a: { chrom: '1', start: 1, end: 2, name: 'x', score: 0, strand: '+', eufid: 'd1' },
    b: { chrom: '1', start: 3, end: 4, name: 'y', score: 0, strand: '+', eufid: 'd2' }
  }
]
const closestRecords = [
  {
    a: { chrom: '1', start: 1, end: 2, name: 'x', score: 0, strand: '+', eufid: 'd1' },
    b: { chrom: '1', start: 5, end: 6, name: 'y', score: 0, strand: '+', eufid: 'd2' },
    distance: 3
  }
]

test.each([
  { fn: subtract, operation: 'subtract', records: subtractRecords },
  { fn: intersect, operation: 'intersect', records: intersectRecords },
  { fn: closest, operation: 'closest', records: closestRecords }
])(
  '$operation calls /datasets/comparisons/$operation and unwraps records',
  async ({ fn, operation, records }) => {
    mockedHandle.mockResolvedValueOnce({ records })

    const result = await fn(makeParams(), dialogState)

    expect(mockedGet).toHaveBeenCalledWith(`/datasets/comparisons/${operation}`, {
      params: expect.objectContaining({ reference: ['d1'], strand: true })
    })
    expect(mockedHandle).toHaveBeenCalledWith(
      expect.anything(),
      `Comparison failed: ${operation}`,
      dialogState
    )
    expect(result).toBe(records)
  }
)

test('comparison forwards all supplied parameters', async () => {
  mockedHandle.mockResolvedValueOnce({ records: [] })
  const params: ComparisonParams = {
    reference: ['d1'],
    comparison: ['d2'],
    upload: 'file-abc',
    uploadName: 'my.bed',
    strand: false,
    euf: true,
    taxaId: 9606
  }

  await intersect(params, dialogState)

  expect(mockedGet).toHaveBeenCalledWith(
    '/datasets/comparisons/intersect',
    expect.objectContaining({
      params: {
        reference: ['d1'],
        comparison: ['d2'],
        upload: 'file-abc',
        uploadName: 'my.bed',
        strand: false,
        euf: true,
        taxaId: 9606
      }
    })
  )
})

test('comparison does not swallow failures', async () => {
  const error = new Error()
  mockedHandle.mockRejectedValueOnce(error)

  await expect(intersect(makeParams(), dialogState)).rejects.toBe(error)
})
