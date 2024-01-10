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
        <h1 class="font-ham text-4xl font-semibold m-auto pt-4 pb-4">
          <span>Introduction</span>
        </h1>
        <p class="indent-4 text-xl leading-relaxed mt-2 mb-4">
          Sci-ModoM is under active development. Consult our roadmap for 2024
          <!-- <div class="flex justify-center mt-4 animate-pulse"> -->
          <RouterLink class="pl-2 animate-pulse" :to="{ name: 'roadmap' }">
            <!-- <a class="pl-2 animate-pulse" href="https://www.trr319-rmap.de" target="_blank" rel="noopener noreferrer"> -->
            <Button
              icon="pi pi-arrow-right"
              size="small"
              label="Learn more"
              :pt="{
                root: {
                  class:
                    'bg-crmg border-crmg shadow hover:bg-crmg/75 hover:border-crmg/75 focus:ring-crmg/75 focus:outline-none focus:!shadow-[0_0_0_2px_rgba(255,255,255,1),0_0_0_4px_rgba(0,176,81,1),0_1px_2px_0_rgba(0,0,0,1)]'
                }
              }"
            />
          </RouterLink>
          <!-- </a> -->
          <!-- </div> -->
        </p>
        <p class="indent-4 text-lg underline underline-offset-8 decoration-crmbs-100/25">
          Query nomenclature
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          Sci-ModoM allows to query RNA modification sites according to RNA type, technology,
          species, and genomic features (<span class="italic">Search</span>). The classification of
          detection technologies is taken from
          <a
            class="text-crmg hover:text-crmb"
            href="https://www.nature.com/articles/s12276-022-00821-0"
            target="_blank"
            rel="noopener noreferrer"
            >Detection technologies for RNA modifications</a
          >.
        </p>
        <p class="indent-4 text-lg underline underline-offset-8 decoration-crmbs-100/25">
          Project and dataset
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          Data is also accessible at the study- or dataset-level (<span class="italic">Browse</span
          >). Modifications are associated with a given dataset. Each dataset is assigned a
          <span class="font-semibold">EUFID</span> or
          <span class="font-semibold">EUF identifier</span>. One or more dataset can belong to a
          study or project, <span class="italic">e.g.</span> dataset "Wildtype HEK293T", "Wildtype
          mESC" belong to the "GLORI" project. Projects are identified using a
          <span class="font-semibold">SMID</span> or
          <span class="font-semibold">Sci-ModoM identifier</span>. A dataset can include one or more
          modification, but is uniquely associated with a given technology and species (including
          cell type, tissue, or organ). Project creation is handled by maintainers via request (more
          details soon). Once a project is created, users can add data to it.
        </p>
        <p class="indent-4 text-lg underline underline-offset-8 decoration-crmbs-100/25">
          bedRMod format
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          It is easy to think of a dataset as RNA modifications stored in a given bedRMod file. The
          bedRMod or EU (epitranscriptome unified data exchange) format is similar to the
          <a
            class="text-crmg hover:text-crmb"
            href="https://www.encodeproject.org/data-standards/wgbs/"
            target="_blank"
            rel="noopener noreferrer"
            >ENCODE bedMethyl</a
          >
          format (BED9+2), but includes a header. The bedRMod file is a tabulated count of base
          modifications from every sequencing read over each reference genomic position. It is a
          convenient representation of all the modified based information stored in the
          <a
            class="text-crmg hover:text-crmb"
            href="http://samtools.github.io/hts-specs/SAMtags.pdf"
            target="_blank"
            rel="noopener noreferrer"
            >MM/ML tags</a
          >
          stored in BAM alignment files. When aligning or basecalling, most recent software should
          output these tags.
        </p>
        <p class="indent-4 text-lg underline underline-offset-8 decoration-crmbs-100/25">
          Assembly
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          Available assemblies for different organisms define the assembly version used in
          Sci-ModoM. Dataset that do not match the database assembly version are lifted over. Only
          chromosomes are considered.
        </p>
        <p class="indent-4 text-lg underline underline-offset-8 decoration-crmbs-100/25">
          Annotation
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          Annotation are created by intersecting dataset records with features (UTRs, CDS, ...)
          merged across transcripts extracted from a given Ensembl GTF file.
        </p>
      </div>
      <!-- HOW TO ----  -->
      <div class="text-justify m-6">
        <h1 class="font-ham text-4xl font-semibold m-auto pt-4 pb-4">
          <span>Search</span>
        </h1>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          To query the database for RNA modifications, first select one RNA type (mRNA, tRNA,
          <span class="italic">etc.</span>), then available technologies and organisms. Selected
          records can be exported to CSV.
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          Columns with arrow signs can be sorted. Multiple columns can be sorted, this requires a
          metaKey (<span class="italic">e.g.</span> ⌘ or Ctrl) to be pressed when clicking a header.
          A third click removes the sorting from the column. Table filters to be soon available.
        </p>
        <h1 class="font-ham text-4xl font-semibold m-auto pt-4 pb-4">
          <span>Browse</span>
        </h1>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          Query the database to find projects, studies and/or dataset. You can refine your search
          using global filters (top left), or filter by RNA modification, technology, organism,
          cell, tissue and/or organ. Click on the + button to see additional information. Records
          can be exported to CSV.
        </p>
        <h1 class="font-ham text-4xl font-semibold m-auto pt-4 pb-4">
          <span>Compare</span>
        </h1>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          Compare dataset by finding modifications common to multiple dataset (intersection) or
          modifications found in a group of dataset only (difference). You can also find
          modifications in a given dataset that are close to, but not intersecting with
          modifications in another dataset (closest). You can perform these operations using
          available dataset, but you can also compare these dataset with your own data.
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          <span class="font-bold">A</span> First select a given organism. You can refine your search
          by cell, tissue and/or organ, RNA modification, and technology, or select dataset directly
          (drop down or search).
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          <span class="font-bold">B</span> Select dataset for comparison. You can also use your own
          data. It must be a bedRMod, a BED6, or a BED9+2 file.
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          <span class="font-bold">C</span> Select the operation you want to perform on the dataset
          selected in A and B. Records can be exported to CSV.
        </p>
      </div>
    </SectionLayout>
  </DefaultLayout>
</template>
