<script setup lang="ts">
/* Use this component with :key="accessToken.email" to make sure that it is mounted freshly on login/logouts */

import { onMounted, ref } from 'vue'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import LocalTime from '@/components/ui/LocalTime.vue'
import { type Project, myProjectsCache } from '@/services/project'

const records = ref<Project[]>([])

onMounted(() => {
  myProjectsCache.getData().then((data) => {
    records.value = [...data]
  })
})
</script>
<template>
  <DataTable :value="records" tableStyle="min-width: 50rem">
    <Column field="project_id" header="SMID" />
    <Column field="project_title" header="Title" />
    <Column header="Added">
      <template #body="{ data }">
        <LocalTime :epoch="data.date_added" />
      </template>
    </Column>
  </DataTable>
</template>
