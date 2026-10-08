<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Dropdown from 'primevue/dropdown'
import { type ModificationType, modificationTypeSelectionCache } from '@/services/selection'
import { type CascadeItem, getOptionsForPrimvueCascadeSelect } from '@/utils/primevue'

const model = defineModel<ModificationType>()

withDefaults(
  defineProps<{
    placeholder?: string
  }>(),
  {
    placeholder: ''
  }
)

defineEmits<{
  (e: 'change', modificationType: ModificationType): void
}>()

const options = ref<CascadeItem<ModificationType>[]>([])

onMounted(async () => {
  modificationTypeSelectionCache.getData().then((data) => {
    options.value = getOptionsForPrimvueCascadeSelect(data, [
      'rna_type_name',
      'modomics_short_name'
    ])
  })
})
</script>
<template>
  <Dropdown
    @change="$emit('change', $event.value)"
    v-model="model"
    :options="options"
    :placeholder="placeholder"
    option-label="modomics_short_name"
    option-group-children="cChildren"
    option-group-label="label"
    :pt="{
      root: { class: 'w-full md:w-full' }
    }"
    :ptOptions="{ mergeProps: true }"
  />
</template>
