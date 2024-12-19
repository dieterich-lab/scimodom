<template>
  <div class="text-justify dark:text-white/80">
    <h1 class="font-ham text-4xl font-semibold m-auto pt-4 pb-4">
      <span>FAQs</span>
    </h1>
    <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25 font-semibold">
      Is Sci-ModoM free and open?
    </p>
    <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
      Yes, Sci-ModoM is free and open to all users and there is no login required. Interested users
      can however register to propose new projects, and eventually upload datasets that are made
      publicly available to all users. All datasets coming from the public domain are formatted to
      <a
        class="text-primary-500 hover:text-secondary-500"
        href="https://dieterich-lab.github.io/scimodom/bedrmod.html"
        target="_blank"
        rel="noopener noreferrer"
        >bedRMod</a
      >
      to facilate data sharing, minimal data lineage and better traceability.
    </p>
    <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
      In addition, Sci-ModoM is entirely open source under the GNU Affero General Public Licence
      (AGPL) version 3. Deployment can be automated and is fully reproducible.
    </p>
    <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25 font-semibold">
      Can I compare my own data securely without login?
    </p>
    <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
      Yes, use the
      <router-link :to="{ name: 'compare-docs' }">
        <span class="text-primary-500 hover:text-secondary-500">Compare</span>
      </router-link>
      tool. Login is not required. Data is handled securely.
    </p>
    <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25 font-semibold">
      Can I get more information about the bedRMod format?
    </p>
    <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
      Yes, the official specifications are available at
      <a
        href="https://dieterich-lab.github.io/euf-specs/"
        class="text-primary-500 hover:text-secondary-500"
        rel="noopener noreferrer"
        target="_blank"
      >
        EU format specifications </a
      >. Sci-ModoM imposes a few additional requirements, <span class="italic">e.g.</span>
      only chromosomes are allowed, and they must be formatted according to the Ensembl short
      format. For details, consult the
      <a
        href="https://dieterich-lab.github.io/scimodom/bedrmod.html"
        class="text-primary-500 hover:text-secondary-500"
        rel="noopener noreferrer"
        target="_blank"
      >
        bedRMod format specification (Sci-ModoM) </a
      >.
    </p>
    <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25 font-semibold">
      Can I propose new datasets?
    </p>
    <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
      Yes, but data must be quantitative <span class="italic">i.e.</span> it must minimally contain
      residue-level stoichiometric information (frequency). If possible, a score is defined as
      round(-log10(p value)), where p value is calculated from a statistical test. The coverage can
      be 0, if the number of reads at this position is not available, but it is strongly advised to
      include this information, especially if a score is not available. In principle, any
      modification is valid, as long as it is reported in
      <a
        href="https://genesilico.pl/modomics/"
        class="text-primary-500 hover:text-secondary-500"
        rel="noopener noreferrer"
        target="_blank"
      >
        Modomics </a
      >.
    </p>
    <p class="indent-4 text-lg underline underline-offset-8 decoration-gb-4/25 font-semibold">
      What are SMID and EUFID?
    </p>
    <p class="indent-4 text-lg leading-relaxed mt-2 mb-2">
      Projects are identified using a <span class="font-semibold">SMID</span> or
      <span class="font-semibold">Sci-ModoM (permanent) identifier</span>. Each project may contain
      one or more datasets. Each dataset is assigned a permanent identifier or
      <span class="font-semibold">EUFID</span>
      for
      <span class="font-semibold">Epitranscriptome Unified exchange Format (EUF) identifier</span>.
      Consult the
      <router-link :to="{ name: 'about-docs' }">
        <span class="text-primary-500 hover:text-secondary-500">Documentation</span>
      </router-link>
      for more information.
    </p>
  </div>
</template>
