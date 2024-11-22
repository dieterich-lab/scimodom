<script setup lang="ts">
import { ref } from 'vue'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import type { Project } from '@/services/project'
import ProjectSelectionBox from '@/components/ui/ProjectSelectionBox.vue'
import InputText, { type InputTextPassThroughOptions } from 'primevue/inputtext'
import { GENERIC_FIELD_DEFAULTS, type GenericFieldProps } from '@/utils/ui_style'

const props = withDefaults(defineProps<GenericFieldProps>(), GENERIC_FIELD_DEFAULTS)

const model = defineModel<Project>()
const emits = defineEmits<{
  (e: 'change', project: Project): void
}>()
const dialogVisible = ref<boolean>(false)
const smid = ref<string>('')

function openDialog() {
  dialogVisible.value = true
}

function change(project: Project) {
  model.value = project
  smid.value = project.project_id
  dialogVisible.value = false
  emits('change', project)
}

const pt: InputTextPassThroughOptions = {
  root: ({ parent }) => ({
    class: [
      parent.instance.$name === 'InputGroup'
        ? props.uiStyle.inputTextGroupClasses
        : props.uiStyle.inputTextDefaultClasses
    ]
  })
}
</script>
<template>
  <div class="flex flex-row">
    <InputText
      :id="id"
      v-model="smid"
      type="text"
      placeholder="XXXXXXXX"
      :disabled="true"
      :pt="pt"
      :ptOptions="{ mergeProps: true }"
      :class="markAsError ? props.uiStyle.errorClasses : undefined"
      @update="change"
    />
    <Button
      class="ml-4 self-center"
      label="Select a project"
      icon="pi pi-search-plus"
      @click="openDialog"
    />
    <Dialog
      v-model:visible="dialogVisible"
      header="Available projects"
      :breakpoints="{ '960px': '75vw', '640px': '90vw' }"
      :pt="{
        root: { class: 'w-fit' },
        closeButton: { class: 'focus:ring-secondary-400 dark:focus:ring-secondary-300' }
      }"
      :ptOptions="{ mergeProps: true }"
      :modal="true"
    >
      <ProjectSelectionBox @change="change" />
    </Dialog>
  </div>
</template>
