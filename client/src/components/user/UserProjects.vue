<script setup>
/* Use this component with :key="accessToken.email" to make sure that it is mounted freshly on login/logouts */

import { onMounted, ref } from 'vue'
import LocalTime from '@/components/ui/LocalTime.vue'
import { loadProjects } from '@/services/project'

const records = ref()

onMounted(() => {
  loadProjects(records, null, true)
})
</script>
<template>
  <DataTable :value="records" tableStyle="min-width: 50rem">
    <Column field="project_id" header="SMID" />
    <Column field="project_title" header="Title" />
    <Column header="Added" #body="{ data }">
      <LocalTime :epoch="data.date_added" />
    </Column>
  </DataTable>
</template>
