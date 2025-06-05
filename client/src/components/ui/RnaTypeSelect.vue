<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { type RnaType, rnaTypeCache } from '@/services/rna_type'
import { type GenericFieldProps, GENERIC_FIELD_DEFAULTS } from '@/utils/ui_style'
import Select, { type SelectChangeEvent } from 'primevue/select'

const props = withDefaults(defineProps<GenericFieldProps>(), GENERIC_FIELD_DEFAULTS)

const model = defineModel<RnaType>()

const emit = defineEmits<{
  (e: 'change', rnaType: RnaType): void
}>()

const rnaTypes = ref<RnaType[]>([])

onMounted(() => {
  rnaTypeCache.getData().then((data) => {
    rnaTypes.value = [...data]
  })
})

function change(event: SelectChangeEvent) {
  emit('change', event.value)
}
</script>

<template>
  <Select
    v-model="model"
    :id="id"
    :options="rnaTypes"
    option-label="label"
    placeholder="Select RNA type"
    :class="markAsError ? props.uiStyle.errorClasses : undefined"
    @change="change"
  />
</template>
