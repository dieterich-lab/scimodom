import { HTTP, HTTPSecure } from '@/services/API'

let allProjectsCache = null
let allProjectsByIdCache = null
let myProjectsCache = null
let myProjectsByIdCache = null

async function loadAllProjects(projectsRef = null, refresh = false) {
  if (refresh || allProjectsCache === null) {
    try {
      const response = await HTTP.get('/project/list_all')
      allProjectsCache = response.data
      allProjectsByIdCache = null
    } catch (err) {
      console.log(`Failed to fetch all projects: ${err}`)
    }
  }
  if (projectsRef !== null) {
    projectsRef.value = allProjectsCache
  }
}

async function loadAllProjectsById(projectsByIdRef, refresh = false) {
  if (refresh || allProjectsCache === null) {
    await loadAllProjects(null, refresh)
  }
  if (allProjectsByIdCache === null) {
    allProjectsByIdCache = mapProjectsById(allProjectsCache)
  }
  projectsByIdRef.value = allProjectsByIdCache
}

function mapProjectsById(asList) {
  return asList.reduce((map, project) => {
    map[project.project_id] = project
    return map
  }, {})
}

async function loadMyProjects(projectsRef = null, refresh = false) {
  if (refresh || allProjectsCache === null) {
    try {
      const response = await HTTPSecure.get('/project/list_mine')
      myProjectsCache = response.data
      myProjectsByIdCache = null
    } catch (err) {
      console.log(`Failed to fetch my projects: ${err}`)
    }
  }
  if (projectsRef !== null) {
    projectsRef.value = await myProjectsCache
  }
}

async function loadMyProjectsById(projectsByIdRef, refresh = false) {
  if (refresh || myProjectsCache === null) {
    await loadMyProjects(null, refresh)
  }
  if (myProjectsByIdCache === null) {
    myProjectsByIdCache = mapProjectsById(myProjectsCache)
  }
  projectsByIdRef.value = myProjectsByIdCache
}

async function loadProjects(
  projectsRef = null,
  projectsByIdRef = null,
  onlyMine = false,
  refresh = true
) {
  if (onlyMine) {
    await loadMyProjects(projectsRef, refresh)
    if (projectsByIdRef !== null) {
      await loadMyProjectsById(projectsByIdRef)
    }
  } else {
    await loadAllProjects(projectsRef, refresh)
    if (projectsByIdRef !== null) {
      await loadAllProjectsById(projectsByIdRef)
    }
  }
}

export { loadProjects }
