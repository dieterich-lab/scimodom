<script setup lang="ts">
import Message from 'primevue/message'
import Button from 'primevue/button'
import img1 from '@/assets/images/docs/about1.png'
import img2 from '@/assets/images/docs/about2.png'
</script>

<template>
  <div class="text-justify dark:text-white/80">
    <h1 class="font-ham text-4xl font-semibold m-auto pt-4 pb-4">
      <span>About Sci-ModoM</span>
    </h1>
    <p class="indent-4 text-xl leading-relaxed mt-2 mb-4">
      Sci-ModoM is a quantitative database of RNA modifications dedicated to novel assays that
      provide transcriptome-wide information at single-base resolution. A learnable user–interface
      allows to
      <router-link
        :to="{ name: 'search-docs' }"
        class="italic text-primary-500 hover:text-secondary-500"
      >
        Search
      </router-link>
      and
      <router-link
        :to="{ name: 'compare-docs' }"
        class="italic text-primary-500 hover:text-secondary-500"
      >
        Compare
      </router-link>
      modifications site-wise across datasets, and to
      <router-link
        :to="{ name: 'browse-docs' }"
        class="italic text-primary-500 hover:text-secondary-500"
      >
        Browse
      </router-link>
      through or download datasets and retrieve metadata.
    </p>
    <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25 font-semibold">
      Query nomenclature
    </p>
    <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
      Query RNA modification sites according to RNA type, species, technology, and genomic features
      (<span class="italic">Search</span>). Modifications are identifed using their
      <a
        href="https://genesilico.pl/modomics/"
        class="text-primary-500 hover:text-secondary-500"
        rel="noopener noreferrer"
        target="_blank"
      >
        Modomics
      </a>
      short name. The classification of detection technologies is based on the underlying assay,
      <span class="italic">e.g.</span>
      chemical- or enzyme/protein-assisted sequencing (NGS 2nd generation), and native RNA or cDNA
      sequencing (NGS 3rd generation).
    </p>
    <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25 font-semibold">
      Project and dataset
    </p>
    <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
      Data is accessible at the project- or dataset-level (<span class="italic">Browse</span>). One
      or more dataset can belong to a project <span class="italic">e.g.</span>
      this project includes 8 datasets:
      <img :src="img1" class="object-center mt-6 mb-6" alt="About: dataset" />
      Each dataset is assigned a permanent identifier or
      <span class="font-semibold">EUFID</span>
      for
      <span class="font-semibold">Epitranscriptome Unified exchange Format (EUF) identifier</span>.
      As shown above, a dataset can include one or more modification, but is uniquely associated
      with a given species (including cell type, tissue, or organ) and technology.
    </p>
    <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
      Projects are identified using a <span class="font-semibold">SMID</span> or
      <span class="font-semibold">Sci-ModoM identifier</span>. Click on the info (<i
        class="pi pi-info -ml-4"
      />) button to access this information and more:
      <img :src="img2" class="object-center mt-6 mb-6" alt="About: project" />
    </p>
    <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25 font-semibold">
      bedRMod format
    </p>
    <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
      Sci-ModoM promotes the bedRMod format for the standardized exchange and storage of
      modification data. Simply put, a dataset consists of per-site records of RNA modifications
      stored in a given bedRMod file. This file contains a formatted header with metadata, followed
      by distinct RNA modification sites, one per line. For more information, consult the
      <a
        class="text-primary-500 hover:text-secondary-500"
        href="https://dieterich-lab.github.io/scimodom/bedrmod.html"
        target="_blank"
        rel="noopener noreferrer"
        >bedRMod format specification</a
      >.
    </p>
    <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25 font-semibold">
      Assembly
    </p>
    <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
      Only one genome assembly version per species is used in Sci-ModoM. Dataset that do not match
      the database assembly version are lifted over. Only chromosome-level information is
      considered; unassigned contigs or scaffolds are discarded.
      <Message severity="info" :closable="false"
        >Sci-ModoM currently uses human GRCh38 and mouse GRCm39</Message
      >
    </p>
    <p class="indent-4 text-xl leading-relaxed mt-12 mb-2">
      For detailed documentation and development notes, consult the
      <a
        class="text-primary-500 hover:text-secondary-500"
        href="https://dieterich-lab.github.io/scimodom/"
        target="_blank"
        rel="noopener noreferrer"
        >server documentation</a
      >.
    </p>
    <p class="indent-4 text-xl leading-relaxed mt-4 mb-2">
      Consult our development plan for 2024
      <RouterLink class="pl-2 animate-pulse" :to="{ name: 'roadmap' }">
        <!-- <a class="pl-2 animate-pulse" href="https://www.trr319-rmap.de" target="_blank" rel="noopener noreferrer"> -->
        <Button icon="pi pi-arrow-right" size="small" label="Learn more" rounded />
      </RouterLink>
    </p>
  </div>
</template>
