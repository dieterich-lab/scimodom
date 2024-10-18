import { type Strand } from '@/utils/common'
import { handleRequestWithErrorReporting } from '@/utils/request'
import { HTTP } from '@/services/API'
import type { DialogStateStore } from '@/stores/DialogState'

interface ComparisonParams {
  reference: string[]
  comparison: string[]
  upload?: string
  upload_name?: string
  strand: boolean
  euf: boolean
}

interface ComparisonRecord {
  chrom: string
  start: number
  end: number
  name: string
  score: number
  strand: Strand
  coverage: number
  frequency: number
  eufid: string
}

interface SubtractRecord extends ComparisonRecord {}

interface IntersectRecord {
  a: ComparisonRecord
  b: ComparisonRecord
}

interface ClosestRecord {
  a: ComparisonRecord
  b: ComparisonRecord
  distance: number
}

async function do_http_get<T>(
  operation: string,
  params: ComparisonParams,
  dialogState: DialogStateStore
): Promise<any> {
  return (await handleRequestWithErrorReporting(
    HTTP.get(`/dataset/${operation}`, {
      params: params,
      paramsSerializer: {
        indexes: null
      }
    }),
    `Failed to do ${operation}`,
    dialogState
  )) as T[]
}

async function subtract(
  params: ComparisonParams,
  dialogState: DialogStateStore
): Promise<SubtractRecord[]> {
  return await do_http_get<SubtractRecord>('subtract', params, dialogState)
}

async function intersect(
  params: ComparisonParams,
  dialogState: DialogStateStore
): Promise<IntersectRecord[]> {
  return await do_http_get<IntersectRecord>('intersect', params, dialogState)
}

async function closest(
  params: ComparisonParams,
  dialogState: DialogStateStore
): Promise<ClosestRecord[]> {
  return await do_http_get<ClosestRecord>('closest', params, dialogState)
}

export {
  type ComparisonRecord,
  type ComparisonParams,
  type SubtractRecord,
  type IntersectRecord,
  type ClosestRecord,
  subtract,
  intersect,
  closest
}
