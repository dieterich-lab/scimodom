import { test, expect } from 'vitest'
import { getComparisonDisplayRecord } from '@/utils/comparison'

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
