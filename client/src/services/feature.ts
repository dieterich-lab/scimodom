import { type DialogStateStore } from '@/stores/DialogState'
import { handleRequestWithErrorReporting, HTTP } from '@/services/API'

interface FeaturesResponse {
  features: string[]
}

async function getFeaturesByRnaType(
  rnaType: string,
  dialogState: DialogStateStore
): Promise<string[]> {
  const raw = await handleRequestWithErrorReporting<FeaturesResponse>(
    HTTP.get(`/catalogs/rna-types/${rnaType}/features`),
    `Failed to load FeaturesResponse: ${rnaType})`,
    dialogState
  )
  return raw.features
}

export { getFeaturesByRnaType }
