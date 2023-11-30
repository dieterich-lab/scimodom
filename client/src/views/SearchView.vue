<script setup>
import { ref, onMounted } from 'vue'
import { toTree, toIds, fmtOrder } from '@/utils/index.js'
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

const onExport = () => {
  dt.value.exportCSV()
}

onMounted(() => {
  lazyParams.value = {
    first: dt.value.first,
    rows: dt.value.rows
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
  var selectedModificationIds = toIds(selectedModification.value, [])
  var options = selectOptions.value.filter((item) =>
    selectedModificationIds.includes(item.modification_id)
  )
  technology.value = toTree(options, ['cls', 'meth', 'tech'], 'technology_id')
  lazyLoad()
}

const updateSpecies = () => {
  selectedSpecies.value = undefined
  var selectedModificationIds = toIds(selectedModification.value, [])
  var selectedTechnologyIds = toIds(selectedTechnology.value, [])
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

function lazyLoad() {
  loading.value = true
  service
    .get('/search', {
      params: {
        modification: toIds(selectedModification.value, []),
        technology: toIds(selectedTechnology.value, []),
        organism: toIds(selectedSpecies.value, []),
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
          class="text-transparent bg-clip-text bg-gradient-to-r from-crmgs-50 from-10% via-crmgs-25 via-40% via-crmbs-50 via-60% to-crmbs-100 to-100"
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
            :pt="{
              root: { class: 'w-full md:w-full' }
            }"
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
            :pt="{
              root: { class: 'w-full md:w-full' }
            }"
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
                @click="onExport($event)"
                :pt="{
                  root: {
                    class:
                      'bg-crmb border-crmb hover:bg-crmb/75 hover:border-crmb/75 focus:ring-crmb/75 focus:outline-none focus:shadow-[0_0_0_2px_rgba(255,255,255,1),0_0_0_4px_rgba(2,176,237,1),0_1px_2px_0_rgba(0,0,0,1)]'
                  }
                }"
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
        </DataTable>
      </div>
    </SectionLayout>
  </DefaultLayout>
</template>

<style scoped></style>
