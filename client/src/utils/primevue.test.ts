import { test, expect } from 'vitest'
import {
  formatPrimvueSortMetas,
  getOptionsForPrimvueCascadeSelect,
  getOptionsForPrimvueTreeSelect
} from '@/utils/primevue'
import type { DataTableSortMeta } from 'primevue/datatable'

interface TestItem {
  cat1: string
  cat2: string
  value: string
}

const TEST_ITEMS: TestItem[] = [
  { cat1: 'a', cat2: 'x', value: 'aaa2' },
  { cat1: 'a', cat2: 'x', value: 'aaa3' },
  { cat1: 'b', cat2: 'z', value: 'ccc1' },
  { cat1: 'a', cat2: 'y', value: 'bbb2' },
  { cat1: 'a', cat2: 'y', value: 'bbb1' },
  { cat1: 'b', cat2: 'z', value: 'ccc2' },
  { cat1: 'a', cat2: 'x', value: 'aaa1' }
]

test('getOptionsForPrimvueCascadeSelect', () => {
  expect(getOptionsForPrimvueCascadeSelect(TEST_ITEMS, ['cat1', 'cat2', 'value'])).toStrictEqual([
    {
      label: 'a',
      cChildren: [
        {
          label: 'x',
          cChildren: [
            { cat1: 'a', cat2: 'x', value: 'aaa1' },
            { cat1: 'a', cat2: 'x', value: 'aaa2' },
            { cat1: 'a', cat2: 'x', value: 'aaa3' }
          ]
        },
        {
          label: 'y',
          cChildren: [
            { cat1: 'a', cat2: 'y', value: 'bbb1' },
            { cat1: 'a', cat2: 'y', value: 'bbb2' }
          ]
        }
      ]
    },
    {
      label: 'b',
      cChildren: [
        {
          label: 'z',
          cChildren: [
            { cat1: 'b', cat2: 'z', value: 'ccc1' },
            { cat1: 'b', cat2: 'z', value: 'ccc2' }
          ]
        }
      ]
    }
  ])
})

test('getOptionsForPrimvueTreeSelect', () => {
  expect(
    getOptionsForPrimvueTreeSelect(TEST_ITEMS, ['cat1', 'cat2', 'value'], 'value')
  ).toStrictEqual([
    {
      label: 'a',
      key: 'a',
      children: [
        {
          label: 'x',
          key: 'a/x',
          children: [
            { label: 'aaa1', key: 'aaa1' },
            { label: 'aaa2', key: 'aaa2' },
            { label: 'aaa3', key: 'aaa3' }
          ]
        },
        {
          label: 'y',
          key: 'a/y',
          children: [
            { label: 'bbb1', key: 'bbb1' },
            { label: 'bbb2', key: 'bbb2' }
          ]
        }
      ]
    },
    {
      label: 'b',
      key: 'b',
      children: [
        {
          label: 'z',
          key: 'b/z',
          children: [
            { label: 'ccc1', key: 'ccc1' },
            { label: 'ccc2', key: 'ccc2' }
          ]
        }
      ]
    }
  ])
})

test('formatPrimvueSortMeta', () => {
  const input: DataTableSortMeta[] = [
    { field: 'x', order: 1 },
    { field: 'y', order: -1 },
    { field: 'z' },
    {}
  ]
  expect(formatPrimvueSortMetas(input)).toStrictEqual(['x%2Basc', 'y%2Bdesc', 'z'])
})
