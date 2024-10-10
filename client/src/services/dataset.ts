import { HTTP, HTTPSecure } from '@/services/API'
import { ByKeyCache, Cache } from '@/utils/cache'

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
      const response = await HTTP.get('/dataset/list_all')
      return response.data as Dataset[]
    } catch (err) {
      console.log(`Failed to fetch all datasets: ${err}`)
      throw err
    }
  }
}

class MyDatasetCache extends Cache<Dataset[]> {
  async getPromise(): Promise<Dataset[]> {
    try {
      const response = await HTTPSecure.get('/dataset/list_mine')
      return response.data as Dataset[]
    } catch (err) {
      console.log(`Failed to fetch MY datasets: ${err}`)
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

export {
  type Dataset,
  allDatasetsCache,
  allDatasetsByIdCache,
  myDatasetsCache,
  myDatasetsByIdCache,
  getDatasetsByTaxaId
}
