import { DIALOG, type DialogStateStore } from '@/stores/DialogState'
import { handleRequestWithErrorReporting, HTTPSecure } from '@/services/API'

const MAX_UPLOAD_SIZE = 50 * 1024 * 1024

class DatasetTooLarge extends Error {}

interface UploadedFile {
  id: string
  name: string
}

export interface UploadResponse {
  file_id: string
}

async function uploadTemporaryDataset(
  file: File,
  dialogState: DialogStateStore
): Promise<UploadedFile> {
  const file_size = file.size
  if (file_size > MAX_UPLOAD_SIZE) {
    dialogState.message = `This file is to large (${file_size} bytes, max ${MAX_UPLOAD_SIZE})`
    dialogState.state = DIALOG.ALERT
    throw new DatasetTooLarge()
  }
  const result = (await handleRequestWithErrorReporting(
    HTTPSecure.post('transfer/tmp_upload', file),
    `Failed to upload '${file.name}'`,
    dialogState
  )) as UploadResponse
  return {
    name: file.name,
    id: result.file_id
  }
}

export { uploadTemporaryDataset, type UploadedFile }
