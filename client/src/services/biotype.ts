import { type DialogStateStore } from '@/stores/DialogState'
import { handleRequestWithErrorReporting, HTTP } from '@/services/API'

interface BioTypesResponse {
  biotypes: string[]
}

async function getBioTypes(rnaType: string, dialogState: DialogStateStore): Promise<string[]> {
  const data = await handleRequestWithErrorReporting<BioTypesResponse>(
    HTTP.get(`/catalogs/rna-types/${rnaType}/biotypes`),
    `Failed to load BiotypesResponse: ${rnaType}`,
    dialogState
  )
  return data.biotypes
}

export { getBioTypes }
