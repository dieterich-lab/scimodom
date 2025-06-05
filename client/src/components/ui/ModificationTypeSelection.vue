<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Select from 'primevue/select'
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
    options.value = getOptionsForPrimvueCascadeSelect(data, ['rna_name', 'modomics_sname'])
  })
})
</script>
<template>
  <Select
    @change="$emit('change', $event.value)"
    v-model="model"
    :options="options"
    :placeholder="placeholder"
    option-label="modomics_sname"
    option-group-children="cChildren"
    option-group-label="label"
    :pt="{
      root: { class: 'w-full md:w-full' }
    }"
    :ptOptions="{ mergeProps: true }"
  />
</template>
