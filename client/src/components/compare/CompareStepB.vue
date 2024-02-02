<script setup>
import { ref, watch } from 'vue'
import {
  updOrganismFromSpec,
  updModificationFromOrg,
  updTechnologyFromOrgAndMod,
  updDataset
} from '@/utils/selection.js'
import service from '@/services/index.js'

const props = defineProps({
  selectedSpecies: {
    type: String,
    required: true
  },
  referenceDataset: {
    type: Array,
    required: true
  },
  options: {
    type: Array,
    required: true
  },
  dataset: {
    type: Array,
    required: true
  }
})

const disabled = ref(false)
const uploadURL = service.getUri() + '/upload'

const modification = ref()
const selectedModification = ref()
const technology = ref()
const selectedTechnology = ref()
const organism = ref()
const selectedOrganism = ref()
const datasetSelection = ref()
const selectedDataset = ref()

const emit = defineEmits(['selectedDataset', 'uploadedDataset'])

watch(
  () => props.selectedSpecies,
  () => {
    modification.value = undefined
    technology.value = undefined
    selectedOrganism.value = undefined
    selectedModification.value = undefined
    selectedTechnology.value = undefined
    organism.value = updOrganismFromSpec(props.options, props.selectedSpecies)
    updateDataset()
    emitNone()
  },
  { immediate: true }
)

watch(
  () => props.referenceDataset,
  () => {
    modification.value = undefined
    technology.value = undefined
    selectedOrganism.value = undefined
    selectedModification.value = undefined
    selectedTechnology.value = undefined
    updateDataset()
    emitNone()
  },
  { immediate: true }
)

const onUpload = (event) => {
  disabled.value = true
  selectedDataset.value = undefined
  emit('uploadedDataset', event.xhr.response)
  emit('selectedDataset', undefined)
}

const updateModification = () => {
  selectedModification.value = undefined
  selectedTechnology.value = undefined
  selectedDataset.value = undefined
  modification.value = updModificationFromOrg(props.options, selectedOrganism.value)
  updateDataset()
}

const updateTechnology = () => {
  selectedTechnology.value = undefined
  selectedDataset.value = undefined
  technology.value = updTechnologyFromOrgAndMod(
    props.options,
    selectedOrganism.value,
    selectedModification.value
  )
  updateDataset()
}

function emitNone() {
  emit('uploadedDataset', undefined)
  emit('selectedDataset', undefined)
}

function updateDataset() {
  selectedDataset.value = undefined
  datasetSelection.value = updDataset(
    props.options,
    organism.value,
    selectedOrganism.value,
    selectedModification.value,
    selectedTechnology.value,
    props.dataset,
    {
      isFilter: true,
      slctDS: props.referenceDataset
    }
  )
  disabled.value =
    Object.is(props.referenceDataset, undefined) || props.referenceDataset.length === 0
      ? true
      : false
}
</script>

<template>
  <div class="grid grid-flow-row-dense grid-cols-4 gap-6">
    <FileUpload
      mode="basic"
      name="file"
      :url="uploadURL"
      accept="text/plain,.bed,.bedrmod"
      :maxFileSize="1000000"
      :auto="true"
      chooseLabel="Upload modifications (bedRMod)"
      @upload="onUpload($event)"
      :disabled="disabled"
      :pt="{
        root: { class: 'w-full md:w-full' }
      }"
      :ptOptions="{ mergeProps: true }"
    >
    </FileUpload>
    <MultiSelect
      @change="updateModification"
      v-model="selectedOrganism"
      :options="organism"
      optionLabel="label"
      placeholder="1. Select cell/tissue"
      :maxSelectedLabels="3"
      :disabled="disabled"
      :pt="{
        root: { class: 'w-full md:w-full' }
      }"
      :ptOptions="{ mergeProps: true }"
    />
    <TreeSelect
      @change="updateTechnology"
      v-model="selectedModification"
      :options="modification"
      selectionMode="checkbox"
      :metaKeySelection="false"
      placeholder="2. Select RNA modifications"
      :disabled="disabled"
      :pt="{
        root: { class: 'w-full md:w-full' }
      }"
      :ptOptions="{ mergeProps: true }"
    />
    <TreeSelect
      @change="updateDataset"
      v-model="selectedTechnology"
      :options="technology"
      selectionMode="checkbox"
      :metaKeySelection="false"
      placeholder="3. Select technologies"
      :disabled="disabled"
      :pt="{
        root: { class: 'w-full md:w-full' }
      }"
      :ptOptions="{ mergeProps: true }"
    />
    <MultiSelect
      @change="
        emit(
          'selectedDataset',
          $event.value.map((d) => d.dataset_id)
        )
      "
      v-model="selectedDataset"
      :options="datasetSelection"
      filter
      optionLabel="dataset_display"
      placeholder="4. Select dataset"
      :maxSelectedLabels="3"
      :disabled="disabled"
      :pt="{
        root: { class: 'col-span-4 w-full md:w-full' }
      }"
      :ptOptions="{ mergeProps: true }"
    />
  </div>
</template>
