import type { EufRecord } from '@/utils/bed6'

import type { Dataset } from '@/services/dataset'
import type { UploadedFile } from '@/services/dataset_upload'
import type { ComparisonParams } from '@/services/comparison'

interface UploadDescriptor extends UploadedFile {
  isEUF: boolean
}

interface ComparisonDatasets {
  datasets: Dataset[]
}

interface ResultStepA {
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
        upload_name: resultStepB.name,
        euf: resultStepB.isEUF
      }
    : {
        comparison: resultStepB.datasets.map((x) => x.dataset_id)
      }

  return {
    reference: resultStepA.datasets.map((x) => x.dataset_id),
    ...paramsStepB,
    strand: resultStepC?.strandAware === true
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
  eufid: string
}

interface ComparisonDisplayRecord {
  a: ComparisonRecordString
  b: ComparisonRecordString
  distance: string
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
  eufid: ''
}

function getComparisonDisplayRecord(
  a?: EufRecord,
  b?: EufRecord,
  distance?: number
): ComparisonDisplayRecord {
  return {
    a: recordToStrings(a),
    b: recordToStrings(b),
    distance: distance !== undefined ? `${distance}` : ''
  }
}

function recordToStrings(x?: EufRecord): ComparisonRecordString {
  if (x === undefined) {
    return NULL_COMPARISON_RECORD
  }
  return {
    ...x,
    start: `${x.start}`,
    end: `${x.end}`,
    score: `${x.score}`,
    strand: `${x.strand}`,
    coverage: `${x.coverage}`,
    frequency: `${x.frequency}`
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
