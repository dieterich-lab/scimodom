import { type DialogStateStore } from '@/stores/DialogState'
import { getApiUrl, handleRequestWithErrorReporting, HTTP, HTTPSecure } from '@/services/API'

interface BamFile {
  id: number
  original_file_name: string
  storage_file_name: string
  dataset_id: string
}

async function getBamFilesByDatasetId(
  datasetId: string,
  dialogState: DialogStateStore
): Promise<BamFile[]> {
  return await handleRequestWithErrorReporting<BamFile[]>(
    HTTP.get(`/bam_file/all/${datasetId}`),
    `Failed to load bam files for dataset '${datasetId}'`,
    dialogState
  )
}

async function deleteBamFile(
  datasetId: string,
  name: string,
  dialogState: DialogStateStore
): Promise<void> {
  const cookedName = encodeURI(name)
  return await handleRequestWithErrorReporting(
    HTTPSecure.delete(`/bam_file/${datasetId}/${cookedName}`),
    `Failed to delete BAM file '${name}' (dataset ${datasetId})`,
    dialogState
  )
}

function getBamFileDownLoadURL(datasetId: string, name: string): string {
  const cookedName = encodeURI(name)
  return getApiUrl(`bam_file/${datasetId}/${cookedName}`)
}

export { type BamFile, getBamFilesByDatasetId, deleteBamFile, getBamFileDownLoadURL }
