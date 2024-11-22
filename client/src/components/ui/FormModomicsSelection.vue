<script setup lang="ts">
import { useId } from 'vue'
import { type Modomics } from '@/services/modomics'
import FormFieldWrapper from '@/components/ui/FormFieldWrapper.vue'
import ModomicsSelection from '@/components/ui/ModomicsSelection.vue'
import { type FormFieldProps, FORM_FIELD_DEFAULTS } from '@/utils/ui_style'

withDefaults(defineProps<FormFieldProps>(), FORM_FIELD_DEFAULTS)

const model = defineModel<Modomics>()

const emit = defineEmits<{ (e: 'change', modomics: Modomics): void }>()

function change(modomics: Modomics): void {
  emit('change', modomics)
}

const id = useId()
</script>
<template>
  <FormFieldWrapper :field-id="id" :error="error" :ui-style="uiStyle">
    <template v-slot:label>Modification</template>
    <template v-slot:field>
      <ModomicsSelection
        v-model="model"
        :id="id"
        :markAsError="!!error"
        :ui-style="uiStyle"
        @change="change"
      />
    </template>
  </FormFieldWrapper>
</template>
