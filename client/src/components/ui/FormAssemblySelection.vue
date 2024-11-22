<script setup lang="ts">
import { useId } from 'vue'
import { type Assembly } from '@/services/assembly'
import FormFieldWrapper from '@/components/ui/FormFieldWrapper.vue'
import AssemblySelection from '@/components/ui/AssemblySelection.vue'
import { type FormFieldProps, FORM_FIELD_DEFAULTS } from '@/utils/ui_style'

interface Props extends FormFieldProps {
  taxaId?: number
}

withDefaults(defineProps<Props>(), FORM_FIELD_DEFAULTS)

const model = defineModel<Assembly>()

const emit = defineEmits<{ (e: 'change', assembly: Assembly): void }>()

function change(assembly: Assembly): void {
  emit('change', assembly)
}

const id = useId()
</script>
<template>
  <FormFieldWrapper :field-id="id" :error="error" :ui-style="uiStyle">
    <template v-slot:label>Assembly</template>
    <template v-slot:field>
      <AssemblySelection
        v-model="model"
        :id="id"
        :taxa-id="taxaId"
        :markAsError="!!error"
        :ui-style="uiStyle"
        @change="change"
      />
    </template>
  </FormFieldWrapper>
</template>
