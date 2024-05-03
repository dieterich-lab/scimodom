<script setup>
import { ref, inject, onMounted } from 'vue'
import { HTTP } from '@/services/API.js'

const dialogRef = inject('dialogRef')
const records = ref()

const splitStr = (str) => {
  return str.split(',')
}

onMounted(() => {
  HTTP.get('/smid')
    .then(function (response) {
      records.value = response.data
    })
    .catch((error) => {
      console.log(error)
    })
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
    <Column field="id" header="SMID"></Column>
    <Column field="title" header="Title"></Column>
    <Column field="summary" header="Summary"></Column>
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
