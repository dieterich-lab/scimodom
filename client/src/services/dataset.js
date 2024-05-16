import { HTTP, HTTPSecure } from '@/services/API'

let allDatasetsCache = null
let allDatasetsByIdCache = null
let myDatasetsCache = null
let myDatasetsByIdCache = null

async function loadAllDatasets(datasetsRef = null, refresh = false) {
  if (refresh || allDatasetsCache === null) {
    try {
      const response = await HTTP.get('/dataset/list_all')
      allDatasetsCache = response.data
      allDatasetsByIdCache = null
    } catch (err) {
      console.log(`Failed to fetch all dataset: ${error}`)
    }
  }
  if (datasetsRef !== null) {
    datasetsRef.value = allDatasetsCache
  }
}

async function loadAllDatasetsById(datasetsByIdRef, refresh = false) {
  if (refresh || allDatasetsCache === null) {
    await loadAllDatasets(null, refresh)
  }
  if (allDatasetsByIdCache === null) {
    allDatasetsByIdCache = mapDatasetsById(allDatasetsCache)
  }
  datasetsByIdRef.value = allDatasetsByIdCache
}

function mapDatasetsById(asList) {
  return asList.reduce((map, dataset) => {
    map[dataset.dataset_id] = dataset
    return map
  }, {})
}

async function loadMyDatasets(datasetsRef = null, refresh = false) {
  if (refresh || allDatasetsCache === null) {
    try {
      const response = await HTTPSecure.get('/dataset/list_mine')
      myDatasetsCache = response.data
      myDatasetsByIdCache = null
    } catch (err) {
      console.log(`Failed to fetch MY dataset: ${error}`)
    }
  }
  if (datasetsRef !== null) {
    datasetsRef.value = await myDatasetsCache
  }
}

async function loadMyDatasetsById(datasetsByIdRef, refresh = false) {
  if (refresh || myDatasetsCache === null) {
    await loadMyDatasets(null, refresh)
  }
  if (myDatasetsByIdCache === null) {
    myDatasetsByIdCache = mapDatasetsById(myDatasetsCache)
  }
  datasetsByIdRef.value = myDatasetsByIdCache
}

async function loadDatasets(
  datasetsRef = null,
  datasetsByIdRef = null,
  onlyMine = false,
  refresh = true
) {
  if (onlyMine) {
    await loadMyDatasets(datasetsRef, refresh)
    if (datasetsByIdRef !== null) {
      await loadMyDatasetsById(datasetsByIdRef)
    }
  } else {
    await loadAllDatasets(datasetsRef, refresh)
    if (datasetsByIdRef !== null) {
      await loadAllDatasetsById(datasetsByIdRef)
    }
  }
}

export { loadDatasets }
