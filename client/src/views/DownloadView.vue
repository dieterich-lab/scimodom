<template>
  <DefaultLayout>
    <SectionLayout>
      <h1 class="font-ham mb-4 text-3xl font-extrabold text-gray-900 md:text-5xl lg:text-6xl">
        <span
          class="text-transparent bg-clip-text bg-gradient-to-r from-crmapgreen2 from-10% via-crmapgreen1 via-40% via-crmapblue2 via-60% to-crmapblue4 to-100"
        >
          Download
        </span>
        selected dataset
      </h1>
      <p class="text-lg font-normal text-gray-500 lg:text-xl">Database dump or EUF files</p>
      <Divider :pt="{ root: { class: 'bg-crmapgreen0' } }" />
    </SectionLayout>
  </DefaultLayout>
</template>
