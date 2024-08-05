<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { HTTP } from '@/services/API.js'
import { fmtOrder } from '@/utils/index.js'

const props = defineProps({
  coords: {
    type: Object,
    required: true
  }
})

const router = useRouter()

const dt = ref()
const first = ref(0)
const rows = ref(10)
const records = ref()
const loading = ref(false)
const totalRecords = ref(0)
const lazyParams = ref({
  first: first.value,
  rows: rows.value
})

watch(
  () => props.coords,
  () => {
    lazyLoad()
  },
  { immediate: true }
)

// table-related utilities
const getFileName = () => {
  let stamp = new Date()
  return 'scimodom_per_site_' + stamp.toISOString().replaceAll(/:/g, '')
}

const onPage = (event) => {
  lazyParams.value = event
  lazyLoad(event)
}

const onSort = (event) => {
  lazyParams.value = event
  lazyLoad(event)
}

const onExport = () => {
  dt.value.exportCSV()
}

const navigateTo = (eufid) => {
  router.push({ name: 'browse', params: { eufid: eufid } })
}

function lazyLoad(event) {
  loading.value = true
  lazyParams.value = { ...lazyParams.value, first: event?.first || first.value }
  HTTP.get('/modification/sitewise', {
    params: {
      taxaId: props.coords.taxa_id,
      chrom: props.coords.chrom,
      start: props.coords.start,
      end: props.coords.end,
      firstRecord: lazyParams.value.first,
      maxRecords: lazyParams.value.rows,
      multiSort: fmtOrder(lazyParams.value.multiSortMeta)
    },
    paramsSerializer: {
      indexes: null
    }
  })
    .then(function (response) {
      records.value = response.data.records.filter(
        (record) =>
          record.dataset_id != props.coords.dataset_id &&
          record.modification_id != props.coords.modification_id
      )
      totalRecords.value = records.value.length
      loading.value = false
    })
    .catch((error) => {
      console.log(error)
    })
}
</script>

<template>
  <DataTable
    :value="records"
    dataKey="id"
    ref="dt"
    :exportFilename="getFileName()"
    lazy
    paginator
    :totalRecords="totalRecords"
    :loading="loading"
    :first="first"
    :rows="rows"
    @page="onPage($event)"
    @sort="onSort($event)"
    removableSort
    sortMode="multiple"
    stripedRows
  >
    <template #header>
      <div style="text-align: right">
        <Button
          icon="pi pi-external-link"
          size="small"
          label="Export"
          severity="secondary"
          raised
          @click="onExport($event)"
        />
      </div>
    </template>
    <template #loading>
      <ProgressSpinner style="width: 60px; height: 60px" strokeWidth="6" />
    </template>
    <template #empty>
      <p class="text-center text-secondary-500 font-semibold">
        This modification site is not reported in other datasets!
      </p>
    </template>
    <Column field="dataset_id" header="EUFID" exportHeader="EUFID">
      <template #body="{ data }">
        <Button
          size="small"
          :label="data.dataset_id"
          severity="secondary"
          text
          @click="navigateTo(data.dataset_id)"
        />
      </template>
    </Column>
    <Column field="rna" header="RNA"></Column>
    <Column field="name" header="Name" exportHeader="name">
      <template #body="{ data }">
        <a
          class="text-primary-500 hover:text-secondary-500"
          :href="'https://www.genesilico.pl/modomics/modifications/' + data.reference_id"
          target="_blank"
          rel="noopener noreferrer"
          >{{ data.name }}
        </a>
      </template>
    </Column>
    <Column field="short_name" header="Organism"></Column>
    <Column field="cto" header="Cell/Tissue"></Column>
    <Column field="tech" header="Technology"></Column>
    <Column field="chrom" exportHeader="chrom" style="display: none"></Column>
    <Column field="start" exportHeader="chromStart" style="display: none"></Column>
    <Column field="end" exportHeader="chromEnd" style="display: none"></Column>
    <Column field="strand" exportHeader="strand" style="display: none"></Column>
    <Column field="score" header="Score" sortable exportHeader="score"></Column>
    <Column field="coverage" header="Coverage" sortable exportHeader="coverage"></Column>
    <Column field="frequency" header="Frequency" sortable exportHeader="frequency"></Column>
  </DataTable>
</template>
