<script setup>
import { ref } from 'vue'
import DataTable from 'primevue/datatable'
import Button from 'primevue/button'
import { useAccessToken } from '@/stores/AccessToken'
import { HTTP, HTTPSecure, getApiUrl } from '@/services/API'
import LocalTime from '@/components/ui/LocalTime.vue'
import { useDialogState, DIALOG } from '@/stores/DialogState'
import { handleRequestWithErrorReporting } from '@/utils/request'

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

const mayChange = ref(false)
const bamFiles = ref([])

function refreshData() {
  if (accessToken.token !== null) {
    HTTPSecure.get(`/user/may_change_dataset/${props.datasetId}`)
      .then((response) => {
        mayChange.value = response.data.write_access
      })
      .catch(() => {})
  }
  HTTP.get(`/bam_file/all/${props.datasetId}`).then((response) => {
    bamFiles.value = response.data
  })
}

function askToDelete(name) {
  dialogState.message = `Really delete '${name}' belonging dataset '${props.datasetTitle}' (${props.datasetId})?`
  dialogState.confirmCallback = () => deleteBamFile(props.datasetId, name)
  dialogState.state = DIALOG.CONFIRM
}

function deleteBamFile(datasetId, name) {
  const cookedName = encodeURI(name)
  handleRequestWithErrorReporting(
    HTTPSecure.delete(`/bam_file/${datasetId}/${cookedName}`),
    'Failed to delete BAM file',
    dialogState
  ).then(() => refreshData())
}

function getDownLoadURL(bam_file) {
  const cookedName = encodeURI(bam_file.original_file_name)
  return getApiUrl(`bam_file/${props.datasetId}/${cookedName}`)
}

refreshData()
</script>
<template>
  <DataTable :value="bamFiles" tableStyle="min-width: 50rem">
    <Column field="original_file_name" header="Name" />
    <Column header="Last changed" #body="{ data }">
      <LocalTime :epoch="data.mtime_epoch" />
    </Column>
    <Column field="size_in_bytes" header="Bytes" />
    <Column #body="{ data }" key="download">
      <a :href="getDownLoadURL(data)">
        <Button text severity="secondary" label="Download" />
      </a>
    </Column>
    <Column v-if="mayChange" #body="{ data }" key="actions">
      <Button
        icon="pi pi-trash"
        outlined
        rounded
        severity="danger"
        @click="askToDelete(data.original_file_name)"
      />
    </Column>
  </DataTable>
</template>
