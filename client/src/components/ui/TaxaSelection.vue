<script setup lang="ts">
import { ref, watch } from 'vue'
import { type Taxa } from '@/services/taxa'
import { taxaSelectionCache } from '@/services/selection'
import CascadeSelect, { type CascadeSelectChangeEvent } from 'primevue/cascadeselect'
import { type CascadeItem, getOptionsForPrimvueCascadeSelect } from '@/utils/primevue'
import { GENERIC_FIELD_DEFAULTS, type GenericFieldProps } from '@/utils/ui_style'

interface Props extends GenericFieldProps {
  modificationIds?: number[]
  placeholder?: string
  disabled?: boolean
}
const props = withDefaults(defineProps<Props>(), {
  ...GENERIC_FIELD_DEFAULTS,
  placeholder: 'Select organism',
  disabled: false
})

const model = defineModel<Taxa>()

const emit = defineEmits<{
  (e: 'change', taxa: Taxa): void
}>()

const options = ref<CascadeItem<Taxa>[]>([])

watch(
  () => props.modificationIds,
  () => {
    taxaSelectionCache.getData().then((data) => {
      const rawOptions = data.map((x) => {
        return { ...x, kingdom: x.kingdom ? x.kingdom : x.domain }
      })
      options.value = getOptionsForPrimvueCascadeSelect(rawOptions, ['kingdom', 'taxa_sname'])
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
    v-model="model"
    :id="id"
    :options="options"
    optionLabel="taxa_sname"
    optionGroupLabel="label"
    :optionGroupChildren="['cChildren']"
    :placeholder="placeholder"
    :pt="{
      root: { class: 'w-full md:w-full' }
    }"
    :ptOptions="{ mergeProps: true }"
    :class="markAsError ? props.uiStyle.errorClasses : undefined"
    :disabled="disabled"
    @change="change"
  />
</template>
