<script setup>
import ScimodomLogo from './ScimodomLogo.vue'
import NavigationBar from './NavigationBar.vue'
// import ButtonIcon from '@/components/ui/ButtonIcon.vue'
</script>

<template>
  <header class="top-0 z-20 sticky bg-white opacity-90 border-b border-[#e2ecec]">
    <div
      class="p-1 bg-gradient-to-r from-crmgs-50 from-10% via-crmgs-25 via-40% via-crmbs-50 via-60% to-crmbs-100 to-100%"
    />
    <div class="mx-auto w-full max-w-screen-2xl p-2 py-6 lg:py-8 flex flex-wrap items-center">
      <div class="flex flex-wrap 2xl:w-4/5 xl:w-auto">
        <ScimodomLogo />
        <NavigationBar />
      </div>
      <div class="flex flex-wrap 2xl:w-1/5 xl:w-auto 2xl:pl-8 xl:pl-0 gap-4">
        <Button
          icon="pi pi-user"
          size="small"
          label="Login"
          :pt="{
            root: {
              class:
                'bg-crmg border-crmg hover:bg-crmgs-50 hover:border-crmgs-50 focus:ring-crmgs-50 focus:outline-none'
            }
          }"
        />
        <Button
          icon="pi pi-user-plus"
          size="small"
          label="Sign Up"
          :pt="{
            root: {
              class:
                'bg-crmb border-crmb hover:bg-crmbs-50 hover:border-crmbs-50 focus:ring-crmbs-50 focus:outline-none'
            }
          }"
        />
      </div>
      <!-- <SearchForm /> -->
    </div>
  </header>
</template>
