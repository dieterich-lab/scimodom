<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import MultiSelect from 'primevue/multiselect'
import {
  type ModificationType,
  type SelectionBase,
  getModificationTypesByRnaType,
  resolveSelections
} from '@/services/selection'
import { type GenericFieldProps, GENERIC_FIELD_DEFAULTS } from '@/utils/ui-style'

export interface MultiModificationTypeSelectionExtraProps {
  rnaType?: string
  // choose from these selections (e.g. of a project) instead of all selections
  selections?: SelectionBase[]
}
interface Props extends GenericFieldProps, MultiModificationTypeSelectionExtraProps {}

const props = withDefaults(defineProps<Props>(), GENERIC_FIELD_DEFAULTS)

const model = defineModel<ModificationType[]>()

defineEmits<{
  (e: 'change', data: ModificationType[]): void
}>()

const options = ref<ModificationType[]>([])

const disabled = computed(() => !options.value?.length)

watch(
  () => [props.rnaType, props.selections],
  () => {
    const rnaType = props.rnaType
    if (rnaType) {
      resolveSelections(props.selections).then((available) => {
        options.value = getModificationTypesByRnaType(available, rnaType)
      })
    } else {
      options.value = []
    }
  },
  { immediate: true }
)
</script>
<template>
  <MultiSelect
    v-model="model"
    :id="id"
    :options="options"
    optionLabel="modomics_short_name"
    placeholder="Select modification"
    :disabled="disabled"
    :class="markAsError ? props.uiStyle.errorClasses : undefined"
    @change="$emit('change', $event.value)"
  />
</template>
