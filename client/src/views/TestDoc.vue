<script setup>
import StyledHeadline from '@/components/ui/StyledHeadline.vue'
import SubTitle from '@/components/ui/SubTitle.vue'
import DocMenu from '@/components/documentation/DocMenu.vue'
</script>

<template>
  <DefaultLayout>
    <SectionLayout>
      <StyledHeadline text="Documentation" />
      <SubTitle>General information and how-to</SubTitle>
      <Divider />
      <div class="flex flex-row">
        <div class="basis-1/6">
          <DocMenu />
        </div>
        <div class="basis-5/6">
          <router-view></router-view>
        </div>
      </div>
    </SectionLayout>
  </DefaultLayout>
</template>
