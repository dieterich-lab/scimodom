<script setup>
import DataTable from 'primevue/datatable'

const props = defineProps({
  projects: {
    type: Array,
    required: true
  }
})

function splitStr(str) {
  return str.split(',')
}
</script>
<template>
  <DataTable :value="projects" tableStyle="min-width: 50rem">
    <Column field="project_id" header="SMID" />
    <Column field="project_title" header="Title" />
    <Column field="project_summary" header="Summary" />
    <Column field="date_added" header="Added" />
    <Column field="date_published" header="Published" />
    <Column field="doi" header="DOI">
      <template #body="{ data }">
        <div class="list-none" v-for="doi in splitStr(data.doi)">
          <a class="text-secondary-500 pr-12" target="_blank" :href="`https://doi.org/${doi}`">{{
            doi
          }}</a>
        </div>
      </template>
    </Column>
    <Column field="pmid" header="PMID">
      <template #body="{ data }">
        <div class="list-none" v-for="pmid in splitStr(data.pmid)">
          <a
            class="text-secondary-500"
            target="_blank"
            :href="`http://www.ncbi.nlm.nih.gov/pubmed/${pmid}`"
            >{{ pmid }}</a
          >
        </div>
      </template>
    </Column>
  </DataTable>
</template>
