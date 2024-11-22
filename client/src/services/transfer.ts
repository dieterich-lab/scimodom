import type { DialogStateStore } from '@/stores/DialogState'
import { handleRequestWithErrorReporting, HTTPSecure } from '@/services/API'

interface PostFileResponse {
  file_id: string
}

async function postTemporaryFile(
  file: File,
  dialogState: DialogStateStore
): Promise<PostFileResponse> {
  return await handleRequestWithErrorReporting<PostFileResponse>(
    HTTPSecure.post('transfer/tmp_upload', file),
    `Failed to upload '${file.name}'`,
    dialogState
  )
}

export { postTemporaryFile }
