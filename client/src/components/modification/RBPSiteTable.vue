<script setup lang="ts">
import { ref, watch } from 'vue'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import { type Modification, getTargetSites } from '@/services/modification'
import { useDialogState } from '@/stores/DialogState'
import type { Bed6Record } from '@/utils/bed6'
import { trashRequestErrors } from '@/services/API'

const props = defineProps<{
  modification?: Modification
}>()
const dialogState = useDialogState()

interface DataItem extends Bed6Record {
  source: string
  target: string
  motif: string
  rbp: string
}

const dt = ref()
const records = ref<DataItem[]>([])

watch(
  () => props.modification,
  () => {
    if (props.modification) {
      getTargetSites(props.modification, 'RBP', dialogState)
        .then((data) => {
          records.value = data.map((x) => getDataItemFromBed6Record(x))
        })
        .catch((e) => {
          records.value = []
          trashRequestErrors(e)
        })
    } else {
      records.value = []
    }
  },
  { immediate: true }
)

function getDataItemFromBed6Record(x: Bed6Record): DataItem {
  const [source, target, rawMotif, rbp] = x.name.split(':')
  const motif = rawMotif.padStart(3, '0')
  const score = x.score / 1000
  return { ...x, score, source, target, motif, rbp }
}

// table-related utilities
const getFileName = () => {
  let stamp = new Date()
  return 'scimodom_binding_sites_' + stamp.toISOString().replace(/:/g, '')
}

const onExport = () => {
  dt.value.exportCSV()
}
</script>

<template>
  <DataTable :value="records" dataKey="id" ref="dt" :exportFilename="getFileName()" stripedRows>
    <template #header>
      <div style="text-align: right">
        <Button
          icon="pi pi-external-link"
          size="small"
          label="Export"
          severity="secondary"
          raised
          @click="onExport"
        />
      </div>
    </template>
    <template #empty>
      <p class="text-center text-secondary-500 font-semibold">
        No known RBP binding site affected by this modification!
      </p>
    </template>
    <Column field="rbp" header="RBP"></Column>
    <Column field="target" header="Target"></Column>
    <Column field="source" header="Source"></Column>
    <Column field="start" header="Start"></Column>
    <Column field="end" header="End"></Column>
    <Column field="score">
      <template #header>
        <span v-tooltip.top="'MSS score'">Score</span>
      </template>
    </Column>
    <Column field="strand" header="Strand"></Column>
  </DataTable>
</template>
