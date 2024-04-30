<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fmtOrder, fmtFilter } from '@/utils/index.js'
import { FilterMatchMode, FilterOperator } from 'primevue/api'
import {
  updModification,
  updOrganismFromMod,
  updTechnologyFromModAndOrg,
  updSelectionFromAll
} from '@/utils/selection.js'
import { HTTP } from '@/services/API.js'

const router = useRouter()

const options = ref()
const biotypes = ref()
const features = ref()

const modification = ref()
const selectedModification = ref()
const technology = ref()
const selectedTechnology = ref()
const organism = ref()
const selectedOrganism = ref()
const selection = ref()
const taxid = ref()
const chroms = ref()
const selectedChrom = ref()
const selectedChromStart = ref()
const selectedChromEnd = ref()

// new

const selectedBiotypes = ref()
const selectedFeatures = ref()
const selectedGene = ref()

const disabled = computed(() => isAllSelected())

const dt = ref()
const first = ref(0)
const rows = ref(10)
const records = ref()
const loading = ref(false)
const totalRecords = ref(0)

const lazyParams = ref({})

function isAllSelected() {
  return (
    selectedModification.value == null ||
    selectedTechnology.value == null ||
    selectedOrganism.value == null
  )
}

const clearCoords = () => {
  selectedChromStart.value = undefined
  selectedChromEnd.value = undefined
}

const getFileName = () => {
  let sep = '_&_'
  let fileName = 'scimodom_search'
  if (!(selectedModification.value == null || selectedOrganism.value == null)) {
    fileName =
      fileName +
      '_mod=' +
      selectedModification.value.label +
      sep +
      'taxid=' +
      taxid.value +
      sep +
      'tissue=' +
      selectedOrganism.value.label.replaceAll(/ /g, '_')
  }
  return fileName
}

const navigateTo = (eufid) => {
  router.push({ name: 'browse', params: { eufid: eufid } })
}

const onPage = (event) => {
  lazyParams.value = event
  if (!disabled.value) {
    lazyLoad(event)
  }
}

const onSort = (event) => {
  lazyParams.value = event
  if (!disabled.value) {
    lazyLoad(event)
  }
}

const onExport = () => {
  dt.value.exportCSV()
}

const updateOrganism = () => {
  selectedOrganism.value = undefined
  selectedTechnology.value = undefined
  selectedChrom.value = undefined
  selectedChromStart.value = undefined
  selectedChromEnd.value = undefined
  technology.value = undefined
  selection.value = undefined
  records.value = undefined
  organism.value = updOrganismFromMod(options.value, selectedModification.value)
}

const updateTechnology = () => {
  selectedTechnology.value = undefined
  selectedChrom.value = undefined
  selectedChromStart.value = undefined
  selectedChromEnd.value = undefined
  selection.value = undefined
  records.value = undefined
  technology.value = updTechnologyFromModAndOrg(
    options.value,
    selectedModification.value,
    selectedOrganism.value
  )
}

const updateSelection = () => {
  selectedChrom.value = undefined
  selectedChromStart.value = undefined
  selectedChromEnd.value = undefined
  records.value = undefined
  let result = updSelectionFromAll(
    options.value,
    selectedModification.value,
    selectedOrganism.value,
    selectedTechnology.value
  )
  taxid.value = result.taxid[0]
  selection.value = result.selection
  if (selection.value.length == 0) {
    // handle the case where all checkboxes are unticked
    selectedTechnology.value = undefined
    selection.value = undefined
    chroms.value = undefined
  } else {
    // get chrom.sizes
    HTTP.get(`/chrom/${taxid.value}`)
      .then(function (response) {
        chroms.value = response.data
      })
      .catch((error) => {
        console.log(error)
      })
  }
}

