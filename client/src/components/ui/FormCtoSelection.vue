<script setup lang="ts">
import { useId } from 'vue'
import { type Cto } from '@/services/selection'
import FormFieldWrapper from '@/components/ui/FormFieldWrapper.vue'
import CtoSelection from '@/components/ui/CtoSelection.vue'
import { type FormFieldProps, FORM_FIELD_DEFAULTS } from '@/utils/ui_style'

interface Props extends FormFieldProps {
  modificationIds?: number[]
}

withDefaults(defineProps<Props>(), FORM_FIELD_DEFAULTS)

const model = defineModel<Cto>()

const emit = defineEmits<{ (e: 'change', cto: Cto): void }>()

function change(cto: Cto): void {
  emit('change', cto)
}

const id = useId()
</script>
<template>
  <FormFieldWrapper :field-id="id" :error="error" :ui-style="uiStyle">
    <template v-slot:label>Organism</template>
    <template v-slot:field>
      <CtoSelection
        v-model="model"
        :id="id"
        :modification-ids="modificationIds"
        :markAsError="!!error"
        :ui-style="uiStyle"
        @change="change"
      />
    </template>
  </FormFieldWrapper>
</template>
