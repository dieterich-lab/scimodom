import Plotly from 'plotly.js'
import { handleRequestWithErrorReporting, HTTP } from '@/services/API'
import { ColorFactory } from '@/utils/color'
import { type DialogStateStore } from '@/stores/DialogState'

type SunburstType = 'search' | 'browse'

interface SunburstData extends Omit<Partial<Plotly.PieData>, 'type'> {
  // There should be a better solution ...
  type: 'sunburst'
  parents: string[]
}

interface PrefilledSunburstData {
  ids: Plotly.PlotData['ids']
  labels: Plotly.PlotData['labels']
  parents: Plotly.PlotData['parents']
  values: Plotly.PlotData['values']
  marker: { colors: Plotly.Color[] }
  textfont: { color: Array<string> }
  customdata: Array<number>
}

interface SunburstResponseData {
  name: string
  children: SunburstResponseData[] | SunburstLeafNode[]
  cumulativeSize?: number
}

interface SunburstLeafNode {
  name: string
  size: number
}

function isLeafNode(x: SunburstResponseData | SunburstLeafNode): x is SunburstLeafNode {
  return Object.prototype.hasOwnProperty.call(x, 'size')
}

async function getSunBurstData(
  type: SunburstType,
  dialogState: DialogStateStore
): Promise<Plotly.PlotData[]> {
  try {
    const data = await handleRequestWithErrorReporting<SunburstResponseData[]>(
      HTTP.get(`/sunburst/${type}`),
      `Failed to load Sunburst data, type ${type}`,
      dialogState
    )
    calculateCumulativeSize(data[0])
    return [getPlotlySunburstData(data[0]) as Plotly.PlotData]
  } catch (err) {
    console.log(`Failed to fetch sunburst/${type} data: ${err}`)
    throw err
  }
}

function calculateCumulativeSize(node: SunburstResponseData | SunburstLeafNode): number {
  if (isLeafNode(node)) {
    return node.size
  } else {
    node.cumulativeSize = node.children.reduce(
      (accumulator, currentValue) => accumulator + calculateCumulativeSize(currentValue),
      0
    )
    return node.cumulativeSize
  }
}

function getPlotlySunburstData(node: SunburstResponseData): SunburstData {
  const sunburst: SunburstData & PrefilledSunburstData = {
    type: 'sunburst',
    ids: [],
    labels: [],
    parents: [],
    values: [],
    marker: { colors: [], line: { width: 1 } },
    textfont: { color: [], family: '"Open Sans", verdana, arial, sans-serif', size: 12 }, // Set the text color for each label.
    customdata: [],
    hovertemplate: '<b>%{label}</b> : %{customdata}<extra></extra>',
    textinfo: 'label'
    // Does not seem to exist: insidetextorientation: 'horizontal'
  }
  const colorFactory = new ColorFactory()
  collectedDataFromNodes(node, sunburst, colorFactory)

  return sunburst
}

function collectedDataFromNodes(
  node: SunburstResponseData | SunburstLeafNode,
  sunburst: SunburstData & PrefilledSunburstData,
  colorFactory: ColorFactory,
  depth: number = 0,
  parent: string = '',
  parentColor: string = ''
) {
  const id = parent ? `${parent}-${node.name}` : node.name
  const value = isLeafNode(node) ? node.size : 0
  const customData = isLeafNode(node) ? node.size : node.cumulativeSize || 0
  const color = colorFactory.getColor(depth, parentColor)
  const textColor = colorFactory.getTextColor(depth)

  sunburst.ids.push(id)
  sunburst.labels.push(node.name)
  sunburst.parents.push(parent)
  sunburst.values.push(value)
  sunburst.customdata.push(customData)
  sunburst.marker.colors.push(color)
  sunburst.textfont.color.push(textColor)
  if (!isLeafNode(node)) {
    for (const child of node.children) {
      collectedDataFromNodes(child, sunburst, colorFactory, depth + 1, id, color)
    }
  }
}

export { type SunburstType, getSunBurstData }
