<script setup lang="ts">
import { ref, watch } from 'vue'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import { getTargetSites, type Modification } from '@/services/modification'
import type { Bed6Record, Strand } from '@/utils/bed6'
import { useDialogState } from '@/stores/DialogState'
import { trashRequestErrors } from '@/services/API'

interface TableItem {
  chrom: string
  start: number
  end: number
  strand: Strand
  score: number
  source: string
  target: string
  mirna: string
}

const props = defineProps<{
  modification?: Modification
}>()

const dt = ref()
const records = ref<TableItem[]>([])
const dialogState = useDialogState()

watch(
  () => props.modification,
  () => {
    if (props.modification) {
      getTargetSites(props.modification, 'MIRNA', dialogState)
        .then((data) => {
          records.value = data.map((x) => getTableItemFromBed6Record(x))
        })
        .catch((e) => trashRequestErrors(e))
    } else {
      records.value = []
    }
  },
  { immediate: true }
)

function getTableItemFromBed6Record(x: Bed6Record): TableItem {
  let [source, target, mirna] = x.name.split(':')
  return { ...x, source, target, mirna }
}

// table-related utilities
const getFileName = () => {
  let stamp = new Date()
  return 'scimodom_mirna_targets_' + stamp.toISOString().replace(/:/g, '')
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
          @click="onExport()"
        />
      </div>
    </template>
    <template #empty>
      <p class="text-center text-secondary-500 font-semibold">
        No known miRNA target site affected by this modification!
      </p>
    </template>
    <Column field="mirna" header="miRNA"></Column>
    <Column field="target" header="Target"></Column>
    <Column field="source" header="Source"></Column>
    <Column field="start" header="Start"></Column>
    <Column field="end" header="End"></Column>
    <Column field="score">
      <template #header>
        <span v-tooltip.top="'context++ score percentile'">Score</span>
      </template>
    </Column>
    <Column field="strand" header="Strand"></Column>
  </DataTable>
</template>
