<script setup>
import { ref, onMounted } from 'vue'
import { nestedSort, toCascade, toTree } from '@/utils'
import { HTTP } from '@/services/API'

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

const taxa = ref()
const selectedTaxa = ref()
const allSelections = ref()

const resetDefaults = () => {
  selectedModification.value = undefined
  selectedOrganism.value = undefined
  selectedTechnology.value = []
  selectionIds.value = []
  taxaId.value = 0 // TODO
  taxaName.value = undefined
  rnaType.value = 'WTS' // TODO
  selectedGene.value = undefined
  selectedBiotypes.value = undefined
  selectedFeatures.value = undefined
  selectedChrom.value = undefined
  selectedChromStart.value = undefined
  selectedChromEnd.value = undefined
}

const updateTaxa = (value) => {
  // note that the new model values will only be available after the parent has updated
  // and passed the updated value back down to the child - but here we don't need the values
  let opts = allSelections.value.filter((item) => item.taxa_id == value.key)
  selectionIds.value = opts.map((item) => item.selection_id)
  taxaName.value = [...new Set(opts.map((item) => item.taxa_name))][0]
  taxaId.value = value.key
}

// lifecyle
onMounted(() => {
  HTTP.get('/selections')
    .then(function (response) {
      allSelections.value = response.data
      allSelections.value = allSelections.value.map((item) => {
        const kingdom = Object.is(item.kingdom, null) ? item.domain : item.kingdom
        return { ...item, kingdom }
      })
      taxa.value = toCascade(toTree(allSelections.value, ['kingdom', 'taxa_sname'], 'taxa_id'))
      nestedSort(taxa.value, ['child1'])
    })
    .catch((error) => {
      console.log(error)
    })
  resetDefaults()
})
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-10 gap-6">
    <div class="col-span-3">
      <CascadeSelect
        @change="updateTaxa($event.value)"
        v-model="selectedTaxa"
        :options="taxa"
        optionLabel="label"
        optionGroupLabel="label"
        :optionGroupChildren="['child1']"
        placeholder="1. Select organism"
        :pt="{
          root: { class: 'w-full md:w-full' }
        }"
        :ptOptions="{ mergeProps: true }"
      />
    </div>
    <div class="col-span-3" />
    <div class="col-span-3" />
    <div />
  </div>
</template>
