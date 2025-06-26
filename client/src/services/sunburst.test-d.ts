import { expectTypeOf } from 'vitest'
import { getSunBurstData } from '@/services/sunburst'
import type Plotly from 'plotly.js'

expectTypeOf(getSunBurstData).returns.resolves.toEqualTypeOf<Plotly.PlotData[]>()
