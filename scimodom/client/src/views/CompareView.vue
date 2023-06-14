<script setup>
import andIcon from '@/components/icons/and.vue'

import { ref } from 'vue'

const searchBy = ref('byRegions')

const selectedModifications = ref()
const modifications = ref([
  { short_name: 'm6A', name: 'N6-methyladenosine', modomics: '6A', moiety: 'nucleoside' },
  { short_name: 'm5C', name: '5-methylcytidine', modomics: '5C', moiety: 'nucleoside' },
  { short_name: 'Y', name: 'Pseudouridine', modomics: '9U', moiety: 'nucleoside' },
  { short_name: 'Q', name: 'Queuosine', modomics: '10G', moiety: 'nucleoside' }
])

const selectedRegions = ref()
const regions = ref([
  { name: "3'UTR" },
  { name: "5'UTR" },
  { name: 'Exonic' },
  { name: 'Intronic' },
  { name: 'Intergenic'}
])
const value = ref(null);
const options = ref([
  { name: 'AND', value: 'and' },
  { name: 'OR', value: 'or' },
  { name: 'XOR', value: 'xor' },
  { name: 'NOT', value: 'not' },
]);
const selectedTechnologies = ref()
const technologies = ref([
    {
        key: '0',
        label: 'Quantification'
    },
    {
        key: '1',
        label: 'Locus-specific'
    },
    {
        key: '2',
        label: 'NGS 2nd generation',
        children: [
            {
                key: '2-0',
                label: 'Direct sequencing',
                data: 'NGS Direct',
            },
            {
                key: '2-1',
                label: 'Chemical-assisted sequencing',
                data: 'NGS Chemical-assisted',
                children: [
                    { key: '2-1-0', label: 'm6A-SAC-seq', data: 'Chemical m6A-SAC-seq' },
                    { key: '2-1-1', label: 'RiboMeth-seq', data: 'Chemical RiboMeth-seq' }
                ]
            },
            {
                key: '2-2',
                label: 'Antibody-based sequencing',
                data: 'NGS Antibody-based',
                children: [
                    { key: '2-2-0', label: 'm6A-seq/MeRIP', data: 'Antibody m6A-seq/MeRIP' }
                ]
            },
            {
                key: '2-3',
                label: 'Enzyme/protein-assisted sequencing',
                data: 'NGS Enzyme/protein-assisted',
                children: [
                    { key: '2-3-0', label: 'DART-seq', data: 'Enzyme/protein DART-seq' },
                    { key: '2-3-1', label: 'm6A-REF-seq/MAZTER-seq', data: 'Enzyme/protein m6A-REF-seq/MAZTER-seq' }
                ]
            }
        ]
    },
    {
        key: '3',
        label: 'NGS 3rd generation'
    }
])
const selectedSpecies = ref()
const species = ref([
    {
        key: '0',
        label: 'Eukaryota',
        children: [
            {
                key: '0-1',
                label: 'Animalia',
                data: 'Eukaryota Animalia',
                children: [
                    {
                        key: '0-1-0',
                        label: 'Arthropoda',
                        data: 'Animalia Arthropoda',
                    },
                    {
                        key: '0-1-1',
                        label: 'Chordata',
                        data: 'Animalia Chordata',
                        children: [
                          {
                            key: '0-1-1-0',
                            label: 'M. Musculus',
                            data: 'Chordata M. Musculus',
                            children: [
                              { key: '0-1-1-0-1', label: 'mESCs', data: 'mESCs M. Musculus'},
                              { key: '0-1-1-0-2', label: 'Heart', data: 'Heart M. Musculus'},
                            ]
                          },
                          {
                            key: '0-1-1-1',
                            label: 'H. Sapiens',
                            data: 'Chordata H. Sapiens',
                            children: [
                              { key: '0-1-1-1-1', label: 'HEK293', data: 'HEK293 H. Sapiens'},
                              { key: '0-1-1-1-2', label: 'Heart', data: 'Heart H. Sapiens'},
                              { key: '0-1-1-1-3', label: 'Liver', data: 'Liver H. Sapiens'},
                            ]
                          }
                        ]
                    },
                    {
                        key: '0-1-2',
                        label: 'Nematoda',
                        data: 'Animalia Nematoda',
                        children: [
                            { key: '0-1-2-0', label: 'C. elegans', data: 'Nematoda C. elegans' }
                        ]
                    }
                ]
            },
            {
                key: '0-2',
                label: 'Fungi',
                data: 'Eukaryota Fungi'
            },
            {
                key: '0-3',
                label: 'Plantae',
                data: 'Eukaryota Plantae'
            }
        ]
    },
    {
        key: '1',
        label: 'Prokaryota',
        children: [
            {
                key: '1-0',
                label: 'Bacteria',
                data: 'Prokaryota Bacteria',
                children: [
                            { key: '1-0-0', label: 'E. coli', data: 'Bacteria E. coli' }
                ]
            },
        ]
    },
    {
        key: '2',
        label: 'Viria'
    }
])

const genes = [
  {name: 'Agene', id: 'Aid'},
  {name: 'Bgene', id: 'Bid'},
  {name: 'Cgene', id: 'Cid'},
  {name: 'Dgene', id: 'Did'},
  {name: 'Egene', id: 'Eid'},
  {name: 'Fgene', id: 'Fid'}
]
const selectedGenes = ref()

