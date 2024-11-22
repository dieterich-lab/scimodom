<script setup lang="ts">
import { useId } from 'vue'
import type { Project } from '@/services/project'
import FormFieldWrapper from '@/components/ui/FormFieldWrapper.vue'
import ProjectSelection from '@/components/ui/ProjectSelection.vue'
import { FORM_FIELD_DEFAULTS, type FormFieldProps } from '@/utils/ui_style'

withDefaults(defineProps<FormFieldProps>(), FORM_FIELD_DEFAULTS)

const model = defineModel<Project>()

const emit = defineEmits<{ (e: 'change', project: Project): void }>()

function change(project: Project) {
  emit('change', project)
}

const id = useId()
</script>
<template>
  <FormFieldWrapper :field-id="id" :error="error" :ui-style="uiStyle">
    <template v-slot:label>Sci-ModoM ID (SMID)</template>
    <template v-slot:field>
      <ProjectSelection
        v-model="model"
        :id="id"
        :markAsError="!!error"
        :ui-style="uiStyle"
        @change="change"
      />
    </template>
  </FormFieldWrapper>
</template>
