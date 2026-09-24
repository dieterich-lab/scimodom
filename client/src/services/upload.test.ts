import { test, expect, vi, beforeEach } from 'vitest'
import { postTemporaryFile } from '@/services/upload'
import { handleRequestWithErrorReporting, HTTPSecure } from '@/services/API'
import { type DialogStateStore } from '@/stores/DialogState'
import { type AxiosResponse } from 'axios'

vi.mock('@/services/API', () => ({
  HTTPSecure: { post: vi.fn().mockResolvedValue({} as AxiosResponse) },
  handleRequestWithErrorReporting: vi.fn()
}))

const mockedPost = vi.mocked(HTTPSecure.post)
const mockedHandle = vi.mocked(handleRequestWithErrorReporting)
const dialogState = {} as DialogStateStore

beforeEach(() => {
  mockedPost.mockClear()
  mockedHandle.mockReset()
})

function makeFile(name: string, content = 'x'): File {
  return new File([content], name, { type: 'text/plain' })
}

test('postTemporaryFile posts the file', async () => {
  const expected = { file_id: 'abc123' }
  mockedHandle.mockResolvedValueOnce(expected)
  const file = makeFile('sample.bedrmod')

  const result = await postTemporaryFile(file, dialogState)

  expect(mockedPost).toHaveBeenCalledWith('/uploads', file)
  expect(mockedHandle).toHaveBeenCalledWith(
    expect.anything(),
    "Failed to upload 'sample.bedrmod'",
    dialogState
  )
  expect(result).toBe(expected)
})

test('postTemporaryFile does not swallow failures', async () => {
  const error = new Error()
  mockedHandle.mockRejectedValueOnce(error)

  await expect(postTemporaryFile(makeFile('x'), dialogState)).rejects.toBe(error)
})
