import { type DialogStateStore } from '@/stores/DialogState'
import { handleRequestWithErrorReporting, HTTP } from '@/services/API'

interface Chrom {
  chrom: string
  size: number
}

async function getChromsByTaxaId(taxaId: number, dialogState: DialogStateStore): Promise<Chrom[]> {
  return await handleRequestWithErrorReporting<Chrom[]>(
    HTTP.get(`/chroms/${taxaId}`),
    'Failed to load chromes',
    dialogState
  )
}

export { type Chrom, getChromsByTaxaId }
