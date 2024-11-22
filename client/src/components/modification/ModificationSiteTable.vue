<script setup lang="ts">
import { ref, watch } from 'vue'
import Button from 'primevue/button'
import ProgressSpinner from 'primevue/progressspinner'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import { useRouter } from 'vue-router'
import { getSiteWiseInfo, type Modification, type SiteWiseInfo } from '@/services/modification'
import { useDialogState } from '@/stores/DialogState'
import { trashRequestErrors } from '@/services/API'

const props = defineProps<{
  modification?: Modification
}>()
const dialogState = useDialogState()
const router = useRouter()

const dt = ref()
const records = ref<SiteWiseInfo[]>([])
const loading = ref<boolean>(false)

watch(
  () => props.modification,
  () => {
    if (props.modification) {
      const m = props.modification
      loading.value = true
      getSiteWiseInfo(m, dialogState)
        .then((x) => {
          records.value = x.filter((r) => r.dataset_id != m.dataset_id && r.modification_id != m.id)
        })
        .catch((e) => trashRequestErrors(e))
        .finally(() => {
          loading.value = false
        })
    }
  },
  { immediate: true }
)

// table-related utilities
const getFileName = () => {
  let stamp = new Date()
  return 'scimodom_per_site_' + stamp.toISOString().replace(/:/g, '')
}

const onExport = () => {
  dt.value.exportCSV()
}

const navigateTo = (eufid: string) => {
  const { href } = router.resolve({ name: 'browse', params: { eufid: eufid } })
  window.open(href, '_blank')
}
</script>

<template>
  <DataTable
    :value="records"
    dataKey="id"
    ref="dt"
    :exportFilename="getFileName()"
    paginator
    :loading="loading"
    :rows="5"
    removableSort
    sortMode="multiple"
    stripedRows
    paginatorTemplate="RowsPerPageDropdown FirstPageLink PrevPageLink CurrentPageReport NextPageLink LastPageLink"
    currentPageReportTemplate="{first} to {last} of {totalRecords}"
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
    <Column field="score" header="Score" :sortable="true" exportHeader="score"></Column>
    <Column field="coverage" header="Coverage" :sortable="true" exportHeader="coverage"></Column>
    <Column field="frequency" header="Frequency" :sortable="true" exportHeader="frequency"></Column>
  </DataTable>
</template>
