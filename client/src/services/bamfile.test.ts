import { test, expect, vi, beforeEach } from 'vitest'
import {
  getBamFilesByDatasetId,
  deleteBamFile,
  getBamFileDownLoadURL,
  type BamFile
} from '@/services/bamfile'
import { getApiUrl, handleRequestWithErrorReporting, HTTP, HTTPSecure } from '@/services/API'
import { type DialogStateStore } from '@/stores/DialogState'
import { type AxiosResponse } from 'axios'

vi.mock('@/services/API', () => ({
  getApiUrl: vi.fn((uri: string) => `/${uri}`),
  HTTP: { get: vi.fn().mockResolvedValue({} as AxiosResponse) },
  HTTPSecure: { delete: vi.fn().mockResolvedValue({} as AxiosResponse) },
  handleRequestWithErrorReporting: vi.fn()
}))

const mockedGet = vi.mocked(HTTP.get)
const mockedDelete = vi.mocked(HTTPSecure.delete)
const mockedHandle = vi.mocked(handleRequestWithErrorReporting)
const mockedGetApiUrl = vi.mocked(getApiUrl)
const dialogState = {} as DialogStateStore

beforeEach(() => {
  mockedGet.mockClear()
  mockedDelete.mockClear()
  mockedHandle.mockReset()
  mockedGetApiUrl.mockClear()
})

const bams: BamFile[] = [
  {
    original_file_name: 'sample1.bam',
    size_in_bytes: 500,
    mtime_epoch: 1705508468
  },
  {
    original_file_name: 'sample2.bam',
    size_in_bytes: 200,
    mtime_epoch: 1256084168
  }
]

test('getBamFilesByDatasetId calls /datasets/<datasetId>/attachments/bam', async () => {
  mockedHandle.mockResolvedValueOnce(bams)

  const result = await getBamFilesByDatasetId('d1', dialogState)

  expect(mockedGet).toHaveBeenCalledWith('/datasets/d1/attachments/bams')
  expect(mockedHandle).toHaveBeenCalledWith(
    expect.anything(),
    "Failed to load bam files for dataset 'd1'",
    dialogState
  )
  expect(result).toBe(bams)
})

test('getBamFilesByDatasetId does not swallow failures', async () => {
  const error = new Error()
  mockedHandle.mockRejectedValueOnce(error)

  await expect(getBamFilesByDatasetId('d1', dialogState)).rejects.toBe(error)
})

test('deleteBamFile deletes /datasets/<datasetId>/attachments/bam/<name>', async () => {
  mockedHandle.mockResolvedValueOnce(undefined)

  await deleteBamFile('d1', 'sample 1.bam', dialogState)

  // encodeURI turns a space into %20 but leaves other path characters alone...
  expect(mockedDelete).toHaveBeenCalledWith('/datasets/d1/attachments/bams/sample%201.bam')
  expect(mockedHandle).toHaveBeenCalledWith(
    expect.anything(),
    "Failed to delete BAM file 'sample 1.bam' (dataset d1)",
    dialogState
  )
})

test('deleteBamFile does not swallow failures', async () => {
  const error = new Error()
  mockedHandle.mockRejectedValueOnce(error)

  await expect(deleteBamFile('d1', 'sample.bam', dialogState)).rejects.toBe(error)
})

test('getBamFileDownLoadURL builds the download URL via getApiUrl', () => {
  const url = getBamFileDownLoadURL('d1', 'sample.bam')

  expect(mockedGetApiUrl).toHaveBeenCalledWith('datasets/d1/attachments/bams/sample.bam')
  expect(url).toBe('/datasets/d1/attachments/bams/sample.bam')
})
