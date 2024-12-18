<script setup lang="ts">
import Message from 'primevue/message'
import img1 from '@/assets/images/docs/browse1.png'
import img2 from '@/assets/images/docs/browse2.png'
import img3 from '@/assets/images/docs/browse3.png'
import img4 from '@/assets/images/docs/browse4.png'
</script>

<template>
  <div class="text-justify dark:text-white/80">
    <h1 class="font-ham text-4xl font-semibold m-auto pt-4 pb-4">
      <span>Browse</span>
    </h1>
    <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25 font-semibold">
      Query and filters
    </p>
    <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
      Query the database to find projects and/or datasets, and access metadata. You can refine your
      search using global filters (top left of table <span class="italic">e.g.</span> search for
      datasets containing "NSUN" in their metadata or title):
      <img :src="img1" class="object-center mt-6 mb-6" alt="Browse: global filter" />
      and/or table filters (RNA type and modification, organism, cell, tissue and/or organ, or
      technology, <span class="italic">e.g.</span> search for "mESC"):
      <img :src="img2" class="object-center mt-6 mb-6" alt="Browse: table filter" />
      Use "Match Any" to combine filters, <span class="italic">e.g.</span> search for different
      technologies:
      <img :src="img3" class="object-center mt-6 mb-6" alt="Browse: table filter" />
      <Message severity="warn" :closable="false"
        >Don't forget to clear filters when changing search parameters, this is not automatically
        done</Message
      >
    </p>
    <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25 font-semibold">
      Results table
    </p>
    <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
      <Message severity="success" :closable="false">Download datasets as bedRMod</Message>
      <Message severity="success" :closable="false">Access or export metadata and more</Message>
      Click the info (<i class="pi pi-info -ml-4" />) button to see project-related information and
      additional attachments (BAM files):
      <img :src="img4" class="object-center mt-6 mb-6" alt="Browse: plus" />
      BAM file attachments (if available) allow to access read-level information before it is
      aggregated site-wise into bedRMod. Each dataset can be downloaded as a
      <a
        class="text-primary-500 hover:text-secondary-500"
        href="https://dieterich-lab.github.io/euf-specs/"
        target="_blank"
        rel="noopener noreferrer"
        >bedRMod</a
      >
      file.
    </p>
    <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
      The complete list of datasets and their metadata can be exported to CSV.
    </p>
  </div>
</template>
