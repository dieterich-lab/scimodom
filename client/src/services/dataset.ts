import { type DialogStateStore } from '@/stores/DialogState'
import { HTTP, HTTPAuth, handleRequestWithErrorReporting } from '@/services/API'
import { ByKeyCache, Cache } from '@/utils/cache'

interface DatasetSummaryResponse {
  count: number
}

interface MayChangeDatasetResponse {
  write_access: boolean
}

interface Dataset {
  project_id: string
  dataset_id: string
  dataset_title: string
  sequencing_platform: string | null
  basecalling: string | null
  bioinformatics_workflow: string | null
  experiment: string | null
  project_title: string
  project_summary: string
  doi?: string
  pmid?: number
  rna: string
  modomics_sname: string
  tech: string
  taxa_sname: string
  taxa_id: number
  cto: string
}

class AllDatasetCache extends Cache<Dataset[]> {
  async getPromise(): Promise<Dataset[]> {
    try {
      const response = await HTTP.get('/datasets')
      return response.data as Dataset[]
    } catch (err) {
      console.log(`Failed to fetch datasets: ${err}`)
      throw err
    }
  }
}

class MyDatasetCache extends Cache<Dataset[]> {
  async getPromise(): Promise<Dataset[]> {
    try {
      const response = await HTTPAuth.get('/users/me/datasets')
      return response.data as Dataset[]
    } catch (err) {
      console.log(`Failed to fetch my datasets: ${err}`)
      throw err
    }
  }
}

const allDatasetsCache = new AllDatasetCache()
const allDatasetsByIdCache = new ByKeyCache(allDatasetsCache, (d) => d.dataset_id)
const myDatasetsCache = new MyDatasetCache()
const myDatasetsByIdCache = new ByKeyCache(myDatasetsCache, (d) => d.dataset_id)

async function getDatasetsByTaxaId(taxaId: number): Promise<Readonly<Dataset[]>> {
  return (await allDatasetsCache.getData()).filter((item) => item.taxa_id === taxaId)
}

async function mayChangeDataset(
  datasetId: string,
  dialogState: DialogStateStore
): Promise<boolean> {
  const data = await handleRequestWithErrorReporting<MayChangeDatasetResponse>(
    HTTPAuth.get(`/users/me/datasets/${datasetId}/permissions`),
    `Failed to load dataset '${datasetId}' permission for user`,
    dialogState
  )
  return data.write_access
}

async function getDatasetSummary(dialogState: DialogStateStore): Promise<DatasetSummaryResponse> {
  return await handleRequestWithErrorReporting<DatasetSummaryResponse>(
    HTTP.get('/datasets/summary'),
    'Failed to load dataset summary',
    dialogState
  )
}

export {
  type Dataset,
  type DatasetSummaryResponse,
  allDatasetsCache,
  allDatasetsByIdCache,
  myDatasetsCache,
  myDatasetsByIdCache,
  getDatasetsByTaxaId,
  mayChangeDataset,
  getDatasetSummary
}
