<script setup lang="ts">
import { useId } from 'vue'
import { type Technology, type SelectionBase } from '@/services/selection'
import FormFieldWrapper from '@/components/ui/FormFieldWrapper.vue'
import TechnologySelection from '@/components/ui/TechnologySelection.vue'
import { type FormFieldProps, FORM_FIELD_DEFAULTS } from '@/utils/ui-style'
import { type TechnologySelectionExtraProps } from '@/utils/technology'

interface Props extends FormFieldProps, TechnologySelectionExtraProps {
  // choose from these selections (e.g. of a project) instead of all selections
  selections?: SelectionBase[]
}

withDefaults(defineProps<Props>(), FORM_FIELD_DEFAULTS)

const model = defineModel<Technology>()

const emit = defineEmits<{
  (e: 'change', technology: Technology): void
}>()

function change(data: Technology) {
  emit('change', data)
}

const id = useId()
</script>
<template>
  <FormFieldWrapper :field-id="id" :error="error" :ui-style="uiStyle">
    <template v-slot:label>Technology</template>
    <template v-slot:field>
      <TechnologySelection
        v-model="model"
        :id="id"
        :modification-ids="modificationIds"
        :organism-id="organismId"
        :selections="selections"
        :markAsError="!!error"
        :ui-style="uiStyle"
        @change="change"
      />
    </template>
  </FormFieldWrapper>
</template>
