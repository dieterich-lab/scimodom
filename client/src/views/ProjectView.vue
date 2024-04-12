<script setup>
import { ref } from 'vue'

import ProjectForm from '@/components/project/ProjectForm.vue'
</script>

<template>
  <DefaultLayout>
    <SectionLayout>
      <h1
        class="font-ham mb-4 text-3xl font-extrabold text-gray-900 dark:text-white/80 md:text-5xl lg:text-6xl"
      >
        <span
          class="text-transparent bg-clip-text bg-gradient-to-r from-gg-2 from-10% via-gg-1 via-40% via-gb-2 via-60% to-gb-4 to-100"
        >
          Project
        </span>
        creation
      </h1>
      <p class="text-lg font-normal text-gray-500 dark:text-surface-400 lg:text-xl">
        Fill the template and request to create a new project
      </p>
      <Divider />
      <p class="text-lg leading-relaxed mt-2 mb-4 dark:text-white/80">
        To upload data to an existing project, use the
        <RouterLink :to="{ name: 'upload' }" class="text-primary-500 hover:text-secondary-500">
          dataset upload form
          <i class="pi pi-arrow-up-right text-sm" />
        </RouterLink>
        <br />
        To create a new project, complete the form below.
      </p>
    </SectionLayout>

    <ProjectForm />
  </DefaultLayout>
</template>
