<script setup>
import { ref, computed, onMounted } from 'vue'
import { toIds, fmtOrder, fmtFilter } from '@/utils/index.js'
import { FilterMatchMode, FilterOperator } from 'primevue/api'
import {
  updModification,
  updOrganismFromMod,
  updTechnologyFromModAndOrg,
  updSelectionFromAll
} from '@/utils/selection.js'
import service from '@/services/index.js'

const options = ref()
const biotypes = ref()
const features = ref()
const names = ref()
const modification = ref()
const selectedModification = ref()
const technology = ref()
const selectedTechnology = ref()
const organism = ref()
const selectedOrganism = ref()
const taxid = ref()
const selection = ref()

const chroms = ref()
const selectedChrom = ref()
const selectedChromStart = ref()
const selectedChromEnd = ref()

const disabled = computed(() => isAllSelected())

const dt = ref()
const first = ref(0)
const records = ref()
const loading = ref(false)
const loadingButton = ref(false)
const totalRecords = ref(0)
const lazyParams = ref({})
const filters = ref({
  gene_name: { value: null, matchMode: FilterMatchMode.STARTS_WITH },
  gene_biotype: { value: null, matchMode: FilterMatchMode.IN },
  feature: { value: null, matchMode: FilterMatchMode.IN }
  // name: { value: null, matchMode: FilterMatchMode.IN }
  // name: { value: null, matchMode: 'in' }
  // name: {
  //   operator: FilterOperator.AND,
  //   constraints: [{ value: null, matchMode: FilterMatchMode.IN }]
  // },
})

const submitQuery = () => {
  loadingButton.value = true
  lazyLoad()
  loadingButton.value = false
  // setTimeout(() => {
  //     loadingButton.value = false
  // }, 2500)
}

function isAllSelected() {
  return (
    Object.is(selectedModification.value, undefined) ||
    Object.is(selectedTechnology.value, undefined) ||
    Object.is(selectedOrganism.value, undefined)
  )
}

const onPage = (event) => {
  lazyParams.value = event
  lazyLoad(event)
}

const onSort = (event) => {
  lazyParams.value = event
  lazyLoad(event)
}

const onFilter = (event) => {
  lazyParams.value.filters = filters.value
  // console.log('FILTER:', lazyParams.value.filters)
  // console.log('FILTER NAME:', lazyParams.value.filters['gene_name_gc'])
  // console.log('FILTER BIOTYPE:', lazyParams.value.filters['gene_biotype_gc'])
  // console.log('FILTER FEATURE:', lazyParams.value.filters['feature_gc'])
  console.log('FILTER:', lazyParams.value.filters)
  console.log('FMT FILTER:', fmtFilter(lazyParams.value.filters))
  lazyLoad(event)
}

const onExport = () => {
  dt.value.exportCSV()
}

const updateOrganism = () => {
  selectedOrganism.value = undefined
  selectedTechnology.value = undefined
  technology.value = undefined
  selection.value = undefined
  organism.value = updOrganismFromMod(options.value, selectedModification.value)
}

const updateTechnology = () => {
  selectedTechnology.value = undefined
  selection.value = undefined
  technology.value = updTechnologyFromModAndOrg(
    options.value,
    selectedModification.value,
    selectedOrganism.value
  )
}

const updateSelection = () => {
  let result = updSelectionFromAll(
    options.value,
    selectedModification.value,
    selectedOrganism.value,
    selectedTechnology.value
  )
  taxid.value = result.taxid
  selection.value = result.selection
  // get chrom.sizes
  service
    .getEndpoint(`/chrom/${taxid.value}`)
    .then(function (response) {
      chroms.value = response.data
    })
    .catch((error) => {
      console.log(error)
    })
}

const updateTmp = () => {
  // lazyLoad()
}

function lazyLoad(event) {
  loading.value = true
  lazyParams.value = { ...lazyParams.value, first: event?.first || first.value }
  // console.log("FIRST", lazyParams.value.first)
  // console.log("ROWS", lazyParams.value.rows)
  service
    .get('/search', {
      params: {
        selection: selection.value,
        taxid: taxid.value[0],
        chrom: selectedChrom.value == null ? null : selectedChrom.value.chrom,
        start: selectedChromStart.value == null ? 0 : selectedChromStart.value,
        end:
          selectedChromEnd.value == null
            ? selectedChrom.value == null
              ? 0
              : selectedChrom.value.size
            : selectedChromEnd.value,
        firstRecord: lazyParams.value.first,
        maxRecords: lazyParams.value.rows,
        multiSort: fmtOrder(lazyParams.value.multiSortMeta),
        tableFilter: fmtFilter(lazyParams.value.filters)
      },
      paramsSerializer: {
        indexes: null
      }
    })
    .then(function (response) {
      records.value = response.data.records
      totalRecords.value = response.data.totalRecords
      biotypes.value = response.data.biotypes
      features.value = response.data.features
      // names.value = [...new Set(records.value.map(item => item.name))]
    })
    .catch((error) => {
      console.log(error)
    })
  loading.value = false
}

