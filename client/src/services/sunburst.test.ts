import { test, expect, vi, beforeEach } from 'vitest'
import { getSunBurstData, type SunburstType } from '@/services/sunburst'
import { HTTP, handleRequestWithErrorReporting } from '@/services/API'
import { type DialogStateStore } from '@/stores/DialogState'
import { type AxiosResponse } from 'axios'

// URL.createObjectURL, etc. only exist in the browser
// so importing the real module aborts the whole test file
vi.mock('plotly.js', () => ({ default: {} }))
// import type-checks a mock factory against the real module, per-export,
// so HTTP.get fails against the real AxiosInstance interface
// plain string avoids needing to fake unused axios methods
vi.mock('@/services/API', () => ({
  HTTP: { get: vi.fn().mockResolvedValue({} as AxiosResponse) },
  handleRequestWithErrorReporting: vi.fn()
}))

const mockedGet = vi.mocked(HTTP.get)
const mockedHandle = vi.mocked(handleRequestWithErrorReporting)
// cast empty stand-in passed through by reference for the Pinia store to avoid TS2322
const dialogState = {} as DialogStateStore

beforeEach(() => {
  // clears out call history, but keeps assigned mockResolvedValue
  mockedGet.mockClear(), mockedHandle.mockReset()
})

function makeSunburstTree() {
  return [
    {
      name: 'Browse',
      children: [
        {
          name: 'm6A',
          children: [
            {
              name: 'H. sapiens',
              children: [
                {
                  name: 'HeLa',
                  children: [
                    { name: 'GLORI', size: 18 },
                    { name: 'xPore', size: 6 }
                  ]
                }
              ]
            }
          ]
        },
        {
          name: 'm5C',
          children: [
            {
              name: 'H. sapiens',
              children: [
                {
                  name: 'HeLa',
                  children: [{ name: 'UBS-seq', size: 2 }]
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}

test.each<SunburstType>(['search', 'browse'])(
  'getSunBurstData(%s) calls /charts/sunbursts and returns array',
  async (type) => {
    mockedHandle.mockResolvedValueOnce(makeSunburstTree())

    const data = await getSunBurstData(type, dialogState)

    expect(mockedGet).toHaveBeenCalledWith(`/charts/sunbursts/${type}`)
    expect(mockedHandle).toHaveBeenCalledWith(
      expect.anything(),
      `Failed to load SunburstResponseData: ${type}`,
      dialogState
    )
    // exactly one Plotly.PlotData
    expect(data).toHaveLength(1)
  }
)

test('getSunBurstData flattens the tree into arrays and calculates cumulativeSize', async () => {
  mockedHandle.mockResolvedValueOnce(makeSunburstTree())

  const [plotly] = await getSunBurstData('browse', dialogState)

  expect(plotly.ids).toEqual([
    'Browse',
    'Browse-m6A',
    'Browse-m6A-H. sapiens',
    'Browse-m6A-H. sapiens-HeLa',
    'Browse-m6A-H. sapiens-HeLa-GLORI',
    'Browse-m6A-H. sapiens-HeLa-xPore',
    'Browse-m5C',
    'Browse-m5C-H. sapiens',
    'Browse-m5C-H. sapiens-HeLa',
    'Browse-m5C-H. sapiens-HeLa-UBS-seq'
  ])
  expect(plotly.labels).toEqual([
    'Browse',
    'm6A',
    'H. sapiens',
    'HeLa',
    'GLORI',
    'xPore',
    'm5C',
    'H. sapiens',
    'HeLa',
    'UBS-seq'
  ])
  expect(plotly.parents).toEqual([
    '',
    'Browse',
    'Browse-m6A',
    'Browse-m6A-H. sapiens',
    'Browse-m6A-H. sapiens-HeLa',
    'Browse-m6A-H. sapiens-HeLa',
    'Browse',
    'Browse-m5C',
    'Browse-m5C-H. sapiens',
    'Browse-m5C-H. sapiens-HeLa'
  ])
  expect(plotly.values).toEqual([0, 0, 0, 0, 18, 6, 0, 0, 0, 2])
  expect(plotly.customdata).toEqual([26, 24, 24, 24, 18, 6, 2, 2, 2, 2])
})

test('getSunBurstData does not swallow failures', async () => {
  const error = new Error()
  mockedHandle.mockRejectedValueOnce(error)

  await expect(getSunBurstData('browse', dialogState)).rejects.toBe(error)
})

test('getSunBurstData logs and throws on failure', async () => {
  const error = new Error()
  const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
  mockedHandle.mockRejectedValueOnce(error)

  await expect(getSunBurstData('search', dialogState)).rejects.toBe(error)
  expect(consoleSpy).toHaveBeenCalledWith(
    expect.stringContaining('Failed to fetch /charts/sunbursts/search:')
  )
  consoleSpy.mockRestore()
})
