<script setup lang="ts">
import { ref } from 'vue'
import Button from 'primevue/button'
import { storeToRefs } from 'pinia'
import InstructionsText from '@/components/ui/InstructionsText.vue'
import DatasetSelection from '@/components/ui/DatasetSelection.vue'
import FileUpload from '@/components/upload/FileUpload.vue'
import UploadCard from '@/components/upload/UploadCard.vue'
import LabeledItem from '@/components/ui/LabeledItem.vue'
import { useUploadManager } from '@/stores/UploadManager.js'
import type { Dataset } from '@/services/dataset'

const ILLEGAL_FILENAME_CHAR_REGEXP = /[^a-zA-Z0-9.,_-]/g

const dataset = ref<Dataset>()
const uploadManager = useUploadManager()
const { uploads } = storeToRefs(uploadManager)

async function scheduleUpload(file: File) {
  if (dataset.value) {
    const d = dataset.value
    const cleaned_file_name = encodeURI(file.name.replace(ILLEGAL_FILENAME_CHAR_REGEXP, '_'))
    const info = `${d.dataset_title} [${d.dataset_id}]`
    uploadManager.schedule(file, `/bam_file/${d.dataset_id}/${cleaned_file_name}`, info)
  } else {
    console.log('Tried to schedule BAM upload without a dataset - that should never happen!')
  }
}
</script>
<template>
  <InstructionsText> Attach BAM files to an existing dataset. </InstructionsText>
  <div class="grid gap-y-2 gap-x-8">
    <LabeledItem label="Dataset" class="w-full">
      <DatasetSelection v-model="dataset" :my-datasets-only="true" />
    </LabeledItem>

    <FileUpload
      v-if="dataset !== undefined"
      label="BAM/BAI files"
      accept="application/octet-stream,.bam,.bai"
      :multiple="true"
      :handle-file="scheduleUpload"
    />
    <div v-else>
      <p>Select a dataset and upload files.</p>
    </div>

    <div class="underline mt-4">Uploads</div>
    <div v-if="uploads.length === 0">
      <p>(No recent uploads)</p>
    </div>
    <div v-for="upload in uploads" v-bind:key="upload.id">
      <UploadCard :upload="upload" :key="`${upload.id}/${upload.state.toString()}`" />
    </div>
  </div>
</template>
