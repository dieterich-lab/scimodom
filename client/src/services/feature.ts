import { type DialogStateStore } from '@/stores/DialogState'
import { handleRequestWithErrorReporting, HTTP } from '@/services/API'

async function getFeaturesByRnaType(
  rnaType: string,
  dialogState: DialogStateStore
): Promise<string[]> {
  const raw = await handleRequestWithErrorReporting<{ features: string[] }>(
    HTTP.get(`/features/${rnaType}`),
    `Failed to load features (rnaType: "${rnaType}")`,
    dialogState
  )
  return raw.features
}

export { getFeaturesByRnaType }
