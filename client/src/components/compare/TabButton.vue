<script setup lang="ts">
import { computed } from 'vue'
import Button from 'primevue/button'

const props = defineProps<{
  tabIndex: number
}>()
const model = defineModel<number>()
const label = String(props.tabIndex + 1)
const outlined = computed(() => model.value !== props.tabIndex)

function click() {
  model.value = props.tabIndex
}

const buttonPt = {
  root: () => ({
    class: ['h-12 w-12 p-0 shadow']
  })
}
</script>
<template>
  <Button
    @click="click"
    rounded
    :label="label"
    severity="secondary"
    :outlined="outlined"
    :pt="buttonPt"
    :ptOptions="{ mergeProps: true }"
  />
</template>
