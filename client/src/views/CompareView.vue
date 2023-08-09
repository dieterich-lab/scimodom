<script setup>
import { ref, onMounted } from 'vue'
import service from '@/services/index.js'

import andIcon from '@/components/icons/and.vue'

const searchBy = ref('byRegions')

const selectedModification1 = ref()
const selectedModification2 = ref()
const modification = ref()

const region = ref()
const selectedRegion = ref()

const technology = ref()

const species = ref()
const selectedSpecies = ref()

const value = ref(null);
const options = ref([
  { name: 'AND', value: 'and' },
  { name: 'OR', value: 'or' },
  { name: 'XOR', value: 'xor' },
  { name: 'NOT', value: 'not' },
]);

const selectedTechnology1 = ref()
const selectedTechnology2 = ref()

const genes = ref()
const selectedGenes = ref()

const products = ref()

const selectedDataset1 = ref();
const selectedDataset2 = ref();

const endpoints = ['/modification', '/technology', '/species', '/region', '/genes', '/dataset']

onMounted(() => {
  service
    .getConcurrent(endpoints)
    .then(function (response) {
      modification.value = response[0].data
      technology.value = response[1].data
      species.value = response[2].data
      region.value = response[3].data
      genes.value = response[4].data
      products.value = response[5].data
    })
    .catch((error) => {
      console.log(error)
    })
})
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
                <TreeSelect v-model="selectedModification1" :options="modification" selectionMode="multiple" :metaKeySelection="false" placeholder="Select RNA modifications"
                  class="w-full md:w-20rem" />
              </div>
              <div>
                <TreeSelect v-model="selectedTechnology1" :options="technology" selectionMode="multiple" :metaKeySelection="false" placeholder="Select technologies" class="w-full md:w-20rem" />
              </div>
              <div class="col-start-1 col-end-4">
                <MultiSelect v-model="selectedDataset1" :options="products" filter optionLabel="name" placeholder="Select Dataset"
                        :maxSelectedLabels="3" class="w-full md:w-20rem" />
              </div>
            </div>
          </AccordionTab>
          <AccordionTab header="Select dataset for comparison">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <!-- display="chip" -->
                <!-- <p>Choose modifications and methods to select dataset...</p> -->
                <TreeSelect v-model="selectedModification2" :options="modification" selectionMode="multiple" :metaKeySelection="false" placeholder="Select RNA modifications"
                  :maxSelectedLabels="3" class="w-full md:w-20rem" />
              </div>
              <div>
                <TreeSelect v-model="selectedTechnology2" :options="technology" selectionMode="multiple" :metaKeySelection="false" placeholder="Select technologies" class="w-full md:w-20rem" />
              </div>
              <div class="col-start-1 col-end-4">
                <MultiSelect v-model="selectedDataset2" :options="products" filter optionLabel="name" placeholder="Select Dataset"
                  :maxSelectedLabels="3" class="w-full md:w-20rem" />
              </div>
            </div>
          </AccordionTab>
          <AccordionTab header="Query criteria">
            <div>
              <!-- display="chip" -->
              <TreeSelect v-model="selectedRegion" :options="region" selectionMode="multiple" :metaKeySelection="false" placeholder="select regions"
                :maxselectedlabels="3" class="w-full md:w-20rem" />
            </div>
            <br />
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
