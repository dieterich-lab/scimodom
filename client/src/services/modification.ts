import { type Strand } from '@/utils/common'
import type { DialogStateStore } from '@/stores/DialogState'
import { handleRequestWithErrorReporting } from '@/utils/request'
import { HTTP } from '@/services/API'
import type { DataTableSortMeta } from 'primevue/datatable'
import { formatPrimvueSortMetas } from '@/utils/primevue'

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

interface ModificationResponse {
  records: Modification[]
  totalReccords: number
}

async function getModifications(
  searchParameters: SearchParameters,
  dialogState: DialogStateStore,
  offset?: number,
  limit?: number,
  sortMetas?: DataTableSortMeta[]
): Promise<ModificationResponse> {
  const p = searchParameters
  const url = p.searchBy === 'Gene/Chrom' ? '/modification/query/gene' : '/modification/query'
  const params = {
    // reformat filters for gene, biotypes and features as PV table filters
    modification: p.modificationType,
    organism: p.organism.organism_id,
    technology: p.technologies,
    rnaType: p.modificationType?.rna_name,
    taxaId: p.organism.taxa_id,
    geneFilter: getGeneFilters(p),
    chrom: p.chrom,
    chromStart: p.chromStart,
    chromEnd: p.chromEnd,
    firstRecord: offset,
    maxRecords: limit,
    multiSort: formatPrimvueSortMetas(sortMetas)
  }
  return await handleRequestWithErrorReporting<ModificationResponse>(
    HTTP.get(url, { params: params }),
    'Failed to load features',
    dialogState
  )
}

function getGeneFilters(searchParameters: SearchParameters): string[] {
  const p = searchParameters
  for (const { name, value, matchMode } of [
    // matchMode is actually hard coded to "equal" in the BE; forceSelection is toggled
    { name: 'gene_name', value: p.gene, matchMode: 'startsWith' },
    { name: 'gene_biotype', value: p.biotypes, matchMode: 'in' },
    { name: 'feature', value: p.features, matchMode: 'in' }
  ]) {
    if (!value?.length) {
      continue
    }
    return `${name}%2B${value}%2B${matchMode}`
  }
}

export { type Modification, type ModificationResponse, getModifications }
