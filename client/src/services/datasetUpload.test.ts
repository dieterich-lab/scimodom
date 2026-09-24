import { test, expect, vi, beforeEach } from 'vitest'
import { uploadTemporaryDataset, type UploadResponse } from '@/services/datasetUpload'
import { handleRequestWithErrorReporting, HTTPSecure } from '@/services/API'
import { DIALOG, type DialogStateStore } from '@/stores/DialogState'
import { type AxiosResponse } from 'axios'

vi.mock('@/services/API', () => ({
  HTTPSecure: { post: vi.fn().mockResolvedValue({} as AxiosResponse) },
  handleRequestWithErrorReporting: vi.fn()
}))

const mockedPost = vi.mocked(HTTPSecure.post)
const mockedHandle = vi.mocked(handleRequestWithErrorReporting)

const MAX_UPLOAD_SIZE = 50 * 1024 * 1024

function makeDialogState(): DialogStateStore {
  return { message: '', state: '' } as unknown as DialogStateStore
}

function makeFile(name: string, size = 100): File {
  const file = new File(['x'], name, { type: 'application/octet-stream' })
  // File.size is read-only; override it so we can simulate large files
  // without allocating 50 MB in the test
  Object.defineProperty(file, 'size', { value: size })
  return file
}

beforeEach(() => {
  mockedPost.mockClear()
  mockedHandle.mockReset()
})

test('uploadTemporaryDataset accepts a file at exactly the size limit', async () => {
  mockedHandle.mockResolvedValueOnce({ file_id: 'abc' } as UploadResponse)
  const dialogState = makeDialogState()
  const file = makeFile('at-limit.bed', MAX_UPLOAD_SIZE)

  const result = await uploadTemporaryDataset(file, dialogState)

  expect(mockedPost).toHaveBeenCalledTimes(1)
  expect(mockedPost).toHaveBeenCalledWith('/uploads', file)
  expect(mockedHandle).toHaveBeenCalledWith(
    expect.anything(),
    "Failed to upload 'at-limit.bed'",
    dialogState
  )
  expect(result).toEqual({ name: 'at-limit.bed', id: 'abc' })
})

// we could test toBeInstanceOf(DatasetTooLarge) if this is exported from datasetUpload
test('uploadTemporaryDataset rejects a file over the size limit without calling the API', async () => {
  const dialogState = makeDialogState()
  const file = makeFile('too-big.bed', MAX_UPLOAD_SIZE + 1)

  await expect(uploadTemporaryDataset(file, dialogState)).rejects.toThrow()

  expect(mockedPost).not.toHaveBeenCalled()
  expect(mockedHandle).not.toHaveBeenCalled()
  expect(dialogState.message).toContain('File too large: 52428801 bytes (max. 52428800)')
  expect(dialogState.state).toBe(DIALOG.ALERT)
})

test('uploadTemporaryDataset does not swallow failures', async () => {
  const error = new Error()
  mockedHandle.mockRejectedValueOnce(error)
  const dialogState = makeDialogState()
  const file = makeFile('sample.bedrmod')

  await expect(uploadTemporaryDataset(file, dialogState)).rejects.toBe(error)
})