onMounted(() => {
  lazyParams.value = {
    first: 0,
    rows: 10,
    filters: filters.value
  }
  // lazyLoad()
  service
    .getEndpoint('/selection')
    .then(function (response) {
      options.value = response.data
      modification.value = updModification(options.value)
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
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
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
        <div>
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
        <div>
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
      </div>
      <!-- FILTER 2 -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
        <div>
          <Dropdown
            @change="
              selectedChromStart = null
              selectedChromEnd = null
            "
            v-model="selectedChrom"
            :options="chroms"
            optionLabel="chrom"
            showClear
            :disabled="disabled"
            placeholder="4. Select chromosome (optional)"
            :pt="{
              root: { class: 'w-full md:w-full' }
            }"
            :ptOptions="{ mergeProps: true }"
          />
        </div>
        <InputNumber
          @input="selectedChromEnd = null"
          v-model="selectedChromStart"
          inputId="minmax"
          placeholder="5. Enter region start (optional)"
          :disabled="selectedChrom == null"
          :min="0"
          :max="selectedChrom == null ? 0 : selectedChrom.size - 1"
          :pt="{
            root: { class: 'w-full md:w-full' }
          }"
          :ptOptions="{ mergeProps: true }"
        />
        <div>
          <InputNumber
            v-model="selectedChromEnd"
            inputId="minmax"
            :disabled="selectedChromStart == null"
            placeholder="6. Enter region end (optional)"
            :min="selectedChromStart == null ? 0 : selectedChromStart + 1"
            :max="selectedChrom == null ? 0 : selectedChrom.size"
            :pt="{
              root: { class: 'w-full md:w-full' }
            }"
            :ptOptions="{ mergeProps: true }"
          />
        </div>
        <div></div>
      </div>
      <div class="pt-8">
        <Button
          type="button"
          icon="pi pi-sync"
          label="Submit"
          :disabled="disabled"
          :loading="loadingButton"
          @click="submitQuery"
        />
      </div>
      <!-- SECTION -->
    </SectionLayout>
    <SectionLayout>
      <!-- TABLE -->
      <div>
        <DataTable
          :value="records"
          lazy
          paginator
          :first="first"
          :rows="10"
          v-model:filters="filters"
          @filter="onFilter($event)"
          filterDisplay="row"
          ref="dt"
          :totalRecords="totalRecords"
          :loading="loading"
          @page="onPage($event)"
          @sort="onSort($event)"
          removableSort
          sortMode="multiple"
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
          <Column field="chrom" header="Chrom" sortable exportHeader="chrom"></Column>
          <Column field="start" header="Start" sortable exportHeader="chromStart"></Column>
          <Column field="end" header="End" exportHeader="chromEnd"></Column>
          <Column field="name" header="Name" exportHeader="name"></Column>
          <Column field="score" header="Score" sortable exportHeader="score"></Column>
          <Column field="strand" header="Strand" exportHeader="strand"></Column>
          <Column field="coverage" header="Coverage" sortable exportHeader="coverage"></Column>
          <Column field="frequency" header="Frequency" sortable exportHeader="frequency"></Column>
          <Column
            field="feature"
            header="Feature"
            exportHeader="feature"
            filterField="feature"
            :showFilterMenu="false"
          >
            <template #filter="{ filterModel, filterCallback }">
              <MultiSelect
                v-model="filterModel.value"
                @change="filterCallback()"
                :options="features"
                placeholder="Any"
                :maxSelectedLabels="1"
                :disabled="disabled"
              >
              </MultiSelect>
            </template>
          </Column>
          <Column
            field="gene_biotype"
            header="Biotype"
            exportHeader="biotype"
            filterField="gene_biotype"
            :showFilterMenu="false"
          >
            <template #filter="{ filterModel, filterCallback }">
              <MultiSelect
                v-model="filterModel.value"
                @change="filterCallback()"
                :options="biotypes"
                placeholder="Any"
                :maxSelectedLabels="1"
                :disabled="disabled"
              >
              </MultiSelect>
            </template>
          </Column>
          <Column field="gene_name" header="Gene" exportHeader="geneName" :showFilterMenu="false">
            <template #filter="{ filterModel, filterCallback }">
              <InputText
                type="text"
                v-model="filterModel.value"
                @input="filterCallback()"
                placeholder="Search"
                :disabled="disabled"
              />
            </template>
          </Column>
          <Column field="tech" header="Technology" exportHeader="technology"></Column>
          <Column field="dataset_id" header="EUFID" exportHeader="dataset_id"></Column>
        </DataTable>
      </div>
    </SectionLayout>
  </DefaultLayout>
</template>

<style scoped></style>
