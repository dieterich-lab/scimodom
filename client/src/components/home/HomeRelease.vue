<script setup lang="ts">
import { ref, onMounted } from 'vue'
import SunburstChart from '@/components/ui/SunburstChart.vue'
import { HTTP } from '@/services/API.js'
import SectionLayout from '@/components/layout/SectionLayout.vue'

const sites = ref()
const datasets = ref()

// clean this, and fetch annotation (DB) release info
onMounted(() => {
  HTTP.get('/release')
    .then(function (response) {
      sites.value = response.data.sites
      datasets.value = response.data.datasets
    })
    .catch((error) => {
      console.log(error)
    })
})
</script>

<template>
  <SectionLayout :secondary="false">
    <div>
      <div class="px-4 py-8 md:px-6 lg:px-8 text-center">
        <h1 class="font-ham text-4xl font-semibold m-auto p-4 dark:text-white/80">
          <span>Release</span>
        </h1>
        <p class="leading-loose text-xl font-medium text-gray-600 pt-4 pb-2 dark:text-surface-400">
          Sci-ModoM contains {{ sites }} reported sites with stoichiometric information across
          {{ datasets }} datasets, for genome assemblies <br />
          GRCh38 (human) and GRCm39 (mouse), annotated using Ensembl release 110.
        </p>
        <div class="flex flex-row pt-12">
          <div class="basis-1/2">
            <SunburstChart type="search" />
          </div>
          <div class="basis-1/2">
            <SunburstChart type="browse" />
          </div>
        </div>
      </div>
    </div>
  </SectionLayout>
</template>
