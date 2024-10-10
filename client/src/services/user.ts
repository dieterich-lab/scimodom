import type { DialogStateStore } from '@/stores/DialogState'
import { handleRequestWithErrorReporting } from '@/utils/request'
import { HTTPSecure } from '@/services/API'

interface MayChangeDatasetResponse {
  write_access: boolean
}

async function mayChangeDataset(
  datasetId: string,
  dialogState: DialogStateStore
): Promise<boolean> {
  const data = await handleRequestWithErrorReporting<MayChangeDatasetResponse>(
    HTTPSecure.get(`/user/may_change_dataset/${datasetId}`),
    `Failed to determine if öpgged-in user may change dataset '${datasetId}'`,
    dialogState
  )
  return data.write_access
}

export { mayChangeDataset }
