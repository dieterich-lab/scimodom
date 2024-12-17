<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useDialogState } from '@/stores/DialogState'
import { type Assembly, getAssembliesByTaxaId } from '@/services/assembly'
import { type GenericFieldProps, GENERIC_FIELD_DEFAULTS } from '@/utils/ui_style'
import Dropdown, { type DropdownChangeEvent } from 'primevue/dropdown'
import { trashRequestErrors } from '@/services/API'

interface Props extends GenericFieldProps {
  taxaId?: number
}

const props = withDefaults(defineProps<Props>(), GENERIC_FIELD_DEFAULTS)

const model = defineModel<Assembly>()

const emit = defineEmits<{
  (e: 'change', rnaType: Assembly): void
}>()

const dialogState = useDialogState()

const options = ref<Assembly[]>([])
const disabled = computed(() => !options.value?.length)

watch(
  () => props.taxaId,
  () => {
    if (props.taxaId) {
      getAssembliesByTaxaId(props.taxaId, dialogState)
        .then((data) => {
          options.value = data
        })
        .catch((e) => {
          options.value = []
          trashRequestErrors(e)
        })
    } else {
      options.value = []
    }
  },
  { immediate: true }
)

function change(event: DropdownChangeEvent) {
  emit('change', event.value)
}
</script>
<template>
  <Dropdown
    v-model="model"
    :id="id"
    :options="options"
    option-label="name"
    placeholder="Select assembly"
    :class="markAsError ? props.uiStyle.errorClasses : undefined"
    :disabled="disabled"
    @change="change"
  />
</template>
