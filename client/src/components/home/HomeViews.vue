<script setup>
import CardLink from '@/components/ui/CardLink.vue'
</script>

<template>
  <SectionLayout>
    <div class="grid grid-flow-row gap-6 lg:grid-flow-col xl:gap-0 justify-items-center">
      <div>
        <CardLink icon="pi pi-database dark:text-white/80" route="search">
          <template v-slot:title> Search RNA modifications </template>
          <template v-slot:content>
            Define your research criteria and query the database for RNA modifications.
          </template>
          <template v-slot:link> Search </template>
        </CardLink>
      </div>
      <div>
        <CardLink icon="pi pi-list dark:text-white/80" route="browse">
          <template v-slot:title> Data repository </template>
          <template v-slot:content> Browse through or search the available datasets. </template>
          <template v-slot:link> Browse </template>
        </CardLink>
      </div>
      <div>
        <CardLink icon="pi pi-search dark:text-white/80" route="compare">
          <template v-slot:title> Complex queries </template>
          <template v-slot:content>
            Combinatorial search. Compare your own data with the database.
          </template>
          <template v-slot:link> Compare </template>
        </CardLink>
      </div>
    </div>
  </SectionLayout>
</template>
