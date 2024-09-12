<script setup>
import { ref, onMounted } from 'vue'
import { HTTP } from '@/services/API'
import {
  updModification,
  updOrganismFromMod,
  updTechnologyFromModAndOrg,
  updSelectionFromAll
} from '@/utils/selection.js'

const selectedModification = defineModel('selectedModification')
const selectedOrganism = defineModel('selectedOrganism')
const selectedTechnology = defineModel('selectedTechnology')
const selectionIds = defineModel('selectionIds')
const taxaId = defineModel('taxaId')
const taxaName = defineModel('taxaName')
const rnaType = defineModel('rnaType')

const selectedGene = defineModel('selectedGene')
const selectedBiotypes = defineModel('selectedBiotypes')
const selectedFeatures = defineModel('selectedFeatures')
const selectedChrom = defineModel('selectedChrom')
const selectedChromStart = defineModel('selectedChromStart')
const selectedChromEnd = defineModel('selectedChromEnd')

const allSelections = ref()
const modifications = ref()
const organisms = ref()
const technologies = ref()
const selectedTechnologyObject = ref()

// utilities to reset options/filters
const clearAll = (value) => {
  if (value < 1) {
    technologies.value = undefined
    selectedOrganism.value = undefined
  }
  if (value < 2) {
    selectedTechnologyObject.value = undefined
    selectedTechnology.value = []
  }
  selectedGene.value = undefined
  selectedBiotypes.value = undefined
  selectedFeatures.value = undefined
  selectedChrom.value = undefined
  selectedChromStart.value = undefined
  selectedChromEnd.value = undefined
  selectionIds.value = []
  taxaId.value = 0 // TODO
  taxaName.value = undefined
  rnaType.value = ''
}

// search callbacks
const updateOrganism = (value) => {
  // on first filter (selectedModification) change
  clearAll(0)
  organisms.value = updOrganismFromMod(allSelections.value, value)
}
const updateTechnology = (value) => {
  // on second filter (selectedOrganism) change
  clearAll(1)
  technologies.value = updTechnologyFromModAndOrg(
    allSelections.value,
    selectedModification.value,
    value
  )
}
const updateSelection = (value) => {
  // on third filter (selectedTechnologyObject) change
  clearAll(2)
  let result = updSelectionFromAll(
    allSelections.value,
    selectedModification.value,
    selectedOrganism.value,
    value
  )
  selectedTechnology.value = result.technology
  selectionIds.value = result.selection
  taxaId.value = result.taxaId
  taxaName.value = result.taxaName
  rnaType.value = result.rna
}

// functions
onMounted(() => {
  HTTP.get('/selections')
    .then(function (response) {
      allSelections.value = response.data
      modifications.value = updModification(allSelections.value)
    })
    .catch((error) => {
      console.log(error)
    })
})
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-10 gap-6">
    <div class="col-span-3">
      <Dropdown
        @change="updateOrganism($event.value)"
        v-model="selectedModification"
        :options="modifications"
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
        @change="updateTechnology($event.value)"
        v-model="selectedOrganism"
        :options="organisms"
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
        @change="updateSelection($event)"
        v-model="selectedTechnologyObject"
        :options="technologies"
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
</template>
