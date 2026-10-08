import { expect, test } from 'vitest'
import {
  ComparisonOperation,
  getCompareParams,
  getComparisonDisplayRecord
} from '@/utils/comparison'
import type { Dataset } from '@/services/dataset'

test('getComparisonDisplayRecord empty', () => {
  const r = getComparisonDisplayRecord()
  expect(r.reference.chrom).toBe('')
  expect(r.comparison.name).toBe('')
  expect(r.distance).toBe('')
})

test('getComparisonDisplayRecord full', () => {
  const r = getComparisonDisplayRecord(
    {
      chrom: 'chrom1',
      start: 100,
      end: 199,
      strand: '+',
      name: 'name1',
      coverage: 99,
      frequency: 50,
      score: 10,
      dataset_id: 'abcd1234edgh'
    },
    {
      chrom: 'chrom1',
      start: 200,
      end: 299,
      strand: '-',
      name: 'name1',
      coverage: 98,
      frequency: 60.1,
      score: 11,
      dataset_id: 'abcd12345xyz'
    },
    { distance: 55 }
  )
  expect(r.reference.coverage).toBe('99')
  expect(r.comparison.dataset_id).toBe('abcd12345xyz')
  expect(r.comparison.frequency).toBe('60.10')
  expect(r.distance).toBe('55')
})

test('getComparisonDisplayRecord bed6', () => {
  const r = getComparisonDisplayRecord(
    {
      chrom: 'chrom1',
      start: 100,
      end: 199,
      strand: '+',
      name: 'name1',
      coverage: 99,
      frequency: 50,
      score: 10,
      dataset_id: 'abcd1234edgh'
    },
    {
      chrom: 'chrom1',
      start: 200,
      end: 299,
      strand: '-',
      name: 'name1',
      coverage: 98,
      frequency: 60.1,
      score: 11,
      dataset_id: 'UPLOAD'
    },
    { isEUF: false }
  )
  expect(r.reference.frequency).toBe('50.00')
  expect(r.comparison.coverage).toBe('')
  expect(r.comparison.frequency).toBe('')
})

function getDataset(index: number): Dataset {
  return {
    dataset_id: `d${index}`,
    project_id: `p${index}`,
    dataset_title: `t${index}`,
    modification_type: 'RNA',
    sequencing_platform: null,
    basecalling: null,
    bioinformatics_workflow: null,
    experiment: null,
    external_source: null,
    rna_type: 'rnaType',
    modifications: 'modomics_short_name',
    tech: 'tech',
    taxa_short_name: 'taxa',
    taxa_id: 7,
    cto: 'cto'
  }
}

test('getCompareParams - upload', () => {
  const result = getCompareParams(
    {
      taxaId: 7,
      datasets: [getDataset(1), getDataset(2)],
      remainingDatasets: []
    },
    {
      name: 'file1.bedrmod',
      id: 'fileId1',
      isEUF: true
    },
    {
      operation: ComparisonOperation.intersect,
      strandAware: false
    }
  )
  expect(result).toStrictEqual({
    reference: ['d1', 'd2'],
    upload: 'fileId1',
    uploadName: 'file1.bedrmod',
    strandAware: false,
    euf: true,
    taxaId: 7
  })
})

test('getCompareParams - internal', () => {
  const result = getCompareParams(
    {
      taxaId: 7,
      datasets: [getDataset(1)],
      remainingDatasets: []
    },
    {
      datasets: [getDataset(2), getDataset(3)]
    },
    {
      operation: ComparisonOperation.intersect,
      strandAware: true
    }
  )
  expect(result).toStrictEqual({
    reference: ['d1'],
    comparison: ['d2', 'd3'],
    strandAware: true,
    taxaId: 7
  })
})
