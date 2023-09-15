<script setup>
import ScimodomLogo from './ScimodomLogo.vue'
import NavigationBar from './NavigationBar.vue'
import ButtonIcon from '@/components/ui/ButtonIcon.vue'
</script>

<template>
  <header>
    <div class="h-border" />
    <div class="mx-auto w-full max-w-screen-2xl p-2 py-6 lg:py-8 flex flex-wrap items-center">
      <div class="flex flex-wrap 2xl:w-4/5 xl:w-auto">
        <ScimodomLogo />
        <NavigationBar />
      </div>
      <div class="flex flex-wrap 2xl:w-1/5 xl:w-auto 2xl:pl-8 xl:pl-0">
        <ButtonIcon
          icon="pi pi-user"
          class="text-white bg-crmapgreen hover:bg-crmapgreen2 focus:ring-crmapgreen1"
        >
          Login
        </ButtonIcon>
        <ButtonIcon
          icon="pi pi-user-plus"
          class="text-white bg-crmapblue hover:bg-crmapblue2 focus:ring-crmapblue1"
        >
          Sign Up
        </ButtonIcon>
      </div>
      <!-- <SearchForm /> -->
    </div>
  </header>
</template>

<style scoped>
header {
  @apply top-0 z-20 sticky bg-ctransparent opacity-90 border-b border-cborder;
}
.h-border {
  @apply p-1;
  @apply bg-gradient-to-r from-crmapgreen2 from-10% via-crmapgreen1 via-40% via-crmapblue2 via-60% to-crmapblue4 to-100%;
}
</style>
