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
const loading = ref(false)
const totalRecords = ref(0)
const lazyParams = ref({})

const productTable = ref()

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

onMounted(() => {
  lazyParams.value = {
    first: 0,
    rows: dt.value.rows
    // sortField: null,
    // sortOrder: null,
    // filters: filters.value
  }
  lazyLoad()
  service
    .getEndpoint('/selection')
    .then(function (response) {
      selectOptions.value = response.data
      modification.value = toTree(selectOptions.value, ['rna', 'modomics_sname'], 'modification_id')
      // modification.value = toTree(selectOptions.value, ['rna', 'modomics_sname'])
      console.log(modification.value)
    })
    .catch((error) => {
      console.log(error)
    })
})

// is || really working when selecting only rna or only short_name, both, or when e.g. m6A on both mRNA and tRNA?, etc.
const updateTechnology = () => {
  selectedTechnology.value = undefined
  selectedSpecies.value = undefined
  // var selected = Object.keys(JSON.parse(JSON.stringify(selectedModification.value)))
  // var selected = Object.keys(selectedModification.value).map(Number).filter(value => !Number.isNaN(value))
  var selected = toIds(selectedModification.value)
  console.log('SELECTED=', selected)
  var options = selectOptions.value.filter((item) => selected.includes(item.modification_id))
  technology.value = toTree(options, ['cls', 'meth', 'tech'], 'technology_id')
  lazyLoad()
}

const updateSpecies = () => {
  selectedSpecies.value = undefined
  var selected1 = toIds(selectedModification.value)
  var selected2 = toIds(selectedTechnology.value)
  var options = selectOptions.value.filter(
    (item) => selected1.includes(item.modification_id) && selected2.includes(item.technology_id)
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
      productTable.value = response.data.records
      totalRecords.value = response.data.totalRecords
    })
    .catch((error) => {
      console.log(error)
    })
  loading.value = false
}

const onPage = (event) => {
  lazyParams.value = event
  lazyLoad()
}
</script>

<template>
  <DefaultLayout>
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
      <!-- <Divider :pt="{ root: { class: 'bg-crmapgreen' } }" /> -->
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
              root: { class: 'max-w-[30rem] md:w-full' },
              tree: {
                container: 'm-0 p-0 list-none -space-y-2 overflow-auto',
                toggler: ({ context }) => ({
                  class: [
                    'cursor-pointer select-none inline-flex items-center justify-center overflow-hidden relative shrink-0',
                    'mr-2 w-8 h-8 border-0 bg-transparent rounded-full transition duration-200',
                    'hover:border-transparent focus:outline-none focus:outline-offset-0 focus:shadow-[0_0_0_0.2rem_rgba(114,191,132,1)]',
                    {
                      'text-gray-500 hover:bg-crmapgreen1 hover:text-gray-800': !context.selected,
                      'text-red-600 hover:bg-crmapgreen1': context.selected
                    },
                    {
                      hidden: context.leaf
                    }
                  ]
                }),
                checkbox: ({ context, props }) => ({
                  class: [
                    'cursor-pointer inline-flex relative select-none align-bottom',
                    'w-6 h-6',
                    'flex items-center justify-center',
                    'border-2 w-6 h-6 rounded-lg transition-colors duration-200 text-white text-base',
                    {
                      'border-gray-300 bg-white': !context.checked,
                      'border-crmapgreen1 text-white bg-crmapgreen1': context.checked
                    },
                    {
                      'hover:border-crmapgreen1 focus:outline-none focus:outline-offset-0 focus:shadow-[0_0_0_0.2rem_rgba(114,191,132,1)]':
                        !props.disabled,
                      'cursor-default opacity-60': props.disabled
                    }
                  ]
                }),
                subgroup: {
                  class: ['ml-4 list-none', 'p-0']
                }
              }
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
            class="w-full md:w-20rem"
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
            class="w-full md:w-20rem"
          />
        </div>
      </div>
      <!-- FILTER 2 -->
    </SectionLayout>

    <SectionLayout>
      <DataTable
        :value="productTable"
        lazy
        paginator
        :rows="10"
        ref="dt"
        :totalRecords="totalRecords"
        :loading="loading"
        @page="onPage($event)"
        tableStyle="min-width: 100rem"
      >
        <Column field="chrom" header="chrom"></Column>
        <Column field="start" header="start"></Column>
        <Column field="end" header="end"></Column>
        <Column field="strand" header="strand"></Column>
        <Column field="score" header="score"></Column>
      </DataTable>
    </SectionLayout>

    <!-- results table -->
  </DefaultLayout>
</template>

<style scoped></style>
