<script setup>
import HomeBanner from '@/components/home/HomeBanner.vue'
import HomeViews from '@/components/home/HomeViews.vue'
import HomeIntro from '@/components/home/HomeIntro.vue'
import HomeFeatures from '@/components/home/HomeFeatures.vue'
import HomeRoadmap from '@/components/home/HomeRoadmap.vue'
import HomeRelease from '@/components/home/HomeRelease.vue'
</script>

<template>
  <DefaultLayout :footer="true">
    <HomeBanner />
    <HomeViews />
    <HomeIntro />
    <HomeFeatures />
    <HomeRelease />
    <HomeRoadmap />
  </DefaultLayout>
</template>
