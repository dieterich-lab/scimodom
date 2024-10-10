<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import { type Project, myProjectsCache } from '@/services/project'
import LocalTime from '@/components/ui/LocalTime.vue'
import ReferenceLinks from '@/components/ui/ReferenceLinks.vue'

defineEmits<{
  (e: 'change', value: Project): void
}>()
const records = ref<Project[]>([])

onMounted(() => {
  myProjectsCache.getData().then((data) => {
    records.value = [...data]
  })
})
</script>

<template>
  <DataTable :value="records">
    <Column style="width: 5rem" header="Select">
      <template #body="slotProps">
        <Button
          icon="pi pi-plus"
          outlined
          rounded
          severity="secondary"
          @click="$emit('change', slotProps.data)"
        ></Button>
      </template>
    </Column>
    <Column field="project_id" header="SMID"></Column>
    <Column field="project_title" header="Title"></Column>
    <Column field="project_summary" header="Summary"></Column>
    <Column header="Added">
      <template #body="{ data }">
        <LocalTime :epoch="data.date_added" />
      </template>
    </Column>
    <Column field="contact_name" header="Contact"></Column>
    <Column field="contact_institution" header="Institution"></Column>
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
