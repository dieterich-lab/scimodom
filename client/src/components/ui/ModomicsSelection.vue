<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { type Modomics, modomicsCache } from '@/services/modomics'
import { GENERIC_FIELD_DEFAULTS, type GenericFieldProps } from '@/utils/ui_style'
import Dropdown, { type DropdownChangeEvent } from 'primevue/dropdown'

const props = withDefaults(defineProps<GenericFieldProps>(), GENERIC_FIELD_DEFAULTS)

const model = defineModel<Modomics>()

const emit = defineEmits<{
  (e: 'change', modomics: Modomics): void
}>()

const options = ref<Modomics[]>([])

onMounted(() => {
  modomicsCache.getData().then((data) => {
    options.value = [...data]
  })
})

function change(event: DropdownChangeEvent) {
  emit('change', event.value)
}
</script>
<template>
  <Dropdown
    v-model="model"
    :id="id"
    :options="options"
    option-label="modomics_sname"
    placeholder="Select modification"
    :class="markAsError ? props.uiStyle.errorClasses : undefined"
    @change="change"
  />
</template>
