<script setup lang="ts">
import { computed, watch } from 'vue'
import InputNumber from 'primevue/inputnumber'
import FeatureSelect from '@/components/ui/FeatureSelect.vue'
import GeneSelect from '@/components/ui/GeneSelect.vue'
import ChromSelect from '@/components/ui/ChromSelect.vue'
import BiotypeSelect from '@/components/ui/BiotypeSelect.vue'
import QueryButton from '@/components/search/QueryButton.vue'
import {
  type DummySearchParameters,
  isSearchParameter,
  type SearchParameters
} from '@/utils/search'

const RNA_TYPE = 'WTS' // Should that be a parameter or calculated value?

const model = defineModel<SearchParameters | DummySearchParameters>()

const emit = defineEmits<{
  (e: 'submit', params: SearchParameters): void
}>()

const disabled = computed(() => model.value?.state !== 'complete')
const chromDisabled = computed(() => disabled.value || !!model?.value?.gene)

const selectionIds = computed(() => {
  if (isSearchParameter(model.value)) {
    return model.value.selections.map((x) => x.selection_id)
  } else {
    return []
  }
})

const taxaId = computed(() => {
  if (model.value && isSearchParameter(model.value) && model.value.taxa) {
    return model.value.taxa.taxa_id
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

function changeGene() {
  const v = model.value
  if (v) {
    v.chrom = undefined
  }
  clearCoords()
}

watch(
  () => model.value,
  () => {
    const v = model.value
    if (v) {
      if (v.state === 'incomplete') {
        changeGene()
        v.gene = undefined
        v.biotypes = undefined
        v.features = undefined
      }
    }
  }
)

function submit() {
  if (isSearchParameter(model.value)) {
    emit('submit', model.value)
  } else {
    throw new Error('Submit without valid parameters - this should never happen!')
  }
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
          :disabled="disabled"
          @change="changeGene()"
        />
      </div>
      <div class="col-span-3">
        <BiotypeSelect
          placeholder="Select biotype (optional)"
          v-model="model.biotypes"
          :rna-type="RNA_TYPE"
          :disabled="disabled"
        />
      </div>
      <div class="col-span-3">
        <FeatureSelect
          placeholder="Select feature (optional)"
          v-model="model.features"
          :rna-type="RNA_TYPE"
          :disabled="disabled"
        />
      </div>
    </div>

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
          :disabled="chromDisabled"
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
          :disabled="disabled || !model.chrom"
          :min="0"
          :max="!model.chrom ? 0 : model.chrom.size - 1"
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
          :disabled="disabled || !model.chrom"
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
      <div class="place-self-end">
        <QueryButton v-model="model" @submit="submit" />
      </div>
    </div>
  </div>
</template>
