<script setup lang="ts">
import { ref } from 'vue'
import FormTextInput from '@/components/ui/FormTextInput.vue'
import type { Project } from '@/services/project'
import ProjectSelectionBox from '@/components/project/ProjectSelectionBox.vue'

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
</script>
<template>
  <FormTextInput v-model="smid" :disabled="true" placeholder="XXXXXXXX">
    Sci-ModoM ID (SMID)
  </FormTextInput>
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
</template>
