import { type DialogStateStore } from '@/stores/DialogState'
import { handleRequestWithErrorReporting, HTTP } from '@/services/API'

interface BioTypesResponse {
  biotypes: string[]
}

async function getBioTypes(rnaType: string, dialogState: DialogStateStore): Promise<string[]> {
  const raw = await handleRequestWithErrorReporting<BioTypesResponse>(
    HTTP.get(`/catalogs/rna-types/${rnaType}/biotypes`),
    `Failed to load BiotypesResponse: ${rnaType})`,
    dialogState
  )
  return raw.biotypes
}

export { getBioTypes }
