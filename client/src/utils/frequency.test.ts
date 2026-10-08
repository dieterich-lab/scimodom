import { expect, test } from 'vitest'
import { formatFrequency } from '@/utils/frequency'

test('fixed number of decimals', () => {
  expect(formatFrequency(5)).toBe('5.00')
  expect(formatFrequency(5.4)).toBe('5.40')
  expect(formatFrequency(5.45)).toBe('5.45')
  expect(formatFrequency(100)).toBe('100.00')
  expect(formatFrequency(0)).toBe('0.00')
})
