<script setup lang="ts">
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'

import { ref, onMounted } from 'vue'
import { type Project, allProjectsByIdCache } from '@/services/project'
import LocalTime from '@/components/ui/LocalTime.vue'
import ReferenceLinks from '@/components/ui/ReferenceLinks.vue'

const props = defineProps<{
  projectId: string
}>()

const projects = ref<Project[]>([])

onMounted(() => {
  allProjectsByIdCache.getData().then((data) => {
    const project = data.get(props.projectId)
    projects.value = project ? [project] : []
  })
})
</script>

<template>
  <DataTable :value="projects" tableStyle="min-width: 50rem">
    <Column field="project_id" header="SMID" />
    <Column field="project_title" header="Title" />
    <Column field="project_summary" header="Summary" />
    <Column header="Added">
      <template #body="{ data }">
        <LocalTime :epoch="data.date_added" />
      </template>
    </Column>
    <Column header="Published">
      <template #body="{ data }">
        <LocalTime :epoch="data.date_published" :show-time="false" />
      </template>
    </Column>
    <Column field="doi" header="DOI">
      <template #body="{ data }">
        <ReferenceLinks type="DOI" :data="data.doi" />
      </template>
    </Column>
    <Column field="pmid" header="PMID">
      <template #body="{ data }">
        <ReferenceLinks type="PMID" :data="data.pmid" />
      </template>
    </Column>
  </DataTable>
</template>
