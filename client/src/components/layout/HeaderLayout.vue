<script setup>
import ScimodomLogo from './ScimodomLogo.vue'
import NavigationBar from './NavigationBar.vue'
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
                'bg-crmg border-crmg hover:bg-crmg/75 hover:border-crmg/75 focus:ring-crmg/75 focus:outline-none focus:shadow-[0_0_0_2px_rgba(255,255,255,1),0_0_0_4px_rgba(0,176,81,1),0_1px_2px_0_rgba(0,0,0,1)]'
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
                'bg-crmb border-crmb hover:bg-crmb/75 hover:border-crmb/75 focus:ring-crmb/75 focus:outline-none focus:shadow-[0_0_0_2px_rgba(255,255,255,1),0_0_0_4px_rgba(1,176,237,1),0_1px_2px_0_rgba(0,0,0,1)]'
            }
          }"
        />
      </div>
      <!-- <SearchForm /> -->
    </div>
  </header>
</template>
