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
  </SectionLayout>
</template>
