<script setup lang="ts">
import { computed } from 'vue'
import FeatureSelect from '@/components/search/FeatureSelect.vue'
import GeneSelect from '@/components/search/GeneSelect.vue'
import ChromSelect from '@/components/search/ChromSelect.vue'
import BiotypeSelect from '@/components/search/BiotypeSelect.vue'
import {
  type DummySearchParameters,
  isSearchParameter,
  type SearchParameters
} from '@/utils/search'

const model = defineModel<SearchParameters | DummySearchParameters>()

const selectionIds = computed(() => {
  if (model?.value?.state === 'complete') {
    return model.value.selections.map((x) => x.selection_id)
  } else {
    return []
  }
})

const rnaType = computed(() => {
  if (model.value && isSearchParameter(model.value) && model.value.modificationType) {
    return model.value.modificationType.rna_name
  }
  return ''
})

const taxaId = computed(() => {
  if (model.value && isSearchParameter(model.value) && model.value.organism) {
    return model.value.organism.taxa_id
  }
  return undefined
})

function clearCoords() {
  const v = model.value
  if (v) {
    v.chromStart = undefined
    v.chromEnd = undefined
  }
}

function clearChrom() {
  const v = model.value
  if (v) {
    v.chrom = undefined
  }
  clearCoords()
}
</script>
<template>
  <div v-if="model !== undefined">
    <div class="grid grid-cols-1 md:grid-cols-10 gap-6 mt-6">
      <div class="col-span-3">
        <GeneSelect
          :placeholder="
            model.searchBy === 'Modification' ? 'Select gene (optional)' : '2. Select gene'
          "
          v-model="model.gene"
          :selection-ids="selectionIds"
          :disabled="model.state === 'incomplete'"
          @change="clearChrom()"
        />
      </div>
      <div class="col-span-3">
        <BiotypeSelect
          placeholder="Select biotype (optional)"
          v-model="model.biotypes"
          :rna-type="rnaType"
          :disabled="model.state === 'incomplete'"
        />
      </div>
      <div class="col-span-3">
        <FeatureSelect
          placeholder="Select feature (optional)"
          v-model="model.features"
          :rna-type="rnaType"
          :disabled="model.state === 'incomplete'"
        />
      </div>
    </div>
    <!-- FILTER 3 -->
    <div class="grid grid-cols-1 md:grid-cols-10 gap-6 mt-6">
      <div class="col-span-3">
        <ChromSelect
          :placeholder="
            model.searchBy === 'Modification'
              ? 'Select chromosome (optional)'
              : '2. Select chromosome'
          "
          v-model="model.chrom"
          :taxa-id="taxaId"
          :disabled="model.state === 'incomplete' || !model.gene"
          @change="clearCoords()"
        />
      </div>
      <div class="col-span-3">
        <InputNumber
          @input="model.chromEnd = undefined"
          v-model="model.chromStart"
          inputId="minmax"
          :placeholder="
            model.searchBy === 'Modification'
              ? 'Enter chromosome start (optional)'
              : 'Enter chromosome start'
          "
          :disabled="model.state === 'incomplete'"
          :min="0"
          :max="model.chrom === undefined ? 0 : model.chrom.size - 1"
          :pt="{
            root: { class: 'w-full md:w-full' }
          }"
          :ptOptions="{ mergeProps: true }"
        />
      </div>
      <div class="col-span-3">
        <InputNumber
          v-model="model.chromEnd"
          inputId="minmax"
          :disabled="model.state === 'incomplete'"
          :placeholder="
            model.searchBy === 'Modification'
              ? 'Enter chromosome end (optional)'
              : 'Enter chromosome end'
          "
          :min="model.chromStart === undefined ? 0 : model.chromStart + 1"
          :max="model.chrom ? model.chrom.size : 0"
          :pt="{
            root: { class: 'w-full md:w-full' }
          }"
          :ptOptions="{ mergeProps: true }"
        />
      </div>
    </div>
  </div>
</template>
