<script setup>
import { ref, inject, onMounted } from 'vue'
import { splitStr } from '@/utils/index.js'
import { loadProjects } from '@/services/project'

const dialogRef = inject('dialogRef')
const records = ref()

onMounted(() => {
  // only list my projects
  loadProjects(records, null, true)
})

function selectProject(data) {
  dialogRef.value.close(data)
}
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
          @click="selectProject(slotProps.data)"
        ></Button>
      </template>
    </Column>
    <Column field="project_id" header="SMID"></Column>
    <Column field="project_title" header="Title"></Column>
    <Column field="project_summary" header="Summary"></Column>
    <Column field="date_added" header="Added"></Column>
    <Column field="contact_name" header="Contact"></Column>
    <Column field="contact_institution" header="Institution"></Column>
    <Column field="doi" header="DOI">
      <template #body="{ data }">
        <ul class="list-none" v-for="doi in splitStr(data.doi)">
          <a class="text-secondary-500 pr-12" target="_blank" :href="`https://doi.org/${doi}`">{{
            doi
          }}</a>
        </ul>
      </template>
    </Column>
    <Column field="pmid" header="PMID">
      <template #body="{ data }">
        <ul class="list-none" v-for="pmid in splitStr(data.pmid)">
          <a
            class="text-secondary-500"
            target="_blank"
            :href="`http://www.ncbi.nlm.nih.gov/pubmed/${pmid}`"
            >{{ pmid }}</a
          >
        </ul>
      </template>
    </Column>
  </DataTable>
</template>
