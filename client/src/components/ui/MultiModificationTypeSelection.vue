<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import MultiSelect from 'primevue/multiselect'
import { type ModificationType, getModificationTypesByRnaType } from '@/services/selection'
import { type GenericFieldProps, GENERIC_FIELD_DEFAULTS } from '@/utils/ui-style'

export interface MultiModificationTypeSelectionExtraProps {
  rnaType?: string
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
  () => props.rnaType,
  () => {
    if (props.rnaType) {
      getModificationTypesByRnaType(props.rnaType).then((data) => {
        options.value = [...data]
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
