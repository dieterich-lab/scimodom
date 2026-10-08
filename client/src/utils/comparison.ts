import type { EufRecord } from '@/utils/bed6'
import type { Dataset } from '@/services/dataset'
import type { UploadedFile } from '@/services/dataset-upload'
import type { ComparisonParams } from '@/services/comparison'
import { isReactive } from 'vue'
import { formatFrequency } from '@/utils/frequency'

interface UploadDescriptor extends UploadedFile {
  isEUF: boolean
}

interface ComparisonDatasets {
  datasets: Dataset[]
}

interface ResultStepA {
  taxaId: number
  datasets: Dataset[]
  remainingDatasets: Dataset[]
}

type ResultStepB = UploadDescriptor | ComparisonDatasets

function isUpload(x: ResultStepB): x is UploadDescriptor {
  return (x as UploadDescriptor).name !== undefined
}
enum ComparisonOperation {
  intersect = 'intersect',
  closest = 'closest',
  subtract = 'subtract'
}

interface OperationSpec {
  operation: ComparisonOperation
  strandAware: boolean
}

type ResultStepC = OperationSpec

function getCompareParams(
  resultStepA: ResultStepA,
  resultStepB: ResultStepB,
  resultStepC: ResultStepC
): ComparisonParams {
  const paramsStepB = isUpload(resultStepB)
    ? {
        upload: resultStepB.id,
        uploadName: resultStepB.name,
        euf: resultStepB.isEUF
      }
    : {
        comparison: resultStepB.datasets.map((x) => x.dataset_id)
      }

  return {
    taxaId: resultStepA.taxaId,
    reference: resultStepA.datasets.map((x) => x.dataset_id),
    ...paramsStepB,
    strandAware: resultStepC?.strandAware === true
  }
}

interface ComparisonRecordString {
  chrom: string
  start: string
  end: string
  name: string
  score: string
  strand: string
  coverage: string
  frequency: string
  dataset_id: string
}

interface ComparisonDisplayRecord {
  reference: ComparisonRecordString
  comparison: ComparisonRecordString
  distance: string
}

interface ComparisonDisplayOptions {
  distance?: number
  isEUF?: boolean
}

const NULL_COMPARISON_RECORD: ComparisonRecordString = {
  chrom: '',
  start: '',
  end: '',
  name: '',
  score: '',
  strand: '',
  coverage: '',
  frequency: '',
  dataset_id: ''
}

function getComparisonDisplayRecord(
  a?: EufRecord,
  b?: EufRecord,
  options: ComparisonDisplayOptions = {}
): ComparisonDisplayRecord {
  const { distance, isEUF = true } = options
  return {
    reference: recordToStrings(true, a),
    comparison: recordToStrings(isEUF, b),
    distance: distance !== undefined ? `${distance}` : ''
  }
}

function recordToStrings(isEUF: boolean, x?: EufRecord): ComparisonRecordString {
  if (x === undefined) {
    return NULL_COMPARISON_RECORD
  }
  return {
    ...x,
    start: `${x.start}`,
    end: `${x.end}`,
    score: `${x.score}`,
    strand: `${x.strand}`,
    coverage: isEUF ? `${x.coverage}` : '',
    frequency: isEUF ? formatFrequency(x.frequency) : ''
  }
}

export {
  type ResultStepA,
  type ResultStepB,
  type ResultStepC,
  type OperationSpec,
  type ComparisonDisplayRecord,
  isUpload,
  ComparisonOperation,
  getCompareParams,
  getComparisonDisplayRecord
}
