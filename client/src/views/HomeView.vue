<script setup>
import HomeBanner from '@/components/home/HomeBanner.vue'
import HomeFeatures from '@/components/home/HomeFeatures.vue'
</script>

<template>
  <DefaultLayout :footer="true">
    <HomeBanner />
    <HomeFeatures />
  </DefaultLayout>
</template>
