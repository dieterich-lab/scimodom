import { type Bed6Record, type Strand } from '@/utils/bed6'
import type { DialogStateStore } from '@/stores/DialogState'
import { getApiUrl, handleRequestWithErrorReporting, HTTP } from '@/services/API'
import type { DataTableSortMeta } from 'primevue/datatable'
import { formatPrimvueSortMetas } from '@/utils/primevue'
import type { SearchParameters } from '@/utils/search'

interface Modification {
  id: number
  chrom: string
  start: number
  end: number
  name: string
  score: number
  strand: Strand
  coverage: number
  frequency: number
  dataset_id: string
  feature: string
  gene_id: string
  gene_name: string
  tech: string
  taxa_id: number
  cto: string
}

interface ModificationRequest {
  modification?: number
  organism?: number
  technology?: number[]
  rnaType?: string
  taxaId: number
  geneName?: string
  biotypes?: string[]
  features?: string[]
  chrom?: string
  chromStart?: number
  chromEnd?: number
  firstRecord?: number
  maxRecords?: number
  multiSort?: string[]
}

interface ModificationResponse {
  records: Modification[]
  totalRecords: number
}

interface SiteParams {
  taxaId: number
  chrom: string
  start: number
  end: number
  strand: Strand
}

interface TargetSitesResponse {
  records: Bed6Record[]
}

interface GenomicContextResponse {
  context: string
}

interface SiteWiseInfo extends Bed6Record {
  dataset_id: string
  modification_id: number
  rna: string
  short_name: string
  cto: string
  tech: string
  coverage: number
  frequency: number
}

interface SiteWiseResponse {
  records: SiteWiseInfo[]
}

async function getModifications(
  searchParameters: SearchParameters,
  dialogState: DialogStateStore,
  offset?: number,
  limit?: number,
  sortMetas?: DataTableSortMeta[]
): Promise<ModificationResponse> {
  const url =
    searchParameters.searchBy === 'Gene/Chrom' ? '/modification/query/gene' : '/modification/query'
  const params = {
    ...getQueryParametersFromSearchParameters(searchParameters, sortMetas),
    firstRecord: offset,
    maxRecords: limit
  }
  return await handleRequestWithErrorReporting<ModificationResponse>(
    HTTP.get(url, { params: params }),
    'Failed to load features',
    dialogState
  )
}

function getQueryParametersFromSearchParameters(
  p: SearchParameters,
  sortMetas?: DataTableSortMeta[]
): ModificationRequest {
  return {
    modification: p.modificationType?.modification_id,
    organism: p.cto?.organism_id,
    technology: p.technologies?.map((x) => x.technology_id),
    rnaType: p.rna_type,
    taxaId: p.taxa.taxa_id,
    geneName: p.gene,
    biotypes: p.biotypes,
    features: p.features,
    chrom: p.chrom?.chrom,
    chromStart: p.chromStart,
    chromEnd: p.chromEnd,
    multiSort: formatPrimvueSortMetas(sortMetas)
  }
}

function getModificationExportLink(
  searchParameters: SearchParameters,
  sortMetas?: DataTableSortMeta[],
  getApiUrlCb: (uri: string) => string = getApiUrl
) {
  const uri =
    searchParameters.searchBy === 'Gene/Chrom' ? 'modification/csv/gene' : 'modification/csv'
  const rawParams = getQueryParametersFromSearchParameters(searchParameters, sortMetas)
  const params = new URLSearchParams()
  for (const [k, v] of Object.entries(rawParams)) {
    if (v) {
      if (Array.isArray(v)) {
        v.forEach((x) => params.append(k, x))
      } else {
        params.append(k, v)
      }
    }
  }
  return getApiUrlCb(uri) + '?' + params.toString()
}

function getSiteParams(modification: Modification): SiteParams {
  return {
    ...modification,
    taxaId: modification.taxa_id
  }
}

async function getTargetSites(
  modification: Modification,
  target: string,
  dialogState: DialogStateStore
): Promise<Bed6Record[]> {
  const params = getSiteParams(modification)
  const data = await handleRequestWithErrorReporting<TargetSitesResponse>(
    HTTP.get(`/modification/target/${target}`, { params, paramsSerializer: { indexes: null } }),
    `Failed to load sites for target '${target}' for modification ${modification.id}`,
    dialogState
  )
  return data.records
}

async function getGenomicContext(
  modification: Modification,
  context: number,
  dialogState: DialogStateStore
): Promise<string> {
  const params = getSiteParams(modification)
  const data = await handleRequestWithErrorReporting<GenomicContextResponse>(
    HTTP.get(`/modification/genomic-context/${context}`, {
      params,
      paramsSerializer: { indexes: null }
    }),
    `Failed to get context '${context}' for modification ${modification.id}`,
    dialogState
  )
  return data.context
}

async function getSiteWiseInfo(
  modification: Modification,
  dialogState: DialogStateStore
): Promise<SiteWiseInfo[]> {
  const params = getSiteParams(modification)
  const data = await handleRequestWithErrorReporting<SiteWiseResponse>(
    HTTP.get('/modification/sitewise', { params, paramsSerializer: { indexes: null } }),
    `Failed to get site info for modification ${modification.id}`,
    dialogState
  )
  return data.records
}

export {
  type Modification,
  type ModificationResponse,
  type SiteWiseInfo,
  getModifications,
  getModificationExportLink,
  getTargetSites,
  getGenomicContext,
  getSiteWiseInfo
}
