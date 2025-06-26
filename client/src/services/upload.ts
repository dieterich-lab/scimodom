import type { DialogStateStore } from '@/stores/DialogState'
import { handleRequestWithErrorReporting, HTTPAuth } from '@/services/API'

interface PostFileResponse {
  file_id: string
}

async function postTemporaryFile(
  file: File,
  dialogState: DialogStateStore
): Promise<PostFileResponse> {
  return await handleRequestWithErrorReporting<PostFileResponse>(
    HTTPAuth.post('/uploads', file),
    `Failed to upload '${file.name}'`,
    dialogState
  )
}

export { postTemporaryFile }
