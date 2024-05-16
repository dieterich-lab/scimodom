<script setup>
import Dialog from 'primevue/dialog'
import ProjectDetailsTable from '@/components/dataset/ProjectDetailsTable.vue'
import BamFileTable from '@/components/dataset/BamFileTable.vue'

const props = defineProps({
  dataset: {
    type: Object,
    required: true
  }
})

const modelVisible = defineModel('visible')
</script>
<template>
  <Dialog
    v-model:visible="modelVisible"
    header="Project information"
    :modal="true"
    :pt="{
      root: { class: 'w-fit' },
      closeButton: { class: 'focus:ring-secondary-400 dark:focus:ring-secondary-300' }
    }"
    :ptOptions="{ mergeProps: true }"
  >
    <div>
      <div class="flex space-x-12 mb-6 whitespace-pre-line">
        This dataset is part of the following project:
      </div>
      <ProjectDetailsTable :project-id="dataset.project_id" />
      <div class="flex space-x-12 mt-6 mb-6 whitespace-pre-line">
        The following BAM/BAI files are attached to the dataset:
      </div>
      <BamFileTable :dataset-id="dataset.dataset_id" :dataset-title="dataset.dataset_title" />
    </div>
  </Dialog>
</template>
