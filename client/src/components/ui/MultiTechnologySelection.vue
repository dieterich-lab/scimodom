<script setup lang="ts">
import { ref, watch } from 'vue'
import TreeSelect from 'primevue/treeselect'
import {
  type Technology,
  getTechnologiesByModificationIdsAndOrganismId,
  resolveSelections
} from '@/services/selection'
import { type GenericFieldProps, GENERIC_FIELD_DEFAULTS } from '@/utils/ui-style'
import {
  type TechnologySelectionExtraProps,
  TECHNOLOGY_SELECTION_DEFAULTS
} from '@/utils/technology'
import {
  getOptionsForPrimvueTreeSelect,
  getResultsFromTreeNodeChangeEvent,
  type TreeNode
} from '@/utils/primevue'

export interface Props extends GenericFieldProps, TechnologySelectionExtraProps {}

const props = withDefaults(defineProps<Props>(), {
  ...GENERIC_FIELD_DEFAULTS,
  ...TECHNOLOGY_SELECTION_DEFAULTS
})

const model = defineModel<Technology[]>()
const rawModel = ref()

const emit = defineEmits<{
  (e: 'change', technologies: Technology[]): void
}>()

const rawOptions = ref<Technology[]>([])
const options = ref<TreeNode[]>([])

watch(
  () => [props.modificationIds, props.organismId],
  () => {
    const { modificationIds, organismId } = props
    if (modificationIds && organismId) {
      resolveSelections()
        .then((available) => {
          const data = getTechnologiesByModificationIdsAndOrganismId(
            available,
            modificationIds,
            organismId
          )
          rawOptions.value = data
          options.value = getOptionsForPrimvueTreeSelect(data, ['meth', 'tech'], 'technology_id')
        })
        .catch(() => {
          rawOptions.value = []
          options.value = []
        })
    } else {
      rawOptions.value = []
      options.value = []
    }
  },
  { immediate: true }
)

watch(
  () => model.value,
  () => {
    if (!model.value?.length) {
      rawModel.value = undefined
    }
  }
)

function change(value: string[]) {
  const result = getResultsFromTreeNodeChangeEvent(value, rawOptions.value, 'technology_id')
  model.value = result
  emit('change', result)
}
</script>
<template>
  <TreeSelect
    v-model="rawModel"
    :id="id"
    :options="options"
    selectionMode="checkbox"
    :metaKeySelection="false"
    :placeholder="placeholder"
    :class="markAsError ? props.uiStyle.errorClasses : undefined"
    :pt="{
      root: { class: 'w-full md:w-full' }
    }"
    :ptOptions="{ mergeProps: true }"
    :disabled="disabled"
    @change="change"
  />
</template>
