import { HTTP, HTTPSecure } from '@/services/API'

let allProjectsCache = null
let myProjectsCache = null

async function loadAllProjects(projectsRef = null, refresh = false) {
  if (refresh || allProjectsCache === null) {
    try {
      const response = await HTTP.get('/project/list_all')
      allProjectsCache = response.data
    } catch (err) {
      console.log(`Failed to fetch all projects: ${error}`)
    }
  }
  if (projectsRef !== null) {
    projectsRef.value = allProjectsCache
  }
}

async function loadMyProjects(projectsRef = null, refresh = false) {
  if (refresh || allProjectsCache === null) {
    try {
      const response = await HTTPSecure.get('/project/list_mine')
      myProjectsCache = response.data
    } catch (err) {
      console.log(`Failed to fetch my projects: ${error}`)
    }
  }
  if (projectsRef !== null) {
    projectsRef.value = await myProjectsCache
  }
}

async function loadProjects(projectsRef = null, onlyMine = false, refresh = true) {
  if (onlyMine) {
    await loadMyProjects(projectsRef, refresh)
  } else {
    await loadAllProjects(projectsRef, refresh)
  }
}

export { loadAllProjects, loadMyProjects, loadProjects }
