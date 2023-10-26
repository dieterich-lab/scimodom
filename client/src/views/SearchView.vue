<script setup>
import { ref, onMounted } from 'vue'
import service from '@/services/index.js'

const selectOptions = ref()
const modification = ref()
const selectedModification = ref()
const technology = ref()
const selectedTechnology = ref()
const species = ref()
const selectedSpecies = ref()
const dt = ref()
const records = ref()
const loading = ref(false)
const totalRecords = ref(0)
const lazyParams = ref({})

const onPage = (event) => {
  lazyParams.value = event
  lazyLoad()
}

const onSort = (event) => {
  lazyParams.value = event
  lazyLoad()
}

const onFilter = () => {
  lazyParams.value.filters = filters.value
  lazyLoad()
}

onMounted(() => {
  lazyParams.value = {
    first: dt.value.first,
    rows: dt.value.rows,
    sortField: null,
    sortOrder: null
    // filters: filters.value
  }
  lazyLoad()
  service
    .getEndpoint('/selection')
    .then(function (response) {
      selectOptions.value = response.data
      modification.value = toTree(selectOptions.value, ['rna', 'modomics_sname'], 'modification_id')
    })
    .catch((error) => {
      console.log(error)
    })
})

const updateTechnology = () => {
  selectedTechnology.value = undefined
  selectedSpecies.value = undefined
  var selectedModificationIds = toIds(selectedModification.value)
  var options = selectOptions.value.filter((item) =>
    selectedModificationIds.includes(item.modification_id)
  )
  technology.value = toTree(options, ['cls', 'meth', 'tech'], 'technology_id')
  lazyLoad()
}

const updateSpecies = () => {
  selectedSpecies.value = undefined
  var selectedModificationIds = toIds(selectedModification.value)
  var selectedTechnologyIds = toIds(selectedTechnology.value)
  var options = selectOptions.value.filter(
    (item) =>
      selectedModificationIds.includes(item.modification_id) &&
      selectedTechnologyIds.includes(item.technology_id)
  )
  species.value = toTree(
    options,
    ['domain', 'kingdom', 'phylum', 'taxa_sname', 'cto'],
    'organism_id'
  )
  lazyLoad()
}

const updateTmp = () => {
  lazyLoad()
}

function toTree(data, keys, id) {
  var len = keys.length - 1
  var tree = data.reduce((r, o) => {
    keys.reduce((t, k, idx) => {
      var jdx = idx === len ? id : k
      var tmp = (t.children = t.children || []).find((p) => p.key === o[jdx])
      if (!tmp) {
        t.children.push((tmp = { key: o[jdx], label: o[k] }))
      }
      return tmp
    }, r)
    return r
  }, {}).children
  return tree
}

function toIds(array) {
  if (!(array === undefined)) {
    return Object.keys(array)
      .map(Number)
      .filter((value) => !Number.isNaN(value))
  }
  return []
}

function lazyLoad() {
  loading.value = true
  service
    .get('/search', {
      params: {
        modification: toIds(selectedModification.value),
        technology: toIds(selectedTechnology.value),
        organism: toIds(selectedSpecies.value),
        firstRecord: lazyParams.value.first,
        maxRecords: lazyParams.value.rows
      },
      paramsSerializer: {
        indexes: null
      }
    })
    .then(function (response) {
      records.value = response.data.records
      totalRecords.value = response.data.totalRecords
    })
    .catch((error) => {
      console.log(error)
    })
  loading.value = false
}
</script>

<template>
  <DefaultLayout>
    <!-- SECTION -->
    <SectionLayout>
      <h1 class="font-ham mb-4 text-3xl font-extrabold text-gray-900 md:text-5xl lg:text-6xl">
        <span
          class="text-transparent bg-clip-text bg-gradient-to-r from-crmapgreen2 from-10% via-crmapgreen1 via-40% via-crmapblue2 via-60% to-crmapblue4 to-100"
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
          />
        </div>
        <div>
          <TreeSelect
            @change="updateSpecies()"
            v-model="selectedTechnology"
            :options="technology"
            selectionMode="checkbox"
            :metaKeySelection="false"
            placeholder="2. Select technologies"
          />
        </div>
        <div>
          <TreeSelect
            @change="updateTmp()"
            v-model="selectedSpecies"
            :options="species"
            selectionMode="checkbox"
            :metaKeySelection="false"
            placeholder="3. Select organisms"
          />
        </div>
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
          :first="0"
          :rows="10"
          ref="dt"
          :totalRecords="totalRecords"
          :loading="loading"
          @page="onPage($event)"
          @sort="onSort($event)"
          @filter="onFilter($event)"
          removableSort
          sortMode="multiple"
          :multiSortMeta="[
            { field: 'chrom', order: 1 },
            { field: 'start', order: 1 }
          ]"
          stripedRows
        >
          <Column
            field="chrom"
            header="Chrom"
            sortable
            exportHeader="Chromosome"
            style="width: 20%"
          ></Column>
          <Column field="start" header="start"></Column>
          <Column field="end" header="end"></Column>
          <Column field="strand" header="strand"></Column>
          <Column field="score" header="score"></Column>
        </DataTable>
      </div>
    </SectionLayout>
  </DefaultLayout>
</template>

<style scoped></style>
