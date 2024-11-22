<script setup lang="ts">
import { ref, useId, watch } from 'vue'
import RadioButton from 'primevue/radiobutton'
import { ComparisonOperation, type OperationSpec } from '@/utils/comparison'

const props = defineProps<{
  value: OperationSpec
}>()

const label = getLabel()

function getLabel() {
  const suffix = props.value.strandAware ? '' : ' (strand-unaware)'
  switch (props.value.operation) {
    case ComparisonOperation.intersect:
      return `Intersection${suffix}`
    case ComparisonOperation.closest:
      return `Closest${suffix}`
    case ComparisonOperation.subtract:
      return `Difference${suffix}`
  }
}

const model = defineModel<{
  operation: ComparisonOperation
  strandAware: boolean
}>()

const descriptionSuffix = props.value.strandAware
  ? 'on the same strand.'
  : 'without respect to strand.'

const stringValue = getAsString(props.value)
const stringModel = ref<string>('')
const id = useId()

function getAsString(value: OperationSpec): string {
  return `${value.operation}-${value.strandAware}`
}

function change() {
  model.value = props.value
}

watch(
  () => model.value,
  () => {
    stringModel.value = model.value ? getAsString(model.value) : ''
  }
)
</script>
<template>
  <RadioButton v-model="stringModel" :id="id" :value="stringValue" @change="change" />
  <label :for="id" class="ml-2">
    <span class="inline font-bold">{{ label }}</span>
  </label>
  <p class="mt-0 ml-8 text-sm">
    Search for
    <slot></slot>
    {{ descriptionSuffix }}
  </p>
</template>
