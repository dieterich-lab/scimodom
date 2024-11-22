<script setup lang="ts">
import { onMounted, useTemplateRef } from 'vue'
import { getSunBurstData, type SunburstType } from '@/services/sunburst'
import { COLORS } from '@/utils/color'
import { useDialogState } from '@/stores/DialogState'
import Plotly from 'plotly.js'
import { trashRequestErrors } from '@/services/API'

const LAYOUT = {
  margin: { t: 0, l: 0, r: 0, b: 0 },
  sunburstcolorway: COLORS,
  extendsunburstcolorway: true
}

const props = defineProps<{
  type: SunburstType
}>()

const dialogStore = useDialogState()
const chart = useTemplateRef<Plotly.Root>('chart_ref')

function handleClick() {
  if (chart.value) {
    Plotly.restyle(chart.value, {})
  }
}

onMounted(() => {
  getSunBurstData(props.type, dialogStore)
    .then((new_data) => {
      if (chart.value) {
        Plotly.newPlot(chart.value, new_data, LAYOUT).then((x) => {
          x.on('plotly_click', handleClick)
        })
      }
    })
    .catch((e) => trashRequestErrors(e))
})
</script>

<template>
  <div ref="chart_ref" />
</template>
