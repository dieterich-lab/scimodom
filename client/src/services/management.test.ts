import { test, expect, vi, beforeEach } from 'vitest'
import {
  postDataset,
  postProject,
  type DatasetPostRequest,
  type ProjectPostRequest
} from '@/services/management'
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

function makeDatasetRequest(): DatasetPostRequest {
  return {
    smid: 'SMID001',
    file_id: 'file-abc',
    rna_type: 'WTS',
    modification_id: [7],
    organism_id: 1,
    assembly_id: 42,
    technology_id: 3,
    title: 'My dataset'
  }
}

function makeProjectRequest(): ProjectPostRequest {
  return {
    title: 'My project',
    summary: 'A summary',
    contact_name: 'Ada Lovelace',
    contact_institution: 'Analytical Engines',
    contact_email: 'ada@example.org',
    date_published: '2025-01-01',
    external_sources: [{ doi: '10.1234/x', pmid: 12345 }],
    metadata: [
      {
        rna: 'WTS',
        modomics_id: '123',
        tech: 't1',
        method_id: 'm1',
        note: 'note',
        organism: {
          taxa_id: 9606,
          cto: 'HeLa',
          assembly_name: 'GRCh38',
          assembly_id: '1' // string!
        }
      }
    ]
  }
}

test('postDataset posts the request body to /datasets', async () => {
  const request = makeDatasetRequest()
  mockedHandle.mockResolvedValueOnce(undefined)

  await postDataset(request, dialogState)

  expect(mockedPost).toHaveBeenCalledWith('/datasets', request)
  expect(mockedHandle).toHaveBeenCalledWith(
    expect.anything(),
    'Failed to post dataset',
    dialogState
  )
})

test('postDataset passes the request body', async () => {
  const request = makeDatasetRequest()
  mockedHandle.mockResolvedValueOnce(undefined)

  await postDataset(request, dialogState)

  const [, postedBody] = mockedPost.mock.calls[0]
  expect(postedBody).toBe(request)
})

test('postDataset does not swallow failures', async () => {
  const error = new Error()
  mockedHandle.mockRejectedValueOnce(error)

  await expect(postDataset(makeDatasetRequest(), dialogState)).rejects.toBe(error)
})

test('postProject posts the request body to /projects/requests', async () => {
  const request = makeProjectRequest()
  mockedHandle.mockResolvedValueOnce(undefined)

  await postProject(request, dialogState)

  expect(mockedPost).toHaveBeenCalledWith('/management/project', request)
  expect(mockedHandle).toHaveBeenCalledWith(
    expect.anything(),
    'Failed to post project request',
    dialogState
  )
})

test('postProject passes the request body', async () => {
  const request = makeProjectRequest()
  mockedHandle.mockResolvedValueOnce(undefined)

  await postProject(request, dialogState)

  const [, postedBody] = mockedPost.mock.calls[0]
  expect(postedBody).toBe(request)
})

test('postProject does not swallow failures', async () => {
  const error = new Error()
  mockedHandle.mockRejectedValueOnce(error)

  await expect(postProject(makeProjectRequest(), dialogState)).rejects.toBe(error)
})
