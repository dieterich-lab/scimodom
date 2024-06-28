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
          Sci-ModoM is a quantitative database of RNA modification sites derived from
          high-throughput sequencing experiments. It is dedicated to novel assays that provide
          transcriptome-wide information at single-base resolution. An intuitive user–interface
          allows to <span class="italic">Search</span> and
          <span class="italic">Compare</span> modifications site-wise or across whole datasets, and
          to <span class="italic">Browse</span> through or download datasets and retrieve the
          associated metadata.
        </p>
        <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25 font-semibold">
          Query nomenclature
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          Sci-ModoM allows to query RNA modification sites according to RNA type, species,
          technology, and genomic features (<span class="italic">Search</span>). The classification
          of detection technologies is based on the underlying assay,
          <span class="italic">e.g.</span>
          antibody-based, chemically- or enzymatically-treated, or direct read-out (Nanopore).
        </p>
        <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25 font-semibold">
          Project and dataset
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          Data is also accessible at the study- or dataset-level (<span class="italic">Browse</span
          >). One or more dataset can belong to a study or project,
          <span class="italic">e.g.</span> dataset "Wildtype HEK293T" and "Wildtype mESC" belong to
          the "GLORI" project. Each dataset is assigned a
          <span class="font-semibold">EUFID</span> or
          <span class="font-semibold"
            >Epitranscriptome Unified exchange Format (EUF) identifier</span
          >. Projects are identified using a <span class="font-semibold">SMID</span> or
          <span class="font-semibold">Sci-ModoM identifier</span>. A dataset can include one or more
          modification, but is uniquely associated with a given species (including cell type,
          tissue, or organ) and technology.
        </p>
        <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25 font-semibold">
          bedRMod format
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          Simply put, a dataset consists of per-site records of RNA modifications stored in a given
          bedRMod file. This file contains a formatted header with metadata, followed by distinct
          RNA modification sites, one per line. For more information, consult the
          <a
            class="text-primary-500 hover:text-secondary-500"
            href="https://dieterich-lab.github.io/scimodom/bedrmod.html"
            target="_blank"
            rel="noopener noreferrer"
            >bedRMod format specification</a
          >.
        </p>
        <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25 font-semibold">
          Assembly
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          Only one genome assembly version per species is used in Sci-ModoM. Dataset that do not
          match the database assembly version are lifted over. Only chromosome-level information is
          considered; unassigned contigs or scaffolds are discarded.
        </p>
        <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25 font-semibold">
          Annotation
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          Datasets are annotated with gene informations and genomic features (UTRs, CDS, ...) using
          a fixed version of Ensembl.
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
        <p class="indent-4 text-xl leading-relaxed mt-4 mb-2">
          Consult our development plan for 2024
          <RouterLink class="pl-2 animate-pulse" :to="{ name: 'roadmap' }">
            <!-- <a class="pl-2 animate-pulse" href="https://www.trr319-rmap.de" target="_blank" rel="noopener noreferrer"> -->
            <Button icon="pi pi-arrow-right" size="small" label="Learn more" rounded />
          </RouterLink>
        </p>
      </div>
      <!-- HOW TO -->
      <div class="text-justify m-6 dark:text-white/80">
        <h1 class="font-ham text-4xl font-semibold m-auto pt-4 pb-4">
          <span>Search</span>
        </h1>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          Search modifications site-wise across whole transcriptomes. To query the database, first
          select a modification and species, then available technologies. Some dataset may contain a
          large amount of records; selecting a particular gene of interest or a genomic region can
          significantly reduce the query time. The search can also be narrowed down by selecting a
          biotype or a genomic feature. Selected records can be exported to CSV. To download all
          records for a given dataset, use
          <span class="italic">Browse</span>.
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
          Query the database to find projects and/or datasets. You can refine your search using
          global filters (top left of table), or table filters (RNA type and modification, organism,
          cell, tissue and/or organ, or technology). Click the
          <i class="pi pi-plus -ml-3 mr-1" /> button to see project-related information and
          additional attachments. A dataset can be downloaded as a
          <a
            class="text-primary-500 hover:text-secondary-500"
            href="https://dieterich-lab.github.io/scimodom/bedrmod.html"
            target="_blank"
            rel="noopener noreferrer"
            >bedRMod</a
          >
          file. The list of datasets and their metadata can be exported to CSV.
        </p>
        <h1 class="font-ham text-4xl font-semibold m-auto pt-4 pb-4">
          <span>Compare</span>
        </h1>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          Compare datasets site-wise, including your own, without registration or login. You can
          compare datasets to one another by finding modification sites common to multiple datasets
          (intersection) or those only found in a group of datasets (difference). You can also find
          modification sites in a given dataset that are close to, but not intersecting with sites
          in other datasets (closest). You can perform these operations strand-aware or unaware. You
          can use available datasets, or upload your own data to compare it against database
          records. You data is securely handled and is automatically deleted afterwards.
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          <span class="font-bold">1.</span> First select a given organism, then select up to 3
          reference dataset. Use the search bar (dataset dropdown) to narrow down your selection.
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          <span class="font-bold">2.</span> Select up to 3 dataset for comparison. You can also use
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
          <span class="font-bold">3.</span> Select the operation you want to perform on the dataset
          selected in previous steps. The more dataset you select or the larger the dataset, the
          longer the query time. Records can be exported to CSV.
        </p>
      </div>
      <!-- DATA MANAGEMENT -->
      <div class="text-justify m-6 dark:text-white/80">
        <h1 class="font-ham text-4xl font-semibold m-auto pt-4 pb-4">
          <span>Data management</span>
        </h1>
        <p class="indent-4 text-xl leading-relaxed mt-4 mb-2">
          <span class="font-bold"
            >Sci-ModoM is freely available, and does not require login or registration</span
          >. Interested users can however register to propose new projects, and eventually upload
          datasets and attachments that are made publicly available to all users.
        </p>
        <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25 font-semibold">
          Project template
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          To create a new project, fill the template request form, accessible for logged-in users
          through <span class="italic">User menu > Data > Project template</span>. Add a new
          metadata sheet for each dataset that belongs to this project.
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
        <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25 font-semibold">
          Dataset upload
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          To add dataset to an existing project, fill the upload form (Upload bedRMod), accessible
          for logged-in users through <span class="italic">User menu > Data > Dataset upload</span>.
          Use the Attach BAM files form to upload attachments. Attaching BAM files to a given
          dataset allow users to access read-level information.
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          <a
            class="text-primary-500 hover:text-secondary-500"
            href="https://dieterich-lab.github.io/scimodom/bedrmod.html"
            target="_blank"
            rel="noopener noreferrer"
            >bedRMod</a
          >
          uses a 0-based, half-open coordinate system. If you use a 1-based index, all your
          modification sites will be <span class="italic">off-by-one</span>!
        </p>
        <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25 font-semibold">
          Dataset upload errors
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          Data must be formatted according to the latest
          <a
            class="text-primary-500 hover:text-secondary-500"
            href="https://dieterich-lab.github.io/scimodom/bedrmod.html"
            target="_blank"
            rel="noopener noreferrer"
            >bedRMod format specification</a
          >. Pay particular attention to the header, which must meet strict requirements. Most
          errors are due to a badly formatted header, or a mismatch between a header tag-value pair
          and a corresponding value that you entered when filling the upload form. Most of these
          errors can be resolved quickly without the need to contact us.
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          If you get a
          <span class="italic">File upload failed. Too many skipped records</span> error, this is
          generally due one of the following:
        </p>
        <div class="pl-8">
          <ul class="list-disc">
            <li>wrong format for chromosome (1st column)</li>
            <li>too many contigs/scaffolds (only chromosomes are used)</li>
            <li>wrong modification name (4th column)</li>
            <li>mismatch between the modification name (4th column) and that chosen at upload</li>
            <li>
              too many rows with out-of-range values <span class="italic">e.g.</span> score (5th
              column) or frequency (11th column)
            </li>
          </ul>
        </div>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
          If you get a <span class="italic">Liftover failed</span> error, it is likely that your
          data could not be lifted over (too many unmapped records). Since your data has by then
          been validated for organism, assembly, missing records, <span class="italic">etc.</span>,
          this is unlikely to happen. Please contact us in such cases.
        </p>
      </div>
    </SectionLayout>
  </DefaultLayout>
</template>
