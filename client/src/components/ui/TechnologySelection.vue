<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import CascadeSelect, { type CascadeSelectChangeEvent } from 'primevue/cascadeselect'
import {
  type Technology,
  type SelectionBase,
  getTechnologiesByModificationIdsAndOrganismId,
  resolveSelections
} from '@/services/selection'
import { type GenericFieldProps, GENERIC_FIELD_DEFAULTS } from '@/utils/ui-style'
import {
  type TechnologySelectionExtraProps,
  TECHNOLOGY_SELECTION_DEFAULTS
} from '@/utils/technology'
import { type CascadeItem, getOptionsForPrimvueCascadeSelect } from '@/utils/primevue'

export interface Props extends GenericFieldProps, TechnologySelectionExtraProps {
  // choose from these selections (e.g. of a project) instead of all selections
  selections?: SelectionBase[]
}

const props = withDefaults(defineProps<Props>(), {
  ...GENERIC_FIELD_DEFAULTS,
  ...TECHNOLOGY_SELECTION_DEFAULTS
})

const model = defineModel<Technology>()

const emit = defineEmits<{
  (e: 'change', technology: Technology): void
}>()

const options = ref<CascadeItem<Technology>[]>([])

const realDisabled = computed(() => props.disabled || !options.value?.length)

watch(
  () => [props.modificationIds, props.organismId, props.selections],
  () => {
    const { modificationIds, organismId } = props
    if (modificationIds && organismId) {
      resolveSelections(props.selections).then((available) => {
        options.value = getOptionsForPrimvueCascadeSelect(
          getTechnologiesByModificationIdsAndOrganismId(available, modificationIds, organismId),
          ['meth', 'tech']
        )
      })
    } else {
      options.value = []
    }
  },
  { immediate: true }
)

function change(event: CascadeSelectChangeEvent) {
  emit('change', event.value)
}
</script>
<template>
  <CascadeSelect
    v-model="model"
    :id="id"
    :options="options"
    optionLabel="tech"
    optionGroupLabel="label"
    :optionGroupChildren="['cChildren']"
    :placeholder="placeholder"
    :class="markAsError ? props.uiStyle.errorClasses : undefined"
    :disabled="realDisabled"
    :pt="{ root: { class: 'w-full md:w-full' } }"
    :ptOptions="{ mergeProps: true }"
    @change="change"
  />
</template>
