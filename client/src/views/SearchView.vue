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

function toTree(data, keys) {
  var tree = data.reduce((r, o) => {
    keys.reduce((t, k) => {
      var tmp = (t.children = t.children || []).find((p) => p.key === o[k])
      if (!tmp) {
        t.children.push((tmp = { key: o[k], label: o[k] }))
      }
      return tmp
    }, r)
    return r
  }, {}).children
  return tree
}

onMounted(() => {
  lazyParams.value = {
    first: 0
    // rows: dt.value.rows,
    // sortField: null,
    // sortOrder: null,
    // filters: filters.value
  }
  // lazyLoad()
  service
    .getEndpoint('/selection')
    .then(function (response) {
      selectOptions.value = response.data
      modification.value = toTree(selectOptions.value, ['rna', 'short_name'])
    })
    .catch((error) => {
      console.log(error)
    })
})

// is || really working when selecting only rna or only short_name, both, or when e.g. m6A on both mRNA and tRNA?, etc.
const updateTechnology = () => {
  selectedTechnology.value = undefined
  selectedSpecies.value = undefined
  var selected = Object.keys(JSON.parse(JSON.stringify(selectedModification.value)))
  var options = selectOptions.value.filter(
    (item) => selected.includes(item.rna) || selected.includes(item.short_name)
  )
  technology.value = toTree(options, ['cls', 'meth', 'tech'])
  // lazyLoad()
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
      <Divider :pt="{ root: { class: 'bg-crmapgreen' } }" />
      <!-- <div class="flex flex-row flex-wrap justify-start place-items-center [&>*]:mr-6"> -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <TreeSelect
            @change="updateTechnology()"
            v-model="selectedModification"
            :options="modification"
            selectionMode="multiple"
            :metaKeySelection="false"
            placeholder="1. Select RNA modifications"
            class="w-full md:w-20rem"
          />
        </div>
        <div>
          <TreeSelect
            v-model="selectedTechnology"
            :options="technology"
            selectionMode="multiple"
            :metaKeySelection="false"
            placeholder="2. Select technologies"
            class="w-full md:w-20rem"
          />
        </div>
        <div>
          <TreeSelect
            v-model="selectedSpecies"
            :options="species"
            selectionMode="multiple"
            :metaKeySelection="false"
            placeholder="3. Select organisms"
            class="w-full md:w-20rem"
          />
        </div>
      </div>
      <!-- FILTER 2 -->
    </SectionLayout>

    <!-- results table -->
  </DefaultLayout>
</template>

<style scoped></style>
