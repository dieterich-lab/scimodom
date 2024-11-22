<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import ProgressSpinner from 'primevue/progressspinner'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import ModificationInfo from '@/components/modification/ModificationInfo.vue'
import ChromRegionEnsemblLink from '@/components/search/ChromRegionEnsemblLink.vue'
import GeneEnsemblLink from '@/components/search/GeneEnsemblLink.vue'
import GenesilicoModificationLink from '@/components/search/GenesilicoModificationLink.vue'
import type { SearchParameters } from '@/utils/search'
import type { DataTablePageEvent, DataTableSortEvent, DataTableSortMeta } from 'primevue/datatable'
import {
  getModificationExportLink,
  getModifications,
  type Modification
} from '@/services/modification'
import { useDialogState } from '@/stores/DialogState'
import { trashRequestErrors } from '@/services/API'

const props = defineProps<{
  searchParameters: SearchParameters | null
}>()

const dialogState = useDialogState()

const dt = ref()
const showDetails = ref(false)
const selectedSite = ref<Modification>()
const totalRecords = ref(0)
const loading = ref(false)
const firstRecord = ref(0)
const maxRecords = ref(10)
const sortMetas = ref<DataTableSortMeta[]>()
const records = ref()

const router = useRouter()
const disableExportLink = computed(() => !props.searchParameters || loading.value)
const exportLink = computed(() =>
  props.searchParameters ? getModificationExportLink(props.searchParameters, sortMetas.value) : ''
)
const emptyMessage = computed(() =>
  props.searchParameters && !loading.value ? 'No records match your search criteria!' : ''
)

onMounted(() => loadData())

function loadData() {
  if (props.searchParameters) {
    loading.value = true
    getModifications(
      props.searchParameters,
      dialogState,
      firstRecord.value,
      maxRecords.value,
      sortMetas.value
    )
      .then((data) => {
        records.value = data.records
        totalRecords.value = data.totalRecords
      })
      .catch((e) => {
        records.value = undefined
        totalRecords.value = 0
        trashRequestErrors(e)
      })
      .finally(() => {
        loading.value = false
      })
  } else {
    records.value = undefined
    totalRecords.value = 0
  }
}

function onPageOrSort(event: DataTablePageEvent | DataTableSortEvent) {
  sortMetas.value = event.multiSortMeta
  firstRecord.value = event.first
  maxRecords.value = event.rows
  loadData()
}

function navigateTo(eufid: string) {
  const { href } = router.resolve({ name: 'browse', params: { initialSearchString: eufid } })
  window.open(href, '_blank')
}

function onOverlay(record: Modification) {
  selectedSite.value = { ...record }
  showDetails.value = true
}
</script>

<template>
  <DataTable
    :value="records"
    dataKey="id"
    ref="dt"
    lazy
    :paginator="true"
    :totalRecords="totalRecords"
    :loading="loading"
    :first="firstRecord"
    :rows="maxRecords"
    @page="onPageOrSort($event)"
    @sort="onPageOrSort($event)"
    removableSort
    sortMode="multiple"
    stripedRows
    paginatorTemplate="FirstPageLink PrevPageLink CurrentPageReport NextPageLink LastPageLink"
    currentPageReportTemplate="Showing {first} to {last} of {totalRecords} records"
  >
    <template #header>
      <div style="text-align: right" v-if="disableExportLink">
        <Button
          icon="pi pi-external-link"
          size="small"
          severity="secondary"
          raised
          label="Export"
          :disabled="true"
        />
      </div>
      <div style="text-align: right" v-else>
        <a :href="exportLink">
          <Button
            icon="pi pi-external-link"
            size="small"
            severity="secondary"
            raised
            label="Export"
            v-tooltip.top="'Export full table'"
          />
        </a>
      </div>
    </template>
    <template #empty>
      <p class="text-center text-secondary-500 font-semibold">
        {{ emptyMessage }}
      </p>
    </template>
    <template #loading>
      <ProgressSpinner style="width: 60px; height: 60px" strokeWidth="6" />
    </template>
    <Column field="chrom" header="Chrom" :sortable="true"></Column>
    <Column field="start" header="Start" :sortable="true">
      <template #body="{ data }">
        <ChromRegionEnsemblLink
          :taxa-name="searchParameters?.taxa.taxa_name || ''"
          :chrom="data.chrom"
          :start="data.start"
          :end="data.end"
        />
      </template>
    </Column>
    <Column field="end">
      <template #header>
        <span v-tooltip.top="'Open (end excluded)'">End</span>
      </template>
    </Column>
    <Column field="name" header="Name">
      <template #body="{ data }">
        <GenesilicoModificationLink :name="data.name" :reference-id="data.reference_id" />
      </template>
    </Column>
    <Column field="score" :sortable="true">
      <template #header>
        <span v-tooltip.top="'-log10(p) or 0 if undefined'">Score</span>
      </template>
    </Column>
    <Column field="strand" header="Strand"></Column>
    <Column field="coverage" :sortable="true">
      <template #header>
        <span v-tooltip.top="'0 if not available'">Coverage</span>
      </template>
    </Column>
    <Column field="frequency" :sortable="true">
      <template #header>
        <span v-tooltip.top="'Modification stoichiometry'">Frequency</span>
      </template>
    </Column>
    <Column field="dataset_id">
      <template #header>
        <span v-tooltip.top="'Dataset ID'">EUFID</span>
      </template>
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
    <Column field="tech" header="Technology"></Column>
    <Column field="feature" header="Feature"></Column>
    <Column field="gene_name" header="Gene">
      <template #body="{ data }">
        <GeneEnsemblLink
          :taxa-name="searchParameters?.taxa.taxa_name || ''"
          :gene-name="data.gene_name"
          :gene-id="data.gene_id"
        />
      </template>
    </Column>
    <Column field="gene_biotype" header="Biotype"></Column>
    <Column :exportable="false" style="width: 5%">
      <template #header>
        <span v-tooltip.top="'Click for site information'">Info</span>
      </template>
      <template #body="slotProps">
        <Button
          icon="pi pi-info"
          outlined
          rounded
          severity="secondary"
          @click="onOverlay(slotProps.data)"
        />
      </template>
    </Column>
  </DataTable>
  <ModificationInfo
    v-model:visible="showDetails"
    :modification="selectedSite"
    :key="selectedSite?.id"
  />
</template>
