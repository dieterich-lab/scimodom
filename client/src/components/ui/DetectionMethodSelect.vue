<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { type DetectionMethod, detectionMethodCache } from '@/services/detection_method'
import { GENERIC_FIELD_DEFAULTS, type GenericFieldProps } from '@/utils/ui_style'
import CascadeSelect, { type CascadeSelectChangeEvent } from 'primevue/cascadeselect'
import { type CascadeItem, getOptionsForPrimvueCascadeSelect } from '@/utils/primevue'

const props = withDefaults(defineProps<GenericFieldProps>(), GENERIC_FIELD_DEFAULTS)

const model = defineModel<DetectionMethod>()

const emit = defineEmits<{
  (e: 'change', detectionMethod: DetectionMethod): void
}>()

const options = ref<CascadeItem<DetectionMethod>[]>([])

onMounted(() => {
  detectionMethodCache.getData().then((data) => {
    options.value = getOptionsForPrimvueCascadeSelect(data, ['cls', 'meth'])
  })
})

function change(event: CascadeSelectChangeEvent) {
  emit('change', event.value)
}
</script>
<template>
  <CascadeSelect
    v-model="model"
    :options="options"
    :option-group-children="['cChildren']"
    option-group-label="label"
    :id="id"
    placeholder="Select method"
    option-label="meth"
    :class="markAsError ? props.uiStyle.errorClasses : undefined"
    @change="change"
    :pt="{
      root: { class: 'w-full md:w-full' },
      sublist: { class: 'w-full sm:w-80' }
    }"
    :ptOptions="{ mergeProps: true }"
  />
</template>
