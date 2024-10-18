<script setup lang="ts">
import type { ComparisonDisplayRecord } from '@/utils/comparison'
import { ref } from 'vue'

const COLUMNS = [
  { field: 'a.chrom', header: 'Chrom', exportHeader: 'chrom_ref', sortable: true, tooltip: '' },
  {
    field: 'a.start',
    header: 'Start',
    exportHeader: 'chromStart_ref',
    sortable: true,
    tooltip: ''
  },
  {
    field: 'a.end',
    header: 'End',
    exportHeader: 'chromEnd_ref',
    sortable: false,
    tooltip: 'Open (end excluded)'
  },
  { field: 'a.name', header: 'Name', exportHeader: 'name_ref', sortable: false, tooltip: '' },
  {
    field: 'a.score',
    header: 'Score',
    exportHeader: 'score_ref',
    sortable: true,
    tooltip: '-log10(p) or 0 if undefined'
  },
  { field: 'a.strand', header: 'Strand', exportHeader: 'strand_ref', sortable: false, tooltip: '' },
  {
    field: 'a.eufid',
    header: 'EUFID',
    exportHeader: 'EUFID_ref',
    sortable: false,
    tooltip: 'Dataset ID'
  },
  {
    field: 'a.coverage',
    header: 'Coverage',
    exportHeader: 'coverage_ref',
    sortable: true,
    tooltip: '0 if not available'
  },
  {
    field: 'a.frequency',
    header: 'Frequency',
    exportHeader: 'frequency_ref',
    sortable: true,
    tooltip: 'Modification stoichiometry'
  },
  { field: 'b.chrom', header: 'Chrom', exportHeader: 'chrom', sortable: true, tooltip: '' },
  { field: 'b.start', header: 'Start', exportHeader: 'chromStart', sortable: true, tooltip: '' },
  {
    field: 'b.end',
    header: 'End',
    exportHeader: 'chromEnd',
    sortable: false,
    tooltip: 'Open (end excluded)'
  },
  { field: 'b.name', header: 'Name', exportHeader: 'name', sortable: false, tooltip: '' },
  {
    field: 'b.score',
    header: 'Score',
    exportHeader: 'score',
    sortable: true,
    tooltip: '-log10(p) or 0 if undefined'
  },
  { field: 'b.strand', header: 'Strand', exportHeader: 'strand', sortable: false, tooltip: '' },
  {
    field: 'b.eufid',
    header: 'EUFID',
    exportHeader: 'EUFID',
    sortable: false,
    tooltip: 'Dataset ID or upload'
  },
  {
    field: 'b.coverage',
    header: 'Coverage',
    exportHeader: 'coverage',
    sortable: true,
    tooltip: '0 if not available'
  },
  {
    field: 'b.frequency',
    header: 'Frequency',
    exportHeader: 'frequency',
    sortable: true,
    tooltip: 'Modification stoichiometry or 1 for BED6'
  },
  {
    field: 'distance',
    header: 'Distance',
    exportHeader: 'Distance',
    sortable: false,
    tooltip: 'Distance to closest feature'
  }
]

const model = defineModel<ComparisonDisplayRecord[]>('records')
const loading = defineModel<boolean>('loading')

const dt = ref()

function getFileName() {
  let stamp = new Date()
  return 'scimodom_compare_' + stamp.toISOString().replace(/:/g, '')
}

const onExport = () => {
  dt.value.exportCSV()
}

// https://github.com/primefaces/primevue-tailwind/issues/168
const tablePt = {
  virtualScrollerSpacer: {
    class: 'flex'
  }
}

const ColumnStyle = 'w-{1/19}'
</script>
<template>
  <DataTable
    :value="model"
    ref="dt"
    :exportFilename="getFileName()"
    sortMode="multiple"
    removableSort
    scrollable
    scrollHeight="400px"
    :virtualScrollerOptions="{ itemSize: 46 }"
    tableStyle="min-w-{50rem}"
    :loading="loading"
    :pt="tablePt"
  >
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
    <template #loading>
      <ProgressSpinner style="width: 60px; height: 60px" strokeWidth="6" />
    </template>
    <template #empty>
      <p class="text-center text-secondary-500 font-semibold">
        No records match your search criteria!
      </p>
    </template>
    <ColumnGroup type="header">
      <Row>
        <Column header="Reference dataset(s)" :colspan="9" />
        <Column header="Comparison dataset(s)" :colspan="10" />
      </Row>
      <Row>
        <Column
          v-for="col of COLUMNS"
          :key="col.field"
          :field="col.field"
          :sortable="col.sortable"
          :style="ColumnStyle"
        >
          <template #header>
            <span v-tooltip.top="col.tooltip">{{ col.header }}</span>
          </template>
        </Column>
      </Row>
    </ColumnGroup>
    <Column
      v-for="col of COLUMNS"
      :key="col.field"
      :field="col.field"
      :exportHeader="col.exportHeader"
      :style="ColumnStyle"
    >
    </Column>
  </DataTable>
</template>
