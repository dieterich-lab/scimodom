<script setup>
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
</script>

<template>
  <DefaultLayout>
    <SectionLayout>
      <h1 class="font-ham mb-4 text-3xl font-extrabold text-gray-900 md:text-5xl lg:text-6xl">
        <span
          class="text-transparent bg-clip-text bg-gradient-to-r from-crmapgreen2 from-10% via-crmapgreen1 via-40% via-crmapblue2 via-60% to-crmapblue4 to-100"
        >
          Search
        </span>
        RNA modifications
      </h1>
      <p class="text-lg font-normal text-gray-500 lg:text-xl">
        Select filters and query the database
      </p>
      <Divider :pt="{ root: { class: 'bg-crmapgreen' } }" />
      <!-- <div class="flex flex-row flex-wrap justify-start place-items-center [&>*]:mr-6"> -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
        <!-- display="chip" -->
        <MultiSelect v-model="selectedModifications" :options="modifications" optionLabel="short_name" placeholder="Select RNA modifications"
          :maxSelectedLabels="3" class="w-full md:w-20rem" />
      </div>
      <div>
        <TreeSelect v-model="selectedTechnologies" :options="technologies" selectionMode="checkbox" placeholder="Select technologies" class="w-full md:w-20rem" />
      </div>
      <div>
        <TreeSelect v-model="selectedSpecies" :options="species" selectionMode="checkbox" placeholder="Select organisms" class="w-full md:w-20rem" />
      </div>
      <div>
        <!-- display="chip" -->
        <MultiSelect v-model="selectedRegions" :options="regions" optionLabel="name" placeholder="Select regions"
          :maxselectedlabels="3" class="w-full md:w-20rem" />
      </div>
      <div class="flex flex-wrap justify-evenly content-center">
      <div>
        <RadioButton v-model="searchBy" inputId="byRegions" name="byRegions" value="byRegions" />
        <label for="byRegions" class="ml-2">Regions</label>
      </div>
      <div>
        <RadioButton v-model="searchBy" inputId="byGenes" name="byGenes" value="byGenes" />
        <label for="byGenes" class="ml-2">Genes</label>
      </div>
      <div>
        <RadioButton v-model="searchBy" inputId="byCoords" name="byCoords" value="byCoords" />
        <label for="byCoords" class="ml-2">Coordinates</label>
      </div>
      </div>
      <div>
        <h1 v-if="searchBy === 'byGenes'">Genes</h1>
        <h1 v-else-if="searchBy === 'byCoords'">Coords</h1>
        <h1 v-else ></h1> 
      </div>
    </div>
    </SectionLayout>
  </DefaultLayout>
</template>

<style scoped>
</style>