const products = ref([
  {
      smid: '1000',
      name: 'Dataset and/or paper name 1',
      rnaType: 'mRNA',
      modification: 'm6A',
      technology: 'DART-seq',
      species: '9606',
      cto: 'Heart',
      datePublished: '2023-06-06',
      dateAdded: '2023-06-06',
      doi: '10.123456',
      pmid: '123123',
      access: 'restricted',
      assembly: 'GRCh38.p13',
      annotationSrc: 'Ensembl',
      annotationVer: '106',
      seqPlatform: 'Illumina',
      basecalling: '',
    description: '1 Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
   },
   {
      smid: '1001',
      name: 'Dataset and/or paper name 2',
      rnaType: 'mRNA',
      modification: 'm6A',
      technology: 'm6A-seq/MeRIP',
      species: '9606',
      cto: 'HEK293',
      datePublished: '2023-06-06',
      dateAdded: '2023-06-06',
      doi: '12.123456',
      pmid: '0123123',
      access: 'public',
      assembly: 'GRCh38.p13',
      annotationSrc: 'Ensembl',
      annotationVer: '106',
      seqPlatform: 'Illumina',
      basecalling: '',
     description: '2 Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
   },
     {
      smid: '1002',
      name: 'Dataset and/or paper name 3',
      rnaType: 'mRNA',
      modification: 'm6A,m5C',
      technology: 'ONT',
      species: '9606',
      cto: 'Liver',
      datePublished: '2023-06-06',
      dateAdded: '2023-06-06',
      doi: '13.123456',
      pmid: '223123',
      access: 'public',
      assembly: 'GRCh38.p13',
      annotationSrc: 'Ensembl',
      annotationVer: '106',
      seqPlatform: 'ONT',
      basecalling: '',
       description: '3 Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
   }
])
const selectedDataset = ref();

</script>

<template>
  <DefaultLayout>
    <SectionLayout>
      <h1 class="font-ham mb-4 text-3xl font-extrabold text-gray-900 md:text-5xl lg:text-6xl">
        <span
          class="text-transparent bg-clip-text bg-gradient-to-r from-crmapgreen2 from-10% via-crmapgreen1 via-40% via-crmapblue2 via-60% to-crmapblue4 to-100"
        >
          Compare
        </span>
        dataset
      </h1>
      <p class="text-lg font-normal text-gray-500 lg:text-xl">
        Perform complex queries
      </p>
      <Divider :pt="{ root: { class: 'bg-crmapgreen' } }" />

      <div>
                <Accordion :activeIndex="0">
            <AccordionTab header="Select reference dataset">
              <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="col-start-1 col-end-4">
                  <!-- <p>First choose organism</p> -->
                  <TreeSelect v-model="selectedSpecies" :options="species" placeholder="Select one organism" class="md:w-20rem" />
                </div>
                    <div>
                      <!-- display="chip" -->
                      <!-- <p>Choose modifications and methods to select dataset...</p> -->
                      <MultiSelect v-model="selectedModifications" :options="modifications" optionLabel="short_name" placeholder="Select RNA modifications"
                        :maxSelectedLabels="3" class="w-full md:w-20rem" />
                    </div>
                    <div>
                      <TreeSelect v-model="selectedTechnologies" :options="technologies" selectionMode="checkbox" placeholder="Select technologies" class="w-full md:w-20rem" />
                    </div>
                    <div class="col-start-1 col-end-4">
                      <MultiSelect v-model="selectedDataset" :options="products" filter optionLabel="name" placeholder="Select Dataset"
                        :maxSelectedLabels="3" class="w-full md:w-20rem" />
                    </div>
                  </div>
            </AccordionTab>
            <AccordionTab header="Select dataset for comparison">
              <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div>
                      <!-- display="chip" -->
                      <!-- <p>Choose modifications and methods to select dataset...</p> -->
                      <MultiSelect v-model="selectedModifications" :options="modifications" optionLabel="short_name" placeholder="Select RNA modifications"
                        :maxSelectedLabels="3" class="w-full md:w-20rem" />
                    </div>
                    <div>
                      <TreeSelect v-model="selectedTechnologies" :options="technologies" selectionMode="checkbox" placeholder="Select technologies" class="w-full md:w-20rem" />
                    </div>
                    <div class="col-start-1 col-end-4">
                      <MultiSelect v-model="selectedDataset" :options="products" filter optionLabel="name" placeholder="Select Dataset"
                        :maxSelectedLabels="3" class="w-full md:w-20rem" />
                    </div>
                  </div>
            </AccordionTab>
            <AccordionTab header="Query criteria">
              <div>
                <!-- display="chip" -->
                <MultiSelect v-model="selectedRegions" :options="regions" optionLabel="name" placeholder="select regions"
                  :maxselectedlabels="3" class="w-full md:w-20rem" />
              </div>
              <div class="block flex justify-content-center">
                <SelectButton v-model="value" :options="options" optionLabel="name" />
              </div>
              <div>
                <!-- <img src="https://github.com/dieterich-lab/scimodom/blob/master/scimodom/server/src/static/images/and.svg" alt="Image" width="250" /> -->
                <andIcon />
              </div>
            </AccordionTab>
        </Accordion>
      </div>
    </SectionLayout>
  </DefaultLayout>
</template>
