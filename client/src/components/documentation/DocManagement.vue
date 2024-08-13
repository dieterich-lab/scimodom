<script setup>
import img1 from '@/assets/images/docs/management1.png'
import img2 from '@/assets/images/docs/management2.png'
import img3 from '@/assets/images/docs/management3.png'
import img4 from '@/assets/images/docs/management4.png'
import img5 from '@/assets/images/docs/management5.png'
import img6 from '@/assets/images/docs/management6.png'
</script>

<template>
  <div class="text-justify dark:text-white/80">
    <h1 class="font-ham text-4xl font-semibold m-auto pt-4 pb-4">
      <span>Data management</span>
    </h1>
    <p class="indent-4 text-xl leading-relaxed mt-4 mb-2">
      <span class="font-bold"
        >Sci-ModoM is freely available, and does not require login or registration</span
      >. Interested users can however register to propose new projects, and eventually upload
      datasets and attachments that are made publicly available to all users.
      <Message severity="info" :closable="false"
        >Feel free to contact us if you would like to suggest new data, but you do not want to
        create an account</Message
      >
    </p>
    <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25 font-semibold">
      Project template
    </p>
    <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
      To create a new project, fill the template request form, accessible for logged-in users
      through <span class="italic">User menu > Data > Project template</span>:
      <img :src="img1" class="object-center mt-6 mb-6" alt="Management: project" />
      Add a new metadata sheet for each dataset that belongs to this project:
      <img :src="img2" class="object-center mt-6 mb-6" alt="Management: metadata" />
    </p>
    <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">For example:</p>
    <div class="pl-8">
      <ul class="list-disc">
        <li>
          A study generates human and mouse data, for two conditions, each in three replicates,
          using a detection technology for m6A. For this project, create two metadata sheets, one
          for human and one for mouse. Add notes if necessary. Once the project has been created,
          upload data in separate files for human and mouse, and ideally with as much granularity as
          possible, <span class="inline italic">e.g.</span> one file per condition and/or replicate,
          with appropriate information.
        </li>
        <li>
          A study generates human data using a technology to detect two different modifications. The
          resulting bedRMod file explicitely contains the modification in the 4th column. For this
          project, create two identical metadata sheets, except for the modification.
        </li>
      </ul>
    </div>
    <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
      In general, add a metadata sheet <span class="italic">(i)</span> for each dataset associated
      with a different modification, detection technology, and/or organism (incl. cell type, tissue,
      or organ), or <span class="italic">(ii)</span> for each modification associated with a single
      dataset.
    </p>
    <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25 font-semibold">
      Dataset upload
    </p>
    <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
      To add dataset to an existing project, fill the upload form (Upload bedRMod), accessible for
      logged-in users through <span class="italic">User menu > Data > Dataset upload</span>:
      <img :src="img3" class="object-center mt-6 mb-6" alt="Management: dataset" />
      Select a SMID (available once a project request is accepted), and upload data, providing a
      meaningful title. Accepted projects are listed under
      <span class="italic">User menu > Profile > Settings</span>:
      <img :src="img6" class="object-center mt-6 mb-6" alt="Management: settings" />
      Once a dataset has been uploaded, use the Attach BAM files form to upload attachments:
      <img :src="img5" class="object-center mt-6 mb-6" alt="Management: bam" />
      Attaching BAM files to a given dataset allow users to access read-level information.
    </p>
    <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25 font-semibold">
      Dataset upload errors
    </p>
    <Message severity="warn" :closable="false"
      >bedRMod uses a 0-based, half-open coordinate system. If you use a 1-based index, no errors
      will be reported, but all your modification sites will be
      <span class="italic">off-by-one</span>!</Message
    >
    <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
      Data must be formatted according to the latest
      <a
        class="text-primary-500 hover:text-secondary-500"
        href="https://dieterich-lab.github.io/scimodom/bedrmod.html"
        target="_blank"
        rel="noopener noreferrer"
        >bedRMod format specification</a
      >. Pay particular attention to the header, which must meet strict requirements. Most errors
      are due to a badly formatted header, or a mismatch between a header tag-value pair and a
      corresponding value that you entered when filling the upload form. Most of these errors can be
      resolved quickly without the need to contact us.
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
        <li>
          mismatch between the modification name (4th column) and modification chosen at upload
        </li>
        <li>
          rows with out-of-range values or wrong types <span class="italic">e.g.</span> score (5th
          column) or frequency (11th column)
        </li>
      </ul>
    </div>
    <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
      If you get a <span class="italic">Liftover failed</span> error, it is likely that your data
      could not be lifted over (too many unmapped records). Since your data has by then been
      validated for organism, assembly, missing records, <span class="italic">etc.</span>, this is
      unlikely to happen. Please contact us in such cases.
    </p>
  </div>
</template>
