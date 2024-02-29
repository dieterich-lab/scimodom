<template>
  <DefaultLayout>
    <SectionLayout>
      <h1
        class="font-ham mb-4 text-3xl font-extrabold text-gray-900 dark:text-white/80 md:text-5xl lg:text-6xl"
      >
        <span
          class="text-transparent bg-clip-text bg-gradient-to-r from-gg-2 from-10% via-gg-1 via-40% via-gb-2 via-60% to-gb-4 to-100"
        >
          Download
        </span>
        selected dataset
      </h1>
      <p class="text-lg font-normal text-gray-500 dark:text-surface-400 lg:text-xl">
        Database dumps
      </p>
      <Divider />
      <p class="indent-4 text-xl leading-relaxed mt-2 mb-4 dark:text-white/80">
        Data export is available for Search, Browse, and Compare. Database dumps of all or selected
        dataset will soon be available.
      </p>

      <a
        v-for="doi in splitStr(dois)"
        class="text-secondary-500 ml-2"
        target="_blank"
        :href="`https://doi.org/${doi}`"
        >{{ doi }}</a
      >
    </SectionLayout>
  </DefaultLayout>
</template>

<script setup>
const dois = '10.1038/s41587-022-01587-6'
// const dois = '10.1038/s41587-022-01587-6,10.47366/sabia.v5n1a3'
const splitStr = (str) => {
  return str.split(',')
}
</script>
