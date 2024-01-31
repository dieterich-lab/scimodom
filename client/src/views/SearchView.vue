<script setup>
import { ref, computed, onMounted } from 'vue'
import { toIds, fmtOrder, fmtFilter } from '@/utils/index.js'
import { FilterMatchMode, FilterOperator } from 'primevue/api'
import {
  updModification,
  updTechnologyFromMod,
  updOrganismFromModAndTech
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

const disabled = computed(() => isAllSelected())

const dt = ref()
const first = ref(0)
const records = ref()
const loading = ref(false)
const loadingButton = ref(false)
const totalRecords = ref(0)
const lazyParams = ref({})
const filters = ref({
  gene_name_gc: { value: null, matchMode: 'contains' },
  gene_id_gc: { value: null, matchMode: 'contains' },
  gene_biotype_gc: { value: null, matchMode: 'in' },
  feature_gc: { value: null, matchMode: 'in' }
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
  //   loadingButton.value = false
  setTimeout(() => {
    loadingButton.value = false
  }, 2500)
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
  // console.log('FMT FILTER:', fmtFilter(lazyParams.value.filters))
  lazyLoad(event)
}

const onExport = () => {
  dt.value.exportCSV()
}

const updateTechnology = () => {
  selectedTechnology.value = undefined
  selectedOrganism.value = undefined
  technology.value = updTechnologyFromMod(options.value, selectedModification.value)
  // lazyLoad()
}

const updateOrganism = () => {
  selectedOrganism.value = undefined
  organism.value = updOrganismFromModAndTech(
    options.value,
    selectedModification.value,
    selectedTechnology.value
  )
  // lazyLoad()
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
        modification: toIds(selectedModification.value, []),
        technology: toIds(selectedTechnology.value, []),
        organism: toIds(selectedOrganism.value, []),
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
      <h1 class="font-ham mb-4 text-3xl font-extrabold text-gray-900 md:text-5xl lg:text-6xl">
        <span
          class="text-transparent bg-clip-text bg-gradient-to-r from-gg-2 from-10% via-gg-1 via-40% via-gb-2 via-60% to-gb-4 to-100"
        >
          Search
        </span>
        RNA modifications
      </h1>
      <p class="text-lg font-normal text-gray-500 lg:text-xl">
        Select filters and query the database
      </p>
      <!-- FILTER 1 -->
      <Divider />
      <!-- <div class="flex flex-row flex-wrap justify-start place-items-center [&>*]:mr-6"> -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <TreeSelect
            @change="updateTechnology()"
            v-model="selectedModification"
            :options="modification"
            selectionMode="checkbox"
            :metaKeySelection="false"
            placeholder="1. Select RNA modifications"
            :pt="{
              root: { class: 'w-full md:w-full' }
            }"
            :ptOptions="{ mergeProps: true }"
          />
        </div>
        <div>
          <TreeSelect
            @change="updateOrganism()"
            v-model="selectedTechnology"
            :options="technology"
            selectionMode="checkbox"
            :metaKeySelection="false"
            placeholder="2. Select technologies"
            :pt="{
              root: { class: 'w-full md:w-full' }
            }"
            :ptOptions="{ mergeProps: true }"
          />
        </div>
        <div>
          <TreeSelect
            @change="updateTmp()"
            v-model="selectedOrganism"
            :options="organism"
            selectionMode="checkbox"
            :metaKeySelection="false"
            placeholder="3. Select organisms"
            :pt="{
              root: { class: 'w-full md:w-full' }
            }"
            :ptOptions="{ mergeProps: true }"
          />
        </div>
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

      <!-- FILTER 2 -->
    </SectionLayout>
    <!-- SECTION -->
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
          <Column field="name" header="Name" exportHeader="name">
            <!-- <Column field="name" header="Name" exportHeader="name" :showFilterMenu="false"> -->
            <!-- <template #filter="{ filterModel, filterCallback }">
                 <MultiSelect
                 v-model="filterModel.value"
                 @change="filterCallback()"
                 :options="names"
                 placeholder="Any"
                 :maxSelectedLabels="1"
                 >
                 </MultiSelect>
                 </template> -->
          </Column>
          <Column field="score" header="Score" sortable exportHeader="score"></Column>
          <Column field="strand" header="Strand" exportHeader="strand"></Column>
          <Column field="coverage" header="Coverage" sortable exportHeader="coverage"></Column>
          <Column field="frequency" header="Frequency" sortable exportHeader="frequency"></Column>
          <Column
            field="gene_name_gc"
            header="Gene"
            exportHeader="geneName"
            filterMatchMode="startsWith"
          >
            <!-- <template #filter="{ filterModel, filterCallback }">
                 <InputText
                 type="text"
                 v-model="filterModel.value"
                 @keydown.enter="filterCallback()"
                 class="p-column-filter"
                 placeholder="Search"
                 />
                 </template> -->
          </Column>
          <Column
            field="gene_id_gc"
            header="Gene ID"
            exportHeader="geneId"
            FilterMatchMode="startsWith"
          >
            <!-- <template #filter="{ filterModel, filterCallback }">
                 <InputText
                 type="text"
                 v-model="filterModel.value"
                 @keydown.enter="filterCallback()"
                 class="p-column-filter"
                 placeholder="Search"
                 />
                 </template> -->
          </Column>
          <Column
            field="gene_biotype_gc"
            header="Biotype"
            exportHeader="biotype"
            :showFilterMenu="false"
          >
            <!-- <template #filter="{ filterModel, filterCallback }">
                 <MultiSelect
                 v-model="filterModel.value"
                 @change="filterCallback()"
                 :options="biotypes"
                 placeholder="Any"
                 :maxSelectedLabels="1"
                 >
                 </MultiSelect>
                 </template> -->
          </Column>
          <Column
            field="feature_gc"
            header="Feature"
            exportHeader="feature"
            :showFilterMenu="false"
          >
            <!-- <template #filter="{ filterModel, filterCallback }">
                 <MultiSelect
                 v-model="filterModel.value"
                 @change="filterCallback()"
                 :options="features"
                 placeholder="Any"
                 :maxSelectedLabels="1"
                 >
                 </MultiSelect>
                 </template> -->
          </Column>
        </DataTable>
      </div>
    </SectionLayout>
  </DefaultLayout>
</template>

<style scoped></style>
