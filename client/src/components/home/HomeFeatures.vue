<template>
  <SectionLayout>
    <div class="text-center m-6">
      <h1 class="font-ham text-4xl font-semibold m-auto p-4">
        <span>Features</span>
      </h1>
      <p class="text-xl font-medium text-gray-600 pt-4 pb-2">
        Sci-ModoM is under active development.
      </p>
    </div>
    <div class="grid grid-cols-3 gap-4">
      <div class="justify-center rounded-md p-4 shadow-xl">
        <i class="pi pi-file-export" />
        <div class="font-semibold mb-3 text-lg">Data Format</div>
        <p class="m-0 text-secondary font-medium">
          Support and promote the bedRMod format. This format is similar to the
          <a
            class="text-primary-500 hover:text-secondary-500"
            href="https://www.encodeproject.org/data-standards/wgbs/"
            target="_blank"
            rel="noopener noreferrer"
            >ENCODE bedMethyl</a
          >
          format (BED9+2), but includes a header.
        </p>
      </div>
      <div class="justify-center rounded-md p-4 shadow-xl">
        <i class="pi pi-database" />
        <div class="font-semibold mb-3 text-lg">Database</div>
        <p class="m-0 text-secondary font-medium">
          Starting with m6A and Ψ, we continuously add new data encompassing a wide range of
          modifications, RNA types (mRNA, tRNA, rRNA), technologies, and species.
        </p>
      </div>
      <div class="justify-center rounded-md p-4 shadow-xl">
        <i class="pi pi-chart-bar" />
        <div class="font-semibold mb-3 text-lg">Tools</div>
        <p class="m-0 text-secondary font-medium">
          Search and compare modifications across dataset. More tools coming: genome browser,
          visualization.
        </p>
      </div>
      <div class="justify-center rounded-md p-4 shadow-xl">
        <i class="pi pi-users" />
        <div class="font-semibold mb-3 text-lg">Access</div>
        <p class="m-0 text-secondary font-medium">
          Login with data upload, access management, sharing, and more.
        </p>
      </div>
      <div class="justify-center rounded-md p-4 shadow-xl">
        <i class="pi pi-comments" />
        <div class="font-semibold mb-3 text-lg">Support</div>
        <p class="m-0 text-secondary font-medium">
          Full support during the development phase. Check our
          <a
            href="https://github.com/dieterich-lab/scimodom/discussions"
            class="text-primary-500 hover:text-secondary-500"
            target="_blank"
            rel="noopener noreferrer"
            >forum</a
          >
          or
          <a
            href="mailto:boileau@uni-heidelberg.de"
            class="text-primary-500 hover:text-secondary-500"
            >contact us</a
          >
          with your feedback, request, or questions.
        </p>
      </div>
      <div class="justify-center rounded-md p-4 shadow-xl">
        <i class="pi pi-list" />
        <div class="font-semibold mb-3 text-lg">RNA processing</div>
        <p class="m-0 text-secondary font-medium">
          Integration of RNA processing and RNA-modification-aware MS data.
        </p>
      </div>
    </div>
    <div class="flex justify-center mt-8 animate-pulse">
      <RouterLink :to="{ name: 'documentation' }">
        <Button icon="pi pi-arrow-right" label="Learn more" rounded />
      </RouterLink>
    </div>
  </SectionLayout>
</template>
