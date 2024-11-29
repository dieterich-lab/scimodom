<script setup lang="ts">
import Button from 'primevue/button'
import SectionLayout from '@/components/layout/SectionLayout.vue'
</script>
<template>
  <SectionLayout :secondary="true">
    <div class="px-4 py-8 md:px-6 lg:px-8 text-center">
      <h1 class="font-ham text-4xl font-semibold m-auto p-4 dark:text-white/80">
        <span>Sci-ModoM</span>
      </h1>
      <p class="text-xl font-medium text-gray-600 pt-4 pb-2 dark:text-surface-400">
        Data availability and usability remains a critical challenge in Life Sciences.
      </p>
      <p class="text-xl font-medium text-gray-600 pb-4 dark:text-surface-400">
        In coordination with the epitranscriptomics community, we aim to establish a pan-European
        roadmap to facilitate access to and sharing of high-throughput transcriptome-wide RNA
        modification data, to harmonize data exchange formats and interoperability standards.
      </p>
    </div>
    <div class="flex justify-center mt-4 animate-pulse">
      <a href="https://humanrnomeproject.org" target="_blank" rel="noopener noreferrer">
        <Button icon="pi pi-arrow-right" label="Learn more" rounded />
      </a>
    </div>
    <div class="flex justify-center mt-4 py-4">
      <h1 class="font-ham text-xl font-semibold m-auto p-4 dark:text-white/80">
        <span>How to cite</span>
      </h1>
    </div>
    <div class="flex flex-col item-stretch text-700 line-height-3 -mt-4 dark:text-white/80">
      <div class="self-center">
        Etienne Boileau, Harald Wilhelmi, Anne Busch, Andrea Cappannini, Andreas Hildebrand, Janusz
        M. Bujnicki, Christoph Dieterich.
      </div>
      <div class="self-center">
        <a
          class="text-primary-500 hover:text-secondary-500"
          href="https://doi.org/10.1093/nar/gkae972"
          target="_blank"
          rel="noopener noreferrer"
        >
          Sci-ModoM: a quantitative database of transcriptome-wide high-throughput RNA modification
          sites
        </a>
      </div>
      <div class="self-center">
        <span class="italic">Nucleic Acids Research</span>, 2024, gkae972.
      </div>
    </div>
  </SectionLayout>
</template>
