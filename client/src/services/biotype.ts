import { type DialogStateStore } from '@/stores/DialogState'
import { handleRequestWithErrorReporting, HTTP } from '@/services/API'

interface BioTypesResponse {
  biotypes: string[]
}

async function getBioTypes(rnaType: string = '', dialogState: DialogStateStore): Promise<string[]> {
  const raw = await handleRequestWithErrorReporting<BioTypesResponse>(
    HTTP.get(`/biotypes/${rnaType}`),
    `Failed to load biotypes (rnaType "${rnaType}")`,
    dialogState
  )
  return raw.biotypes
}

export { getBioTypes }
