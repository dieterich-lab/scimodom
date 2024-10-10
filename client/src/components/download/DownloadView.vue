<script setup lang="ts">
import StyledHeadline from '@/components/ui/StyledHeadline.vue'
import SubTitle from '@/components/ui/SubTitle.vue'
import DefaultLayout from '@/components/layout/DefaultLayout.vue'
import SectionLayout from '@/components/layout/SectionLayout.vue'
</script>
<template>
  <DefaultLayout>
    <SectionLayout>
      <StyledHeadline text="Download selected dataset" />
      <SubTitle>Database dumps</SubTitle>

      <Divider />

      <p class="indent-4 text-xl leading-relaxed mt-2 mb-4 dark:text-white/80">
        Data export is available for Search, Browse, and Compare. Database dumps of all or selected
        dataset will soon be available.
      </p>
    </SectionLayout>
  </DefaultLayout>
</template>
