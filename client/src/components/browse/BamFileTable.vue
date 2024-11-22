<script setup lang="ts">
import { ref } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import { useAccessToken } from '@/stores/AccessToken'
import LocalTime from '@/components/ui/LocalTime.vue'
import { useDialogState, DIALOG } from '@/stores/DialogState'
import { mayChangeDataset } from '@/services/user'
import {
  type BamFile,
  deleteBamFile,
  getBamFileDownLoadURL,
  getBamFilesByDatasetId
} from '@/services/bamfile'
import { trashRequestErrors } from '@/services/API'

const props = defineProps({
  datasetId: {
    type: String,
    required: true
  },
  datasetTitle: {
    type: String,
    required: true
  }
})

const accessToken = useAccessToken()
const dialogState = useDialogState()

const mayChange = ref<boolean>(false)
const bamFiles = ref<BamFile[]>([])

function refreshData() {
  if (accessToken.token !== null) {
    mayChangeDataset(props.datasetId, dialogState)
      .then((x) => {
        mayChange.value = x
      })
      .catch((e) => {
        mayChange.value = false
        trashRequestErrors(e)
      })
  }
  getBamFilesByDatasetId(props.datasetId, dialogState)
    .then((data) => (bamFiles.value = data))
    .catch((e) => trashRequestErrors(e))
}

function askToDelete(name: string) {
  dialogState.message = `Really delete '${name}' belonging dataset '${props.datasetTitle}' (${props.datasetId})?`
  dialogState.confirmCallback = () => deleteIt(props.datasetId, name)
  dialogState.state = DIALOG.CONFIRM
}

function deleteIt(datasetId: string, name: string) {
  deleteBamFile(datasetId, name, dialogState)
    .catch((e) => trashRequestErrors(e))
    .finally(() => refreshData())
}

function getDownLoadURL(bamFile: BamFile) {
  return getBamFileDownLoadURL(props.datasetId, bamFile.original_file_name)
}

refreshData()
</script>
<template>
  <DataTable :value="bamFiles" tableStyle="min-width: 50rem">
    <Column field="original_file_name" header="Name" />
    <Column header="Last changed">
      <template #body="{ data }">
        <LocalTime :epoch="data.mtime_epoch" />
      </template>
    </Column>
    <Column field="size_in_bytes" header="Bytes" />
    <Column key="download">
      <template #body="{ data }">
        <a :href="getDownLoadURL(data)">
          <Button text severity="secondary" label="Download" />
        </a>
      </template>
    </Column>
    <Column v-if="mayChange" key="actions">
      <template #body="{ data }">
        <Button
          icon="pi pi-trash"
          outlined
          rounded
          severity="danger"
          @click="askToDelete(data.original_file_name)"
        />
      </template>
    </Column>
  </DataTable>
</template>
