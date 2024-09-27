<script setup>
import img1 from '@/assets/images/docs/search1.png'
import img2 from '@/assets/images/docs/search2.png'
import img3 from '@/assets/images/docs/search3.png'
import img4 from '@/assets/images/docs/search4.png'
import img5 from '@/assets/images/docs/search5.png'
import img6 from '@/assets/images/docs/search6.png'
import img7 from '@/assets/images/docs/search7.png'
import img8 from '@/assets/images/docs/search8.png'
</script>

<template>
  <div class="text-justify dark:text-white/80">
    <h1 class="font-ham text-4xl font-semibold m-auto pt-4 pb-4">
      <span>Search</span>
    </h1>
    <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25 font-semibold">
      Query and filters
    </p>
    <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
      Search modifications site-wise across whole transcriptomes, by organism and technology, or by
      gene or genomic region. To query the database for a given modification, first select a
      modification and species:
      <img :src="img1" class="object-center mt-6 mb-6" alt="Search: filter species" />
      Available cell types, tissues, and/or organisms are shown for a given modification. A standard
      nomenclature is used to describe cell strains, faithful to published data
      <span class="italic">e.g.</span> HEK293 <span class="italic">vs.</span> HEK293T. For a given
      choice of modification and species (<span class="italic">e.g.</span> m6A and HEK293T), one or
      more technologies can be selected:
      <img :src="img2" class="object-center mt-6 mb-6" alt="Search: filter technologies" />
      The query button remains disabled until a valid combination of modification, species, and
      technologies is selected.
      <Message severity="warn" :closable="false">Slow queries for large datasets</Message>
      Some combinations may contain a large amount of records; selecting a particular gene of
      interest:
      <img :src="img3" class="object-center mt-6 mb-6" alt="Search: filter gene" />
      or a genomic region:
      <img :src="img4" class="object-center mt-6 mb-6" alt="Search: filter chrom" />
      can significantly reduce the query time. In addition, as shown above, the search can be
      narrowed down by selecting a biotype or a genomic feature.
      <Message severity="info" :closable="false"
        >Gene and genomic (chromosome) selection are mutually exclusive</Message
      >
      To query the database for all modifications in a particular gene or genomic region, use the
      toggle button, and select a gene or a genomic region:
      <img :src="img8" class="object-center mt-6 mb-6" alt="Search: gene or chrom" />
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
      <Message severity="success" :closable="false"
        >Click on "Start" to visualize the modification site on Ensembl</Message
      >
      <Message severity="success" :closable="false"
        >Click on "Name" to access detailed information on modified residues</Message
      >
      <Message severity="success" :closable="false"
        >Click on "EUFID" to access metadata and download all records for a given dataset in bedRMod
        format</Message
      >
      <Message severity="success" :closable="false"
        >Click on "Gene" to access gene table information on Ensembl</Message
      >
      <Message severity="success" :closable="false"
        >Click on <i class="pi pi-info -ml-3 mr-1" /> to retrieve site-specific information</Message
      >
      Query results are shown in tabular format where sites are recorded per dataset, allowing to
      organize data and prioritize sites with high stoichiometry, coverage, and/or score. Export all
      results to a CSV file.
      <img :src="img5" class="object-center mt-6 mb-6" alt="Search: results table" />
      All columns with arrow signs can be sorted. Multiple columns can be sorted at once, this
      requires a metaKey (<span class="italic">e.g.</span> ⌘ or Ctrl) to be pressed when clicking a
      header. A third click removes the sorting from the column. Site-specific information includes
      the genomic sequence context, support from other datasets, miRNA target or RBP binding sites
      that may be affected by the modification:
      <img :src="img6" class="object-center mt-6 mb-6" alt="Search: plus top" />
      Scroll to the bottom to see all tables:
      <img :src="img7" class="object-center mt-6 mb-6" alt="Search: plus bottom" />
    </p>
    <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
      These tables can also be exported to CSV, including site-specific information. To download
      records for a given dataset, click on the EUFID; the <span class="italic">Browse</span> view
      allows to download bedRMod-formatted records.
    </p>
  </div>
</template>
