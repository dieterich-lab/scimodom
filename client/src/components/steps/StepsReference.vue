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

onMounted(() => {
  service
    .getEndpoint('/selection')
    .then(function (response) {
      selectOptions.value = response.data
      species.value = toTree(
        selectOptions.value,
        ['domain', 'kingdom', 'phylum', 'taxa_sname', 'cto'],
        'organism_id'
      )
    })
    .catch((error) => {
      console.log(error)
    })
})

const updateModification = () => {
  selectedModification.value = undefined
  selectedTechnology.value = undefined
  var selectedSpeciesIds = toIds(selectedSpecies.value)
  console.log('VALUES', selectedSpecies.value)
  console.log('IDS', selectedSpeciesIds)
  var options = selectOptions.value.filter((item) => selectedSpeciesIds.includes(item.taxa_sname))
  console.log('OPTIONS', options)
  modification.value = toTree(options, ['rna', 'modomics_sname'], 'modification_id')
}

const updateTechnology = () => {
  selectedTechnology.value = undefined
  selectedSpecies.value = undefined
  var selectedModificationIds = toIds(selectedModification.value)
  var options = selectOptions.value.filter((item) =>
    selectedModificationIds.includes(item.modification_id)
  )
  technology.value = toTree(options, ['cls', 'meth', 'tech'], 'technology_id')
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
}

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

function toIds(array) {
  if (!(array === undefined)) {
    return Object.keys(array)
      .map(Number)
      .filter((value) => !Number.isNaN(value))
  }
  return []
}
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
    <div>
      <TreeSelect
        @change="updateModification()"
        v-model="selectedSpecies"
        :options="species"
        placeholder="1. Select one organism"
      />
    </div>
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
        v-model="selectedTechnology"
        :options="technology"
        selectionMode="checkbox"
        :metaKeySelection="false"
        placeholder="2. Select technologies"
      />
    </div>
  </div>
</template>
