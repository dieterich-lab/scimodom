import { expect, test } from 'vitest'
import {
  ComparisonOperation,
  getCompareParams,
  getComparisonDisplayRecord
} from '@/utils/comparison'
import type { Dataset } from '@/services/dataset'

test('getComparisonDisplayRecord empty', () => {
  const r = getComparisonDisplayRecord()
  expect(r.a.chrom).toBe('')
  expect(r.b.name).toBe('')
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
      eufid: 'abcd1234edgh'
    },
    {
      chrom: 'chrom1',
      start: 200,
      end: 299,
      strand: '-',
      name: 'name1',
      coverage: 98,
      frequency: 60,
      score: 11,
      eufid: 'abcd12345xyz'
    },
    55
  )
  expect(r.a.coverage).toBe('99')
  expect(r.b.eufid).toBe('abcd12345xyz')
  expect(r.distance).toBe('55')
})

function getDataset(index: number): Dataset {
  return {
    dataset_id: `d${index}`,
    project_id: `p${index}`,
    dataset_title: `t${index}`,
    sequencing_platform: null,
    basecalling: null,
    bioinformatics_workflow: null,
    experiment: null,
    project_title: `pt${index}`,
    project_summary: `foo bar ${index}`,
    doi: `doi${index}`,
    rna: 'rnaType',
    modomics_sname: 'modomics_sname',
    tech: 'tech',
    taxa_sname: 'taxa',
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
      name: 'fil1.bedrmod',
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
    upload_name: 'fil1.bedrmod',
    strand: false,
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
    strand: true,
    taxaId: 7
  })
})
