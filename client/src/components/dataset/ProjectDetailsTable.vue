<script setup>
import DataTable from 'primevue/datatable'
import { ref, onMounted } from 'vue'
import { splitStr } from '@/utils/index.js'
import { loadProjects } from '@/services/project'

const props = defineProps({
  projectId: {
    type: String,
    required: true
  }
})

const projectsById = ref(new Map())
const project = ref([])

onMounted(() => {
  // list all projects by id
  loadProjects(null, projectsById)
    .then((response) => {
      project.value = [projectsById.value[props.projectId]]
    })
    .catch((error) => {
      console.log(error)
    })
})
</script>

<template>
  <DataTable :value="project" tableStyle="min-width: 50rem">
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
