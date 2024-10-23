<script setup lang="ts">
import Plotly from 'plotly.js'
import { onMounted, useTemplateRef } from 'vue'
import { getSunBurstData, type SunburstType } from '@/services/sunburst'
import { COLORS } from '@/utils/color'
import { useDialogState } from '@/stores/DialogState'

const LAYOUT = {
  margin: { t: 0, l: 0, r: 0, b: 0 },
  sunburstcolorway: COLORS,
  extendsunburstcolorway: true
}

const props = defineProps<{
  type: SunburstType
}>()

const dialogStore = useDialogState()
const chart = useTemplateRef<HTMLDivElement>('chart')

onMounted(() => {
  getSunBurstData(props.type, dialogStore).then((data) => {
    if (chart.value) {
      Plotly.newPlot(chart.value, data, LAYOUT)
    }
  })
})
</script>

<template>
  <div ref="chart"></div>
</template>
