<script setup lang="ts">
import { useId } from 'vue'
import type { ModificationType } from '@/services/selection'
import FormFieldWrapper from '@/components/ui/FormFieldWrapper.vue'
import MultiModificationTypeSelection, {
  type MultiModificationTypeSelectionExtraProps
} from '@/components/ui/MultiModificationTypeSelection.vue'
import { FORM_FIELD_DEFAULTS, type FormFieldProps } from '@/utils/ui_style'

interface Props extends FormFieldProps, MultiModificationTypeSelectionExtraProps {}

withDefaults(defineProps<Props>(), FORM_FIELD_DEFAULTS)

const model = defineModel<ModificationType[]>()

const emit = defineEmits<{
  (e: 'change', data: ModificationType[]): void
}>()

function change(modificationTypes: ModificationType[]): void {
  emit('change', modificationTypes)
}

const id = useId()
</script>
<template>
  <FormFieldWrapper :field-id="id" :error="error" :ui-style="uiStyle">
    <template v-slot:label>Modifications</template>
    <template v-slot:field>
      <MultiModificationTypeSelection
        v-model="model"
        :rna-type-name="rnaTypeName"
        :id="id"
        :markAsError="!!error"
        :ui-style="uiStyle"
        @change="change"
      />
    </template>
  </FormFieldWrapper>
</template>
