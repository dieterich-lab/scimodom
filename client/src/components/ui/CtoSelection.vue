<script setup lang="ts">
import { ref, watch } from 'vue'
import CascadeSelect, { type CascadeSelectChangeEvent } from 'primevue/cascadeselect'
import { type Cto, getCtosByModificationIds, ctoSelectionCache } from '@/services/selection'
import { type CascadeItem, getOptionsForPrimvueCascadeSelect } from '@/utils/primevue'

const props = withDefaults(
  defineProps<{
    placeholder?: string
    error?: string
    modificationIds?: number[]
    cls?: string
    disabled?: boolean
  }>(),
  {
    placeholder: 'Select organism',
    disabled: false
  }
)

const model = defineModel<Cto>()

const emit = defineEmits<{
  (e: 'change', cto: Cto): void
}>()

const options = ref<CascadeItem<Cto>[]>([])

watch(
  () => props.modificationIds,
  () => {
    const p = props.modificationIds
      ? getCtosByModificationIds(props.modificationIds)
      : ctoSelectionCache.getData()
    p.then((data) => {
      const rawOptions = data.map((x) => {
        return { ...x, kingdom: x.kingdom ? x.kingdom : x.domain }
      })
      options.value = getOptionsForPrimvueCascadeSelect(rawOptions, [
        'kingdom',
        'taxa_sname',
        'cto'
      ])
    })
  },
  { immediate: true }
)

function change(data: CascadeSelectChangeEvent) {
  emit('change', data.value)
}
</script>
<template>
  <CascadeSelect
    @change="change"
    v-model="model"
    :options="options"
    optionLabel="cto"
    optionGroupLabel="label"
    :optionGroupChildren="['cChildren', 'cChildren']"
    :placeholder="placeholder"
    :pt="{
      root: { class: 'w-full md:w-full' }
    }"
    :ptOptions="{ mergeProps: true }"
    :class="cls"
    :disabled="disabled"
  />
</template>
