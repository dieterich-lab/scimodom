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
  modification_type: string
  sequencing_platform: string | null
  basecalling: string | null
  bioinformatics_workflow: string | null
  experiment: string | null
  rna_type: string
  external_source: string | null
  modifications: string
  tech: string
  taxa_short_name: string
  taxa_id: number
  cto: string
}

// extend dataset metadata with parent project
interface DatasetWithProject extends Dataset {
  project_title: string
  project_summary: string
  doi?: string
  pmid?: string // concat
}

class AllDatasetCache extends Cache<Dataset[]> {
  async getPromise(): Promise<Dataset[]> {
    const response = await HTTP.get<Dataset[]>('/datasets')
    return response.data
  }
}

class MyDatasetCache extends Cache<Dataset[]> {
  async getPromise(): Promise<Dataset[]> {
    const response = await HTTPAuth.get<Dataset[]>('/users/me/datasets')
    return response.data
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
  const data = await handleRequestWithErrorReporting(
    HTTPAuth.get<MayChangeDatasetResponse>(`/users/me/datasets/${datasetId}/permissions`),
    `Failed to load dataset '${datasetId}' permission for user`,
    dialogState
  )
  return data.write_access
}

async function getDatasetSummary(dialogState: DialogStateStore): Promise<DatasetSummaryResponse> {
  return await handleRequestWithErrorReporting(
    HTTP.get<DatasetSummaryResponse>('/datasets/summary'),
    'Failed to load dataset summary',
    dialogState
  )
}

export {
  type Dataset,
  type DatasetWithProject,
  type DatasetSummaryResponse,
  allDatasetsCache,
  allDatasetsByIdCache,
  myDatasetsCache,
  myDatasetsByIdCache,
  getDatasetsByTaxaId,
  mayChangeDataset,
  getDatasetSummary
}