function lazyLoad(event) {
  loading.value = true
  lazyParams.value = { ...lazyParams.value, first: event?.first || first.value }
  // reformat filters for gene, biotypes and features as PV table filters
  let filters = {
    gene_name: {
      value: selectedGene.value == undefined ? null : selectedGene.value,
      matchMode: 'startsWith'
    },
    gene_biotype: {
      value: selectedBiotypes.value == undefined ? null : selectedBiotypes.value,
      matchMode: 'in'
    },
    feature: {
      value: selectedFeatures.value == undefined ? null : selectedFeatures.value,
      matchMode: 'in'
    }
  }
  HTTP.get('/search', {
    params: {
      selection: selection.value,
      taxid: taxid.value,
      geneFilter: fmtFilter(filters),
      chrom: selectedChrom.value == null ? null : selectedChrom.value.chrom,
      chromStart: selectedChromStart.value == null ? 0 : selectedChromStart.value,
      chromEnd:
        selectedChromEnd.value == null
          ? selectedChrom.value == null
            ? null
            : selectedChrom.value.size
          : selectedChromEnd.value,
      firstRecord: lazyParams.value.first,
      maxRecords: lazyParams.value.rows,
      multiSort: fmtOrder(lazyParams.value.multiSortMeta)
    },
    paramsSerializer: {
      indexes: null
    }
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

onMounted(() => {
  lazyParams.value = {
    first: first.value,
    rows: rows.value
  }
  HTTP.get('/selection')
    .then(function (response) {
      options.value = response.data
      modification.value = updModification(options.value)
    })
    .catch((error) => {
      console.log(error)
    })
  HTTP.get('/features_biotypes')
    .then(function (response) {
      biotypes.value = response.data.biotypes
      features.value = response.data.features
    })
    .catch((error) => {
      console.log(error)
    })
})
</script>

<template>
  <DefaultLayout>
    <!-- SECTION -->
    <SectionLayout>
      <h1
        class="font-ham mb-4 text-3xl font-extrabold text-gray-900 dark:text-white/80 md:text-5xl lg:text-6xl"
      >
        <span
          class="text-transparent bg-clip-text bg-gradient-to-r from-gg-2 from-10% via-gg-1 via-40% via-gb-2 via-60% to-gb-4 to-100"
        >
          Search
        </span>
        RNA modifications
      </h1>
      <p class="text-lg font-normal text-gray-500 dark:text-surface-400 lg:text-xl">
        Select filters and query the database
      </p>
      <!-- FILTER 1 -->
      <Divider />
      <!-- <div class="flex flex-row flex-wrap justify-start place-items-center [&>*]:mr-6"> -->
      <div class="grid grid-cols-1 md:grid-cols-10 gap-6">
        <div class="col-span-3">
          <Dropdown
            @change="updateOrganism()"
            v-model="selectedModification"
            :options="modification"
            optionLabel="label"
            optionGroupLabel="label"
            optionGroupChildren="children"
            placeholder="1. Select RNA modification"
            :pt="{
              root: { class: 'w-full md:w-full' }
            }"
            :ptOptions="{ mergeProps: true }"
          />
        </div>
        <div class="col-span-3">
          <CascadeSelect
            @change="updateTechnology()"
            v-model="selectedOrganism"
            :options="organism"
            optionLabel="label"
            optionGroupLabel="label"
            :optionGroupChildren="['child1', 'child2']"
            placeholder="2. Select organism"
            :pt="{
              root: { class: 'w-full md:w-full' }
            }"
            :ptOptions="{ mergeProps: true }"
          />
        </div>
        <div class="col-span-3">
          <TreeSelect
            @change="updateSelection()"
            v-model="selectedTechnology"
            :options="technology"
            selectionMode="checkbox"
            :metaKeySelection="false"
            placeholder="3. Select technology"
            :pt="{
              root: { class: 'w-full md:w-full' }
            }"
            :ptOptions="{ mergeProps: true }"
          />
        </div>
        <div></div>
      </div>
      <!-- FILTER 2 -->
      <!-- <Divider /> -->
      <div class="grid grid-cols-1 md:grid-cols-10 gap-6 mt-6">
        <div class="col-span-3">
          <InputText
            v-model="selectedGene"
            type="text"
            placeholder="4. Select gene (optional)"
            :disabled="disabled"
            :pt="{
              root: { class: 'w-full md:w-full' }
            }"
            :ptOptions="{ mergeProps: true }"
          />
        </div>
        <div class="col-span-3">
          <MultiSelect
            v-model="selectedBiotypes"
            :options="biotypes"
            placeholder="5. Select biotype (optional)"
            :maxSelectedLabels="3"
            :disabled="disabled"
            :pt="{
              root: { class: 'w-full md:w-full' }
            }"
            :ptOptions="{ mergeProps: true }"
          >
          </MultiSelect>
        </div>
        <div class="col-span-3">
          <MultiSelect
            v-model="selectedFeatures"
            :options="features"
            placeholder="6. Select feature (optional)"
            :maxSelectedLabels="3"
            :disabled="disabled"
            :pt="{
              root: { class: 'w-full md:w-full' }
            }"
            :ptOptions="{ mergeProps: true }"
          >
          </MultiSelect>
        </div>
        <div></div>
      </div>
      <!-- FILTER 3 -->
      <!-- <Divider /> -->
      <div class="grid grid-cols-1 md:grid-cols-10 gap-6 mt-6">
        <div class="col-span-3">
          <Dropdown
            @change="clearCoords()"
            v-model="selectedChrom"
            :options="chroms"
            optionLabel="chrom"
            showClear
            :disabled="disabled"
            placeholder="7. Select chromosome (optional)"
            :pt="{
              root: { class: 'w-full md:w-full' }
            }"
            :ptOptions="{ mergeProps: true }"
          />
        </div>
        <div class="col-span-3">
          <InputNumber
            @input="selectedChromEnd = null"
            v-model="selectedChromStart"
            inputId="minmax"
            placeholder="8. Enter region start (optional)"
            :disabled="selectedChrom == null"
            :min="0"
            :max="selectedChrom == null ? 0 : selectedChrom.size - 1"
            :pt="{
              root: { class: 'w-full md:w-full' }
            }"
            :ptOptions="{ mergeProps: true }"
          />
        </div>
        <div class="col-span-3">
          <InputNumber
            v-model="selectedChromEnd"
            inputId="minmax"
            :disabled="selectedChromStart == null"
            placeholder="9. Enter region end (optional)"
            :min="selectedChromStart == null ? 0 : selectedChromStart + 1"
            :max="selectedChrom == null ? 0 : selectedChrom.size"
            :pt="{
              root: { class: 'w-full md:w-full' }
            }"
            :ptOptions="{ mergeProps: true }"
          />
        </div>
        <div class="place-self-end">
          <Button
            type="button"
            size="small"
            icon="pi pi-sync"
            label="Query"
            :disabled="disabled"
            :loading="loading"
            @click="lazyLoad()"
          />
        </div>
      </div>
    </SectionLayout>
    <!-- SECTION -->
    <SectionLayout>
      <!-- TABLE -->
      <div>
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
                :disabled="disabled"
              />
            </div>
          </template>
          <!-- <template #empty> <p class="dark:text-white/80 font-semibold">No records found matching search criteria!</p> </template> -->
          <template #loading>
            <ProgressSpinner style="width: 60px; height: 60px" strokeWidth="6" />
          </template>
          <Column field="chrom" header="Chrom" sortable exportHeader="chrom"></Column>
          <Column field="start" header="Start" sortable exportHeader="chromStart"></Column>
          <Column field="end" header="End" exportHeader="chromEnd"></Column>
          <Column field="name" header="Name" exportHeader="name"></Column>
          <Column field="score" header="Score" sortable exportHeader="score"></Column>
          <Column field="strand" header="Strand" exportHeader="strand"></Column>
          <Column field="coverage" header="Coverage" sortable exportHeader="coverage"></Column>
          <Column field="frequency" header="Frequency" sortable exportHeader="frequency"></Column>
          <Column field="feature" header="Feature" exportHeader="feature"></Column>
          <Column field="gene_biotype" header="Biotype" exportHeader="biotype"></Column>
          <Column field="gene_name" header="Gene" exportHeader="geneName"></Column>
          <Column field="tech" header="Technology" exportHeader="technology"></Column>
          <Column field="dataset_id" header="EUFID" exportHeader="eufid">
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
        </DataTable>
      </div>
    </SectionLayout>
  </DefaultLayout>
</template>

<style scoped></style>
