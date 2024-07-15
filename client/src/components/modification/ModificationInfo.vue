<script setup>
import Dialog from 'primevue/dialog'

const props = defineProps({
  site: {
    type: Object,
    required: true
  }
})

const modelVisible = defineModel('visible')
</script>

<template>
  <Dialog
    v-model:visible="modelVisible"
    header="Modification information"
    :modal="true"
    :pt="{
      root: { class: 'w-fit' },
      closeButton: { class: 'focus:ring-secondary-400 dark:focus:ring-secondary-300' }
    }"
    :ptOptions="{ mergeProps: true }"
  >
    <div>
      <DataTable :value="[site]">
        <Column field="chrom" header="Chrom" sortable exportHeader="chrom"></Column>
        <Column field="start" header="Start" sortable exportHeader="chromStart"></Column>
        <Column field="end" header="End" exportHeader="chromEnd"></Column>
        <Column field="name" header="Name" exportHeader="name"></Column>
        <Column field="score" header="Score" sortable exportHeader="score"></Column>
        <Column field="strand" header="Strand" exportHeader="strand"></Column>
        <Column field="coverage" header="Coverage" sortable exportHeader="coverage"></Column>
        <Column field="frequency" header="Frequency" sortable exportHeader="frequency"></Column>
        <Column field="dataset_id" header="EUFID" exportHeader="EUFID"></Column>
        <Column field="tech" header="Technology" exportHeader="Technology"></Column>
        <Column field="taxa_id" exportHeader="Organism" style="display: none"></Column>
        <Column field="cto" exportHeader="Cell/Tissue" style="display: none"></Column>
        <Column field="feature" header="Feature" exportHeader="Feature"></Column>
        <Column field="gene_name" header="Gene" exportHeader="Gene"></Column>
        <Column field="gene_biotype" header="Biotype" exportHeader="Biotype"></Column>
      </DataTable>
    </div>
  </Dialog>
</template>
