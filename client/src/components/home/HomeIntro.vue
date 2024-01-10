<template>
  <SectionLayout>
    <div class="text-center m-6">
      <h1 class="font-ham text-4xl font-semibold m-auto p-4">
        <span>Sci-ModoM</span>
      </h1>
      <p class="text-xl font-medium text-gray-600 pt-4 pb-2">
        Data availability and usability remain a critical challenge in Life Sciences.
      </p>
      <p class="text-xl font-medium text-gray-600 pb-4">
        In coordination with the epitranscriptomics community, we aim to establish a pan-European
        roadmap to facilitate access to and sharing of high-throughput transcriptome-wide RNA
        modification data, to harmonize data exchange formats and interoperability standards.
      </p>
    </div>
    <div class="flex justify-center mt-4 animate-pulse">
      <a href="https://www.trr319-rmap.de" target="_blank" rel="noopener noreferrer">
        <Button
          icon="pi pi-arrow-right"
          label="Learn more"
          :pt="{
            root: {
              class:
                'bg-crmg border-crmg shadow hover:bg-crmg/75 hover:border-crmg/75 focus:ring-crmg/75 focus:outline-none focus:!shadow-[0_0_0_2px_rgba(255,255,255,1),0_0_0_4px_rgba(0,176,81,1),0_1px_2px_0_rgba(0,0,0,1)]'
            }
          }"
        />
      </a>
    </div>
  </SectionLayout>
</template>
