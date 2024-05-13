<script setup>
import { onMounted, ref } from 'vue'
import { HTTP, HTTPSecure } from '@/services/API'
import AbstractStyle from '@/ui_styles/AbstractStyle'
import DefaultStyle from '@/ui_styles/DefaultStyle'
import LabeledItem from '@/components/ui/LabeledItem.vue'

const props = defineProps({
  label: {
    type: String,
    required: false,
    default: 'Dataset'
  },
  uiStyle: {
    type: AbstractStyle,
    required: false,
    default: DefaultStyle
  },
  myDatasetsOnly: {
    type: Boolean,
    required: false,
    default: false
  }
})

const model = defineModel()
const datasets = ref([])
const datasets_by_id = ref(new Map())

function getLabel(dataset) {
  return `${dataset.dataset_title} ${dataset.dataset_id}`
}

function getEmptyMessage() {
  return props.myDatasetsOnly
    ? 'Your projects have no dataset - either get associated with a project or upload a bedRMod'
    : 'No datasets found'
}

onMounted(() => {
  const query = props.myDatasetsOnly
    ? HTTPSecure('/dataset/list_mine')
    : HTTP.get('/dataset/list_all')
  query
    .then(function (response) {
      datasets.value = response.data
      datasets_by_id.value = datasets.value.reduce((map, dataset) => {
        map[dataset.dataset_id] = dataset
        return map
      }, {})
    })
    .catch((error) => {
      console.log(error)
    })
})
</script>
<template>
  <LabeledItem :label="label" :ui-style="props.uiStyle" class="w-full">
    <Dropdown
      v-model="model"
      :options="datasets"
      filter
      optionValue="dataset_id"
      :optionLabel="getLabel"
      placeholder="Select a dataset"
      :empty-message="getEmptyMessage()"
      class="w-full"
    >
      <template #value="slotProps">
        <div v-if="slotProps.value">
          <div>
            {{ datasets_by_id[slotProps.value].dataset_title }}
            <span class="text-slate-500">[{{ datasets_by_id[slotProps.value].dataset_id }}]</span>
          </div>
        </div>
        <span v-else>
          {{ slotProps.placeholder }}
        </span>
      </template>
      <template #option="slotProps">
        <div class="flex align-items-center">
          <div>
            {{ slotProps.option.dataset_title }}
            <span class="text-slate-500">[{{ slotProps.option.dataset_id }}]</span>
          </div>
        </div>
      </template>
    </Dropdown>
  </LabeledItem>
</template>
