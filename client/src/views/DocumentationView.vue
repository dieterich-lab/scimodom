<template>
  <DefaultLayout>
    <SectionLayout>
      <h1 class="font-ham mb-4 text-3xl font-extrabold text-gray-900 md:text-5xl lg:text-6xl">
        <span
          class="text-transparent bg-clip-text bg-gradient-to-r from-crmgs-50 from-10% via-crmgs-25 via-40% via-crmbs-50 via-60% to-crmbs-100 to-100"
        >
          Documentation
        </span>
      </h1>
      <p class="text-lg font-normal text-gray-500 lg:text-xl">General information and how-to</p>
      <Divider :pt="{ root: { class: 'bg-crmg' } }" />
      <div class="text-justify m-6">
        <h1 class="font-ham text-4xl font-semibold m-auto p-4">
          <span>Introduction</span>
        </h1>
        <p class="indent-4 text-lg mt-2 mb-2">
          Sci-ModoM allows to query RNA modification sites according to RNA type, technology,
          species, and genomic features (Search).
        </p>
        <p class="indent-4 text-lg mt-2 mb-2">
          Data can be accessed at the study- or dataset-level. Modifications are associated with a
          given dataset. Each dataset is assigned a EUFID or EUF identifier. One or more dataset can
          belong to a study or project. Projects are identified using a SMID or Sci-ModoM
          identifier. A dataset can include one or more modification, but is uniquely associated
          with a given technology and species (including cell type, tissue, or organ). Hence it is
          easy to think of a dataset as RNA modifications stored in a given bedRMod file (EU
          format).
        </p>
      </div>
    </SectionLayout>
  </DefaultLayout>
</template>
