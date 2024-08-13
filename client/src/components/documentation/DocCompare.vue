<script setup>
import img1 from '@/assets/images/docs/compare1.png'
import img2 from '@/assets/images/docs/compare2.png'
import img3 from '@/assets/images/docs/compare3.png'
import img4 from '@/assets/images/docs/compare4.png'
</script>

<template>
  <div class="text-justify dark:text-white/80">
    <h1 class="font-ham text-4xl font-semibold m-auto pt-4 pb-4">
      <span>Compare</span>
    </h1>
    <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25 font-semibold">
      Query and filters
    </p>
    <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
      Compare datasets to one another by finding modification sites common to multiple datasets
      (intersection) or those only found in a group of datasets (difference), or find modification
      sites in a given dataset that are close to, but not intersecting with sites in other datasets
      (closest). Perform these operations strand-aware or unaware. Use available datasets, or upload
      your own data to compare it against database records, without registration or login.
    </p>
    <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
      First select a given organism, then select up to 3 reference datasets. Use the search bar
      (dataset dropdown) to narrow down your selection,
      <span class="italic">e.g.</span> select the PRAISE datasets:
      <img :src="img1" class="object-center mt-6 mb-6" alt="Compare: filter 1" />
      Second, select up to 3 datasets for comparison:
      <img :src="img2" class="object-center mt-6 mb-6" alt="Compare: filter 2" />
      You can also use your own data (bedRMod or BED format), click on "Select a file". The format
      is automatically recognized, but can also be forced by using the toggle button. You data is
      securely handled and is automatically deleted. BED files with more than 6 columns are cut down
      to BED6.
      <Message severity="warn" :closable="false"
        >Data coming from a different assembly or an inconsistent choice of reference dataset will
        lead to spurious comparison results</Message
      >
      Finally, Select the operation you want to perform on the datasets selected in previous steps:
      <img :src="img3" class="object-center mt-6 mb-6" alt="Compare: filter 3" />
    </p>
    <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25 font-semibold">
      Results table
    </p>
    <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
      <Message severity="success" :closable="false"
        >Sort data according to stoichiometry (frequency), coverage, and/or score</Message
      >
      <Message severity="success" :closable="false"
        >Hover over selected headers to get more information</Message
      >
      <Message severity="success" :closable="false">Download all comparison results as CSV</Message>
      Columns for EUFID, coverage, and frequency are filled with default values when comparing to a
      BED6 upload. The "Distance" is only shown for dataset difference or "closest":
      <img :src="img4" class="object-center mt-6 mb-6" alt="Compare: results" />
      <Message severity="warn" :closable="false"
        >The more datasets you select or the larger the datasets, the longer the query time, the
        slower the scrolling behaviour</Message
      >
    </p>
  </div>
</template>
