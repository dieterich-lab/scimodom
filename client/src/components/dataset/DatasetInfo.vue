<script setup>
import Dialog from 'primevue/dialog'
import SubTitle from '@/components/ui/SubTitle.vue'
import ProjectDetailsTable from '@/components/dataset/ProjectDetailsTable.vue'
import BamFileTable from '@/components/dataset/BamFileTable.vue'

const props = defineProps({
  dataset: {
    type: Object,
    required: true
  }
})
const modelVisible = defineModel('visible')

const header = () => {
  return 'Information for dataset "' + props.dataset.dataset_title + '"'
}
</script>

<template>
  <Dialog
    v-model:visible="modelVisible"
    :header="header()"
    :modal="true"
    :pt="{
      root: { class: 'w-fit' },
      closeButton: { class: 'focus:ring-secondary-400 dark:focus:ring-secondary-300' }
    }"
    :ptOptions="{ mergeProps: true }"
  >
    <div>
      <SubTitle :small="true">This dataset is part of the following project:</SubTitle>
      <ProjectDetailsTable :project-id="dataset.project_id" />
      <div class="flex mt-6">
        <SubTitle :small="true">The following BAM files are attached to this dataset:</SubTitle>
      </div>
      <BamFileTable :dataset-id="dataset.dataset_id" :dataset-title="dataset.dataset_title" />
    </div>
  </Dialog>
</template>
