<script setup lang="ts">
import { useId } from 'vue'
import type { RnaType } from '@/services/rna_type'
import FormFieldWrapper from '@/components/ui/FormFieldWrapper.vue'
import RnaTypeSelection from '@/components/ui/RnaTypeSelection.vue'
import { type FormFieldProps, FORM_FIELD_DEFAULTS } from '@/utils/ui_style'

withDefaults(defineProps<FormFieldProps>(), FORM_FIELD_DEFAULTS)

const model = defineModel<RnaType>()

const emit = defineEmits<{ (e: 'change', rnaType: RnaType): void }>()

function change(rnaType: RnaType): void {
  emit('change', rnaType)
}

const id = useId()
</script>
<template>
  <FormFieldWrapper :field-id="id" :error="error" :ui-style="uiStyle">
    <template v-slot:label>RNA type</template>
    <template v-slot:field>
      <RnaTypeSelection
        v-model="model"
        :id="id"
        :markAsError="!!error"
        :ui-style="uiStyle"
        @change="change"
      />
    </template>
  </FormFieldWrapper>
</template>
