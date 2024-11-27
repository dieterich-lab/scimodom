import { handleRequestWithErrorReporting, HTTP } from '@/services/API'
import { type DialogStateStore } from '@/stores/DialogState'
import { type EufRecord } from '@/utils/bed6'

interface ComparisonParams {
  reference: string[]
  comparison?: string[]
  upload?: string
  upload_name?: string
  strand: boolean
  euf?: boolean
  taxaId?: number
}

interface SubtractRecord extends EufRecord {}

interface IntersectRecord {
  a: EufRecord
  b: EufRecord
}

interface ClosestRecord {
  a: EufRecord
  b: EufRecord
  distance: number
}

interface Records<T> {
  records: T[]
}

async function doHttpGet<T>(
  operation: string,
  params: ComparisonParams,
  dialogState: DialogStateStore
): Promise<T[]> {
  const response = (await handleRequestWithErrorReporting(
    HTTP.get(`/dataset/${operation}`, {
      params: params,
      paramsSerializer: {
        indexes: null
      }
    }),
    `Comparison failed (${operation})`,
    dialogState
  )) as Records<T>
  return response.records
}

async function subtract(
  params: ComparisonParams,
  dialogState: DialogStateStore
): Promise<SubtractRecord[]> {
  return await doHttpGet<SubtractRecord>('subtract', params, dialogState)
}

async function intersect(
  params: ComparisonParams,
  dialogState: DialogStateStore
): Promise<IntersectRecord[]> {
  return await doHttpGet<IntersectRecord>('intersect', params, dialogState)
}

async function closest(
  params: ComparisonParams,
  dialogState: DialogStateStore
): Promise<ClosestRecord[]> {
  return await doHttpGet<ClosestRecord>('closest', params, dialogState)
}

export {
  type ComparisonParams,
  type SubtractRecord,
  type IntersectRecord,
  type ClosestRecord,
  subtract,
  intersect,
  closest
}
