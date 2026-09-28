import { test, expect, vi, beforeEach } from 'vitest'
import {
  allProjectsCache,
  allProjectsByIdCache,
  myProjectsCache,
  myProjectsByIdCache,
  type Project
} from '@/services/project'
import { HTTP, HTTPSecure } from '@/services/API'
import { type AxiosResponse } from 'axios'

vi.mock('@/services/API', () => ({
  HTTP: { get: vi.fn().mockResolvedValue({} as AxiosResponse) },
  HTTPSecure: { get: vi.fn().mockResolvedValue({} as AxiosResponse) }
}))

const mockedGet = vi.mocked(HTTP.get)
const mockedSecureGet = vi.mocked(HTTPSecure.get)

beforeEach(() => {
  mockedGet.mockClear()
  mockedSecureGet.mockClear()
})

const projects: Project[] = [
  {
    pmid: '0123',
    project_title: 'title 1',
    project_id: 'smid1',
    project_summary: 'summary 1',
    doi: 'doi1',
    date_added: 1722494219.0,
    date_published: 1720483200.0,
    contact_name: 'name1',
    contact_institution: 'institution1'
  },
  {
    pmid: '456',
    project_title: 'title 2',
    project_id: 'smid2',
    project_summary: 'summary 2',
    doi: 'doi2',
    date_added: 1122494219.0,
    date_published: null,
    contact_name: 'name2',
    contact_institution: 'institution2'
  }
]

function mockGet(data: unknown): void {
  mockedGet.mockResolvedValueOnce({ data } as AxiosResponse)
}

function mockSecureGet(data: unknown): void {
  mockedSecureGet.mockResolvedValueOnce({ data } as AxiosResponse)
}

// Tests the exported instances, not their classes, cf. e.g. selection.test.ts
// The first test fetches, the others use the cache

test('allProjectsCache fetches /projects', async () => {
  mockGet(projects)

  const result = await allProjectsCache.getData()

  expect(mockedGet).toHaveBeenCalledWith('/projects')
  expect(result).toEqual(projects)
})

test('myProjectsCache fetches /users/me/projects', async () => {
  mockSecureGet(projects)

  const result = await myProjectsCache.getData()

  expect(mockedSecureGet).toHaveBeenCalledWith('/users/me/projects')
  expect(mockedGet).not.toHaveBeenCalled()
  expect(result).toEqual(projects)
})

test('allProjectsByIdCache', async () => {
  mockGet(projects)

  const map = await allProjectsByIdCache.getData(true)

  expect([...map.keys()].sort()).toEqual(['smid1', 'smid2'])
})
