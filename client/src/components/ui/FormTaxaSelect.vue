<script setup lang="ts">
import { useId } from 'vue'
import type { Taxa } from '@/services/taxa'
import FormFieldWrapper from '@/components/ui/FormFieldWrapper.vue'
import TaxaSelect from '@/components/ui/TaxaSelect.vue'
import { type FormFieldProps, FORM_FIELD_DEFAULTS } from '@/utils/ui_style'

withDefaults(defineProps<FormFieldProps>(), FORM_FIELD_DEFAULTS)

const model = defineModel<Taxa>()

const emit = defineEmits<{ (e: 'change', taxa: Taxa): void }>()

function change(taxa: Taxa): void {
  emit('change', taxa)
}

const id = useId()
</script>
<template>
  <FormFieldWrapper :field-id="id" :error="error" :ui-style="uiStyle">
    <template v-slot:label>Organism</template>
    <template v-slot:field>
      <TaxaSelect
        v-model="model"
        :id="id"
        :markAsError="!!error"
        :ui-style="uiStyle"
        @change="change"
      />
    </template>
  </FormFieldWrapper>
</template>
