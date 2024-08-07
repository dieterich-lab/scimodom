<script setup>
import SunburstChart from '@/components/chart/SunburstChart.vue'
</script>

<template>
  <SectionLayout :secondary="true">
    <div>
      <div class="px-4 py-8 md:px-6 lg:px-8 text-center">
        <h1 class="font-ham text-4xl font-semibold m-auto p-4 dark:text-white/80">
          <span>Release</span>
        </h1>
        <SunburstChart />
      </div>
    </div>
  </SectionLayout>
</template>
