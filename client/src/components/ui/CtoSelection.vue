<script setup lang="ts">
import { ref, watch } from 'vue'
import CascadeSelect, { type CascadeSelectChangeEvent } from 'primevue/cascadeselect'
import {
  type Cto,
  type SelectionBase,
  getCtos,
  getCtosByModificationIds,
  resolveSelections
} from '@/services/selection'
import { type CascadeItem, getOptionsForPrimvueCascadeSelect } from '@/utils/primevue'

const props = withDefaults(
  defineProps<{
    placeholder?: string
    error?: string
    modificationIds?: number[]
    // choose from these selections (e.g. of a project) instead of all selections
    selections?: SelectionBase[]
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
  () => [props.modificationIds, props.selections],
  () => {
    resolveSelections(props.selections).then((available) => {
      const ctos = props.modificationIds
        ? getCtosByModificationIds(available, props.modificationIds)
        : getCtos(available)
      const rawOptions = ctos.map((x) => {
        return { ...x, kingdom: x.kingdom ? x.kingdom : x.domain }
      })
      options.value = getOptionsForPrimvueCascadeSelect(rawOptions, [
        'kingdom',
        'taxa_short_name',
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
