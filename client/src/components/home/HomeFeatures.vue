<script setup lang="ts">
import Button from 'primevue/button'
import SectionLayout from '@/components/layout/SectionLayout.vue'
</script>
<template>
  <SectionLayout :secondary="true">
    <div class="px-4 py-8 md:px-6 lg:px-8 text-center">
      <h1 class="font-ham text-4xl font-semibold m-auto p-4 dark:text-white/80">
        <span>Features</span>
      </h1>
      <p class="text-xl font-medium text-gray-600 pt-4 pb-2 dark:text-surface-400">
        Sci-ModoM is under active development.
      </p>
      <div class="grid grid-cols-3 gap-2">
        <div class="grid-cols-12 md:grid-cols-4 mb-4 px-5">
          <span class="p-3 shadow-2 mb-3 inline-block justify-center" style="rounded-xl">
            <i class="pi pi-file-export text-4xl text-primary-500 dark:text-secondary-500"></i>
          </span>
          <div class="text-900 text-xl mb-3 font-medium dark:text-white/80">Data format</div>
          <span class="text-700 line-height-3 dark:text-white/80">
            Support and promote the
            <a
              class="text-primary-500 hover:text-secondary-500"
              href="https://dieterich-lab.github.io/euf-specs/"
              target="_blank"
              rel="noopener noreferrer"
              >bedRMod</a
            >
            format.
          </span>
        </div>
        <div class="col-12 md:col-4 mb-4 px-5">
          <span class="p-3 shadow-2 mb-3 inline-block surface-card" style="border-radius: 10px">
            <i class="pi pi-database text-4xl text-primary-500 dark:text-secondary-500"></i>
          </span>
          <div class="text-900 text-xl mb-3 font-medium dark:text-white/80">Database</div>
          <span class="text-700 line-height-3 dark:text-white/80">
            Starting with whole-transcriptome m6A, m5C, Ψ, 2'-O-Me, and m7G, we continuously add
            data encompassing a wide range of modifications, technologies, and species.
          </span>
        </div>
        <div class="col-12 md:col-4 mb-4 px-5">
          <span class="p-3 shadow-2 mb-3 inline-block surface-card" style="border-radius: 10px">
            <i class="pi pi-chart-bar text-4xl text-primary-500 dark:text-secondary-500"></i>
          </span>
          <div class="text-900 text-xl mb-3 font-medium dark:text-white/80">Tools</div>
          <span class="text-700 line-height-3 dark:text-white/80">
            Search and compare modifications across datasets. Annotation, interactome.
          </span>
        </div>
        <div class="col-12 md:col-4 mb-4 px-5">
          <span class="p-3 shadow-2 mb-3 inline-block surface-card" style="border-radius: 10px">
            <i class="pi pi-users text-4xl text-primary-500 dark:text-secondary-500"></i>
          </span>
          <div class="text-900 text-xl mb-3 font-medium dark:text-white/80">Access</div>
          <span class="text-700 line-height-3 dark:text-white/80">
            Free and open to all users. There is no login required. Optional login with access
            management and data upload.</span
          >
        </div>
        <div class="col-12 md:col-4 mb-4 px-5">
          <span class="p-3 shadow-2 mb-3 inline-block surface-card" style="border-radius: 10px">
            <i class="pi pi-comments text-4xl text-primary-500 dark:text-secondary-500"></i>
          </span>
          <div class="text-900 text-xl mb-3 font-medium dark:text-white/80">Support</div>
          <span class="text-700 line-height-3 dark:text-white/80">
            Full support during the development phase. Check our
            <a
              href="https://github.com/dieterich-lab/scimodom/discussions"
              class="text-primary-500 hover:text-secondary-500"
              target="_blank"
              rel="noopener noreferrer"
              >forum</a
            >
            or
            <a
              href="mailto:boileau@uni-heidelberg.de"
              class="text-primary-500 hover:text-secondary-500"
              >contact us</a
            >
            with your feedback, request, or questions.
          </span>
        </div>
        <div class="col-12 md:col-4 md:mb-4 mb-0 px-3">
          <span class="p-3 shadow-2 mb-3 inline-block surface-card" style="border-radius: 10px">
            <i class="pi pi-list text-4xl text-primary-500 dark:text-secondary-500"></i>
          </span>
          <div class="text-900 text-xl mb-3 font-medium dark:text-white/80">More...</div>
          <span class="text-700 line-height-3 dark:text-white/80">
            Addition of RNA types (tRNA, rRNA), integration of RNA processing events.</span
          >
        </div>
      </div>
    </div>
    <div class="flex justify-center mt-8 animate-pulse">
      <RouterLink :to="{ name: 'about-docs' }">
        <Button icon="pi pi-arrow-right" label="Learn more about Sci-ModoM" rounded />
      </RouterLink>
    </div>
  </SectionLayout>
</template>
