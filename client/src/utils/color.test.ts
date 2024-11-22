import { test, expect } from 'vitest'
import { toRgb, rgbToString, ColorFactory } from '@/utils/color'

test.each<{ input: string; expected: number[] }>([
  { input: '#ffffff', expected: [255, 255, 255] },
  { input: '#FFFFFF', expected: [255, 255, 255] },
  { input: '#000000', expected: [0, 0, 0] },
  { input: '#204060', expected: [32, 64, 96] }
])('toRgb("%s") should return right value', ({ input, expected }) => {
  expect(toRgb(input)).toStrictEqual(expected)
})

test.each<{ input: number[]; expected: string }>([
  { input: [255, 255, 255], expected: '#ffffff' },
  { input: [0, 0, 0], expected: '#000000' },
  { input: [32, 64, 96], expected: '#204060' }
])('rgbToString() should return right value', ({ input, expected }) => {
  expect(rgbToString(input)).toStrictEqual(expected)
})

test.each<{
  input: { depth: number; parentColor: string }
  expected: { color: string; textColor: string; secondColor?: string }
}>([
  {
    input: { depth: 0, parentColor: '#777777' },
    expected: { color: '#F4F1F5FF', textColor: 'black' }
  },
  {
    input: { depth: 1, parentColor: '#777777' },
    expected: { color: '#00b052', textColor: 'white', secondColor: '#02aeed' }
  },
  {
    input: { depth: 2, parentColor: '#777777' },
    expected: { color: '#5d5d5d', textColor: 'white' }
  },
  {
    input: { depth: 2, parentColor: '#557799' },
    expected: { color: '#3b5d7f', textColor: 'white' }
  },
  {
    input: { depth: 3, parentColor: '#557799' },
    expected: { color: '#2f5173', textColor: 'white' }
  },
  {
    input: { depth: 2, parentColor: '#00b052' },
    expected: { color: '#009638', textColor: 'white' }
  }
])('test ColorFactory', ({ input, expected }) => {
  const f = new ColorFactory()
  expect(f.getColor(input.depth, input.parentColor)).toStrictEqual(expected.color)
  expect(f.getColor(input.depth, input.parentColor)).toStrictEqual(
    expected?.secondColor ? expected.secondColor : expected.color
  )
  expect(f.getTextColor(input.depth)).toStrictEqual(expected.textColor)
})
