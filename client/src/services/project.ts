import { HTTP, HTTPSecure } from '@/services/API'
import { ByKeyCache, Cache } from '@/utils/cache'

interface Project {
  pmid: string
  project_title: string
  project_id: string
  project_summary: string
  doi: string
  date_added: number
  date_published: number | null
  contact_name: string
  contact_institution: string
}

class AllProjectsCache extends Cache<Project[]> {
  async getPromise(): Promise<Project[]> {
    try {
      const response = await HTTP.get('/projects')
      return response.data as Project[]
    } catch (err) {
      console.log(`Failed to fetch projects: ${err}`)
      throw err
    }
  }
}

class MyProjectsCache extends Cache<Project[]> {
  async getPromise(): Promise<Project[]> {
    try {
      const response = await HTTPSecure.get('/users/me/projects')
      return response.data as Project[]
    } catch (err) {
      console.log(`Failed to fetch my projects: ${err}`)
      throw err
    }
  }
}

const allProjectsCache = new AllProjectsCache()
const allProjectsByIdCache = new ByKeyCache(allProjectsCache, (p) => p.project_id)
const myProjectsCache = new MyProjectsCache()
const myProjectsByIdCache = new ByKeyCache(myProjectsCache, (p) => p.project_id)

export {
  type Project,
  allProjectsCache,
  allProjectsByIdCache,
  myProjectsCache,
  myProjectsByIdCache
}
