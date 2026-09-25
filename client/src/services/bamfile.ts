import { type DialogStateStore } from '@/stores/DialogState'
import { getApiUrl, handleRequestWithErrorReporting, HTTP, HTTPSecure } from '@/services/API'

interface BamFile {
  original_file_name: string
  size_in_bytes: number
  mtime_epoch: number
}

async function getBamFilesByDatasetId(
  datasetId: string,
  dialogState: DialogStateStore
): Promise<BamFile[]> {
  return await handleRequestWithErrorReporting<BamFile[]>(
    HTTP.get(`/datasets/${datasetId}/attachments/bams`),
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
    HTTPSecure.delete(`/datasets/${datasetId}/attachments/bams/${cookedName}`),
    `Failed to delete BAM file '${name}' (dataset ${datasetId})`,
    dialogState
  )
}

// GET - used in BamFileTable.vue as a normal hyperlink
function getBamFileDownLoadURL(datasetId: string, name: string): string {
  const cookedName = encodeURI(name)
  return getApiUrl(`datasets/${datasetId}/attachments/bams/${cookedName}`)
}

export { type BamFile, getBamFilesByDatasetId, deleteBamFile, getBamFileDownLoadURL }
