import type { ComparisonRecord } from '@/services/comparison'

enum ComparisonOperation {
  intersect,
  closest,
  subtract
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
  a?: ComparisonRecord,
  b?: ComparisonRecord,
  distance?: number
): ComparisonDisplayRecord {
  return {
    a: recordToStrings(a),
    b: recordToStrings(b),
    distance: distance !== undefined ? `${distance}` : ''
  }
}

function recordToStrings(x?: ComparisonRecord): ComparisonRecordString {
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

export { type ComparisonDisplayRecord, ComparisonOperation, getComparisonDisplayRecord }
