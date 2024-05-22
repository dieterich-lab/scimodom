<script setup>
import StyledHeadline from '@/components/ui/StyledHeadline.vue'
import SubTitle from '@/components/ui/SubTitle.vue'
</script>
<template>
  <DefaultLayout>
    <SectionLayout>
      <StyledHeadline text="Documentation" />
      <SubTitle>General information and how-to</SubTitle>

      <Divider />

      <div class="text-justify m-6 dark:text-white/80">
        <h1 class="font-ham text-4xl font-semibold m-auto pt-4 pb-4">
          <span>Introduction</span>
        </h1>
        <p class="indent-4 text-xl leading-relaxed mt-2 mb-4">
          Sci-ModoM is under active development. Consult our roadmap for 2024
          <!-- <div class="flex justify-center mt-4 animate-pulse"> -->
          <RouterLink class="pl-2 animate-pulse" :to="{ name: 'roadmap' }">
            <!-- <a class="pl-2 animate-pulse" href="https://www.trr319-rmap.de" target="_blank" rel="noopener noreferrer"> -->
            <Button icon="pi pi-arrow-right" size="small" label="Learn more" rounded />
          </RouterLink>
          <!-- </a> -->
          <!-- </div> -->
        </p>
        <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25">
          Query nomenclature
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          Sci-ModoM allows to query RNA modification sites according to RNA type, species,
          technology, and genomic features (<span class="italic">Search</span>). The classification
          of detection technologies is based on
          <a
            class="text-primary-500 hover:text-secondary-500"
            href="https://www.nature.com/articles/s12276-022-00821-0"
            target="_blank"
            rel="noopener noreferrer"
            >Detection technologies for RNA modifications</a
          >.
        </p>
        <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25">
          Project and dataset
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          Data is also accessible at the study- or dataset-level (<span class="italic">Browse</span
          >). Each dataset is assigned a <span class="font-semibold">EUFID</span> or
          <span class="font-semibold">EUF identifier</span>. One or more dataset can belong to a
          study or project, <span class="italic">e.g.</span> dataset "Wildtype HEK293T" and
          "Wildtype mESC" belong to the "GLORI" project. Projects are identified using a
          <span class="font-semibold">SMID</span> or
          <span class="font-semibold">Sci-ModoM identifier</span>. A dataset can include one or more
          modification, but is uniquely associated with a given species (including cell type,
          tissue, or organ) and technology.
        </p>
        <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25">
          bedRMod format
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          Simply put, a dataset consists of per-site records of RNA modifications stored in a given
          bedRMod file. The bedRMod or EU (epitranscriptome unified data exchange) format is similar
          to the
          <a
            class="text-primary-500 hover:text-secondary-500"
            href="https://www.encodeproject.org/data-standards/wgbs/"
            target="_blank"
            rel="noopener noreferrer"
            >ENCODE bedMethyl</a
          >
          format (BED9+2), but includes a header. The name (4th column) must conform to the
          <a
            class="text-primary-500 hover:text-secondary-500"
            href="https://www.genesilico.pl/modomics/modifications"
            target="_blank"
            rel="noopener noreferrer"
            >MODOMICS</a
          >
          nomenclature for the modification short name, and the score (5th column) is a
          site-specific measure of confidence.
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          The bedRMod file is a tabulated count of base modifications from every sequencing read
          over each reference genomic position. It is a convenient representation of the information
          stored in the
          <a
            class="text-primary-500 hover:text-secondary-500"
            href="http://samtools.github.io/hts-specs/SAMtags.pdf"
            target="_blank"
            rel="noopener noreferrer"
            >MM/ML tags</a
          >
          in BAM alignment files. When aligning or basecalling, most recent software should output
          these tags. For more information, consult the
          <a
            class="text-primary-500 hover:text-secondary-500"
            href="https://dieterich-lab.github.io/scimodom/bedrmod.html"
            target="_blank"
            rel="noopener noreferrer"
            >bedRMod format specification</a
          >.
        </p>
        <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25">Assembly</p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          Available assemblies for different organisms define the assembly version used in
          Sci-ModoM. Dataset that do not match the database assembly version are lifted over. Only
          chromosomes are considered.
        </p>
        <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25">Annotation</p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          Annotation are created by intersecting dataset records with features (UTRs, CDS, ...)
          merged across transcripts extracted from a given Ensembl GTF file.
        </p>
        <p class="indent-4 text-xl leading-relaxed mt-4 mb-2">
          For detailed documentation and development notes, consult the
          <a
            class="text-primary-500 hover:text-secondary-500"
            href="https://dieterich-lab.github.io/scimodom/"
            target="_blank"
            rel="noopener noreferrer"
            >server documentation</a
          >.
        </p>
      </div>
      <!-- HOW TO ----  -->
      <div class="text-justify m-6 dark:text-white/80">
        <h1 class="font-ham text-4xl font-semibold m-auto pt-4 pb-4">
          <span>Search</span>
        </h1>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          To query the database for RNA modifications, first select a modification and species, then
          available technologies. Sci-ModoM contains a large amount of records; selecting a
          particular gene or genomic region can significantly reduce the query time. The search can
          also be narrowed down by selecting a biotype or a genomic feature. Selected records can be
          exported to CSV.
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          Columns with arrow signs can be sorted. Multiple columns can be sorted, this requires a
          metaKey (<span class="italic">e.g.</span> ⌘ or Ctrl) to be pressed when clicking a header.
          A third click removes the sorting from the column.
        </p>
        <h1 class="font-ham text-4xl font-semibold m-auto pt-4 pb-4">
          <span>Browse</span>
        </h1>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          Query the database to find projects, studies and/or dataset. You can refine your search
          using global filters (top left of table), or table filters (RNA type and modification,
          organism, cell, tissue and/or organ, or technology). Click the
          <i class="pi pi-plus -ml-3 mr-1" /> button to see project-related information and
          additional attachments. A dataset can be downloaded as a bedRMod file. Records can be
          exported to CSV.
        </p>
        <h1 class="font-ham text-4xl font-semibold m-auto pt-4 pb-4">
          <span>Compare</span>
        </h1>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          Compare dataset by finding modification sites common to multiple dataset (intersection) or
          those only found in a group of dataset (difference). You can also find modification sites
          in a given dataset that are close to, but not intersecting with sites in other dataset
          (closest). You can perform these operations using available dataset, but you can also
          compare dataset with your own data.
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          <span class="font-bold">A</span> First select a given organism, then select up to 3
          reference dataset. Use the search bar (dataset dropdown) to narrow down your selection.
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          <span class="font-bold">B</span> Select up to 3 dataset for comparison. You can also use
          your own data (bedRMod or BED format). BED files with more than 6 columns are cut down to
          BED6.
          <span class="italic"
            >As of June 2024, the header information for the bedRMod format is ignored. Hence there
            is no organism and/or assembly validation (this is always the case for BED). If your
            data comes from a different assembly or an inconsistent choice of reference dataset will
            lead to spurious comparison results.
          </span>
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          <span class="font-bold">C</span> Select the operation you want to perform on the dataset
          selected in A and B. The more dataset you select or the larger the dataset, the longer the
          query time. Records can be exported to CSV.
        </p>
      </div>
      <!-- DATA MANAGEMENT ----  -->
      <div class="text-justify m-6 dark:text-white/80">
        <h1 class="font-ham text-4xl font-semibold m-auto pt-4 pb-4">
          <span>Data management</span>
        </h1>
        <p class="indent-4 text-xl leading-relaxed mt-4 mb-2">
          Sci-ModoM is freely available, and does not require login or registration. Interested
          users can however register to propose new projects, and eventually upload dataset and
          attachments that are made publicly available to all users.
        </p>
        <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25">
          Project template
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          To create a new project, fill the template request form, accessible for logged-in users
          through User menu > Data > Project template. Add a new metadata sheet for each dataset
          that belongs to this project.
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">For example:</p>
        <div class="pl-8">
          <ul class="list-disc">
            <li>
              A study generates human and mouse data, for two conditions, each in three replicates,
              using a detection technology for m6A. For this project, create two metadata sheets,
              one for human and one for mouse. Add notes if necessary. Once the project has been
              created, upload data in separate files for human and mouse, and ideally with as much
              granularity as possible, <span class="inline italic">e.g.</span> one file per
              condition and/or replicate, with appropriate information.
            </li>
            <li>
              A study generates human data using a technology to detect two different modifications.
              The resulting bedRMod file explicitely contains the modification in the 4th column.
              For this project, create two identical metadata sheets, except for the modification.
            </li>
          </ul>
        </div>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          In general, add a metadata sheet <span class="italic">(i)</span> for each dataset
          associated with a different modification, detection technology, and/or organism (incl.
          cell type, tissue, or organ), or <span class="italic">(ii)</span> for each modification
          associated with a single dataset.
        </p>
        <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25">
          Dataset upload
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          To add dataset to an existing project, fill the upload form (Upload bedRMod), accessible
          for logged-in users through User menu > Data > Dataset upload. Use the Attach BAM files
          form to upload attachments. Attaching BAM files to a given dataset allow users to access
          read-level information.
        </p>
      </div>
    </SectionLayout>
  </DefaultLayout>
</template>
