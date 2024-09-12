<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import ModificationInfo from '@/components/modification/ModificationInfo.vue'
import { getApiUrl, HTTP } from '@/services/API'
import { fmtFilter, fmtOrder } from '@/utils'
import ChromRegionEnsemblLink from '@/components/search/ChromRegionEnsemblLink.vue'
import GenesilicoModificationLink from '@/components/search/GenesilicoModificationLink.vue'

const props = defineProps({
  searchParameters: { type: Object },
  taxaName: { type: String },
  disabled: { type: Boolean }
})
/*
  searchParameters look like this

  modification: int - modification ID,
  organism: int - organism ID,
  technology: int[] - technology IDs,
  rnaType: ?,
  taxaId: int | null,
  taxaName: str | null,
  chrom: str | null
  chromStart: int | null
  chromEnd: int | null,
  geneName: ? | null,
  geneBiotype: ? | null,
  feature: ? | null,

  We really need to move to TypeScript ...

*/

const dt = ref()
const showDetails = ref(false)
const selectedSite = ref({})
const totalRecords = ref(0)
const loading = ref(false)
const firstRecord = ref(0)
const maxRecords = ref(10)
const multiSortMeta = ref()
const records = ref()

const router = useRouter()
const disableExportLink = computed(() => props.disabled || loading.value)
const exportLink = computed(() => getExportLink())

onMounted(() => loadData())

function onPageOrSort(event) {
  multiSortMeta.value = event.multiSortMeta
  firstRecord.value = event.first
  maxRecords.value = event.rows
  loadData()
}

function navigateTo(eufid) {
  const { href } = router.resolve({ name: 'browse', params: { eufid: eufid } })
  window.open(href, '_blank')
}

function onOverlay(record) {
  selectedSite.value = { ...record }
  showDetails.value = true
}

function loadData() {
  if (props.disabled) {
    return
  }
  loading.value = true
  const params = getQueryParams(firstRecord.value, maxRecords.value)
  HTTP.get('/modification/', {
    params: params,
    paramsSerializer: { indexes: null }
  })
    .then(function (response) {
      records.value = response.data.records
      totalRecords.value = response.data.totalRecords
      loading.value = false
    })
    .catch((error) => {
      console.log(error)
    })
}

function getQueryParams(myFirstRecord = null, myMaxRecords = null) {
  const p = props.searchParameters
  // reformat filters for gene, biotypes and features as PV table filters
  const filters = {
    // matchMode is actually hard coded to "equal" in the BE; forceSelection is toggled
    gene_name: { value: p.geneName, matchMode: 'startsWith' },
    gene_biotype: { value: p.geneBiotype, matchMode: 'in' },
    feature: { value: p.feature, matchMode: 'in' }
  }
  return {
    modification: p.modification,
    organism: p.organism,
    technology: p.technology,
    rnaType: p.rnaType,
    taxaId: p.taxaId,
    geneFilter: fmtFilter(filters),
    chrom: p.chrom,
    chromStart: p.chromStart,
    chromEnd: p.chromEnd,
    firstRecord: myFirstRecord,
    maxRecords: myMaxRecords,
    multiSort: fmtOrder(multiSortMeta.value)
  }
}

function getExportLink() {
  if (disableExportLink.value) {
    return ''
  }
  const rawParams = getQueryParams()
  const url = new URL(getApiUrl('modification/csv'))
  for (const [k, v] of Object.entries(rawParams)) {
    if (v != null) {
      if (Array.isArray(v)) {
        v.forEach((x) => url.searchParams.append(k, x))
      } else {
        url.searchParams.append(k, v)
      }
    }
  }
  return url.toString()
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
        No records match your search criteria!
      </p>
    </template>
    <template #loading>
      <ProgressSpinner style="width: 60px; height: 60px" strokeWidth="6" />
    </template>
    <Column field="chrom" header="Chrom" sortable></Column>
    <Column field="start" header="Start" sortable>
      <template #body="{ data }">
        <ChromRegionEnsemblLink
          :taxa-name="taxaName"
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
    <Column field="score" sortable>
      <template #header>
        <span v-tooltip.top="'-log10(p) or 0 if undefined'">Score</span>
      </template>
    </Column>
    <Column field="strand" header="Strand"></Column>
    <Column field="coverage" sortable>
      <template #header>
        <span v-tooltip.top="'0 if not available'">Coverage</span>
      </template>
    </Column>
    <Column field="frequency" sortable>
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
    <Column field="gene_name" header="Gene"></Column>
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
  <ModificationInfo v-model:visible="showDetails" :site="selectedSite" />
</template>
