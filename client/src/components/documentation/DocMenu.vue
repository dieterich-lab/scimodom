<template>
  <SectionLayout>
    <router-link :to="{ name: 'about-docs' }">
      <h1 class="font-ham text-xl font-semibold m-auto pb-2">
        <span>About</span>
      </h1>
    </router-link>
    <router-link :to="{ name: 'search-docs' }">
      <h1 class="font-ham text-xl font-semibold m-auto pb-2">
        <span>Search</span>
      </h1>
    </router-link>
    <router-link :to="{ name: 'browse-docs' }">
      <h1 class="font-ham text-xl font-semibold m-auto pb-2">
        <span>Browse</span>
      </h1>
    </router-link>
    <router-link :to="{ name: 'compare-docs' }">
      <h1 class="font-ham text-xl font-semibold m-auto pb-2">
        <span>Compare</span>
      </h1>
    </router-link>
    <router-link :to="{ name: 'management-docs' }">
      <h1 class="font-ham text-xl font-semibold m-auto pb-2">
        <span>Data management</span>
      </h1>
    </router-link>
    <router-link :to="{ name: 'faqs-docs' }">
      <h1 class="font-ham text-xl font-semibold m-auto pb-2">
        <span>FAQs</span>
      </h1>
    </router-link>
  </SectionLayout>
</template>
