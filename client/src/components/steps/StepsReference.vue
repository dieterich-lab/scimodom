<script setup>
import { ref, onMounted } from 'vue'
import service from '@/services/index.js'

// const selectOptions = ref()
const modification = ref()
const selectedModification = ref()
const technology = ref()
const selectedTechnology = ref()
const species = ref()
const selectedSpecies = ref()
const cto = ref()
const selectedCto = ref()
// const referenceDataset = ref()
const dataset = ref()
const selectedDataset = ref()

const props = defineProps({
  selectOptions: {
    type: Array,
    required: true
  },
  referenceDataset: {
    type: Array,
    required: true
  }
})

species.value = toTree(props.selectOptions, ['domain', 'taxa_sname'], 'taxa_sname')

// onMounted(() => {
//   service
//     .getEndpoint('/selection')
//     .then(function (response) {
//       selectOptions.value = response.data
//       species.value = toTree(selectOptions.value, ['domain', 'taxa_sname'], 'taxa_sname')
//     })
//     .catch((error) => {
//       console.log(error)
//     })
//   service
//     .getEndpoint('/compare/dataset')
//     .then(function (response) {
//       referenceDataset.value = response.data
//     })
//     .catch((error) => {
//       console.log(error)
//     })
// })

const updateCto = () => {
  selectedCto.value = undefined
  selectedModification.value = undefined
  selectedTechnology.value = undefined
  selectedDataset.value = undefined
  var options = props.selectOptions.filter(
    (item) => item.taxa_sname === selectedSpecies.value.label
  )
  cto.value = toTree(options, ['cto'], 'organism_id')
  updateDataset()
}

const updateModification = () => {
  selectedModification.value = undefined
  selectedTechnology.value = undefined
  selectedDataset.value = undefined
  var selectedCtoIds = selectedCto.value.map((item) => item.key)
  var options = props.selectOptions.filter((item) => selectedCtoIds.includes(item.organism_id))
  modification.value = toTree(options, ['rna', 'modomics_sname'], 'modification_id')
  updateDataset()
}

const updateTechnology = () => {
  selectedTechnology.value = undefined
  selectedDataset.value = undefined
  var selectedModificationIds = toIds(
    selectedModification.value,
    Array.from(new Set(props.selectOptions.map((item) => item.modification_id)))
  )
  var selectedCtoIds = selectedCto.value.map((item) => item.key)
  var options = props.selectOptions.filter(
    (item) =>
      selectedModificationIds.includes(item.modification_id) &&
      selectedCtoIds.includes(item.organism_id)
  )
  technology.value = toTree(options, ['cls', 'meth', 'tech'], 'technology_id')
  updateDataset()
}

function updateDataset() {
  selectedDataset.value = undefined
  var selectedModificationIds = toIds(
    selectedModification.value,
    Array.from(new Set(props.selectOptions.map((item) => item.modification_id)))
  )
  var selectedTechnologyIds = toIds(
    selectedTechnology.value,
    Array.from(new Set(props.selectOptions.map((item) => item.technology_id)))
  )
  // var selectedCtoIds = selectedCto.value.map((item) => item.key)
  var selectedCtoIds =
    Object.is(selectedCto.value, undefined) || selectedCto.value.length === 0
      ? cto.value.map((item) => item.key)
      : selectedCto.value.map((item) => item.key)
  var options = props.referenceDataset.filter(
    (item) =>
      selectedModificationIds.includes(item.modification_id) &&
      selectedTechnologyIds.includes(item.technology_id) &&
      selectedCtoIds.includes(item.organism_id)
  )
  dataset.value = [...new Map(options.map((item) => [item['dataset_id'], item])).values()].map(
    (item) => {
      return { dataset_id: item.dataset_id, dataset_title: item.dataset_title }
    }
  )
}

// const emit = defineEmits(['selected-dataset'])
// const emitSelectedDataset = (event) => {
//   let datasetIds = event.value.map((item) => item.dataset_id)
//   console.log("EMIT", datasetIds)
//   console.log("EVENT", event.value)
//   emit('selected-dataset', datasetIds)
// }

const updateTmp = () => {}

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

function toIds(array, defaultArray) {
  if (!(array === undefined || Object.keys(array).length === 0)) {
    return Object.keys(array)
      .map(Number)
      .filter((value) => !Number.isNaN(value))
  }
  return defaultArray
}
</script>

<template>
  <div>
    <Card>
      <template v-slot:title> Select a reference dataset </template>
      <template v-slot:subtitle> Choose your seat </template>
      <template v-slot:content>
        <div class="grid grid-flow-row-dense grid-cols-6 grid-row-2 gap-6">
          <Dropdown
            @change="updateCto"
            v-model="selectedSpecies"
            filter
            :options="species"
            optionLabel="label"
            optionGroupLabel="label"
            optionGroupChildren="children"
            placeholder="1. Select one organism"
          />
          <MultiSelect
            @change="updateModification"
            v-model="selectedCto"
            :options="cto"
            optionLabel="label"
            placeholder="2. Select cell/tissue"
            :maxSelectedLabels="3"
          />
          <div class="col-span-2">
            <TreeSelect
              @change="updateTechnology"
              v-model="selectedModification"
              :options="modification"
              selectionMode="checkbox"
              :metaKeySelection="false"
              placeholder="3. Select RNA modifications"
            />
          </div>
          <div class="cold-span-2">
            <TreeSelect
              @change="updateDataset"
              v-model="selectedTechnology"
              :options="technology"
              selectionMode="checkbox"
              :metaKeySelection="false"
              placeholder="4. Select technologies"
            />
          </div>
          <div class="col-span-6 w-full">
            <MultiSelect
              @change="
                $emit(
                  'selectedDataset',
                  selectedDataset.map((item) => item.dataset_id)
                )
              "
              v-model="selectedDataset"
              :options="dataset"
              filter
              optionLabel="dataset_title"
              placeholder="5. Select dataset"
              :maxSelectedLabels="3"
              :pt="{
                root: { class: 'md:w-full' },
                item: ({ props, state, context }) => ({
                  class: context.selected
                    ? 'bg-blue-300'
                    : context.focused
                    ? 'bg-blue-100'
                    : undefined
                })
              }"
            />
          </div>
        </div>
      </template>
      <template v-slot:footer>
        <div class="grid grid-flow-col auto-cols-max justify-between">
          <div />
          <Button
            @click="nextPage()"
            icon="pi pi-angle-right"
            iconPos="right"
            label="Next"
            size="small"
            :pt="{
              root: {
                class:
                  'bg-crmb border-crmb hover:bg-crmbs-50 hover:border-crmbs-50 focus:ring-crmbs-50 focus:outline-none'
              }
            }"
          />
        </div>
      </template>
    </Card>
  </div>
</template>
