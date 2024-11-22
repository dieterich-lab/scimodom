import { type DialogStateStore } from '@/stores/DialogState'
import { handleRequestWithErrorReporting, HTTP } from '@/services/API'

async function getGenesForSelectionIds(
  selectionIds: number[],
  dialogState: DialogStateStore
): Promise<string[]> {
  const raw = await handleRequestWithErrorReporting<string[]>(
    HTTP.get('/genes', { params: { selection: selectionIds } }),
    'Failed to load features',
    dialogState
  )
  return raw.sort()
}

export { getGenesForSelectionIds }
