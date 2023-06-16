<script setup>
import { ref, onMounted } from 'vue'
import service from '@/services/index.js'

const modification = ref()
const selectedModification = ref()

const region = ref()
const selectedRegion = ref()

const technology = ref()
const selectedTechnology = ref()

const species = ref()
const selectedSpecies = ref()

const genes = ref()
const selectedGenes = ref()
const suggestedGenes = ref([])

const sampleResultsTable = ref()

const chroms = [
  {name: 'chr1', id: 1, size: 200709},
  {name: 'chr2', id: 2, size: 300500},
  {name: 'chr3', id: 3, size: 400000},
  {name: 'chr4', id: 4, size: 546987}
]
const selectedChrom = ref(chroms[0])
const rangeChrom = ref([1, selectedChrom.size])

const columns = ref([
  {field: 'gene', header: 'Gene'},
  {field: 'gene_id', header: 'Gene ID'},
  {field: 'technology', header: 'Technology'},
  {field: 'organism', header: 'Organism'},
  {field: 'label', header: 'Cell/Tissue'}
])
const selectedColumns = ref(columns.value)
const onToggle = (val) => {
  selectedColumns.value = columns.value.filter(col => val.includes(col));
}

const dt = ref()
const exportCSV = () => {
  dt.value.exportCSV()
}

const endpoints = ['/modification', '/technology', '/species', '/region', '/eufext', '/genes']

onMounted(() => {
  service
    .getConcurrent(endpoints)
    .then(function (response) {
      modification.value = response[0].data
      technology.value = response[1].data
      species.value = response[2].data
      region.value = response[3].data
      sampleResultsTable.value = response[4].data
      genes.value = response[5].data
    })
    .catch((error) => {
      console.log(error)
    })
})

const searchGenes = (event) => {
  setTimeout(() => {
    if (!event.query.trim().length) {
      suggestedGenes.value = [...genes];
    } else {
      suggestedGenes.value = genes.value.filter((gene) => {
        return gene.name.toLowerCase().startsWith(event.query.toLowerCase());
      });
    }
  }, 250);
}
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
      <!-- FILTER 1 -->
      <Divider :pt="{ root: { class: 'bg-crmapgreen' } }" />
      <!-- <div class="flex flex-row flex-wrap justify-start place-items-center [&>*]:mr-6"> -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <TreeSelect
            v-model="selectedModification"
            :options="modification"
            selectionMode="multiple"
            :metaKeySelection="false"
            placeholder="1. Select RNA modifications"
            class="w-full md:w-20rem"
          />
        </div>
        <div>
          <TreeSelect
            v-model="selectedTechnology"
            :options="technology"
            selectionMode="multiple"
            :metaKeySelection="false"
            placeholder="2. Select technologies"
            class="w-full md:w-20rem"
          />
        </div>
        <div>
          <TreeSelect
            v-model="selectedSpecies"
            :options="species"
            selectionMode="multiple"
            :metaKeySelection="false"
            placeholder="3. Select organisms"
            class="w-full md:w-20rem"
          />
        </div>
      </div>
      <!-- FILTER 2 -->
      <Divider :pt="{ root: { class: 'bg-crmapgreen' } }" />
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <TreeSelect
            v-model="selectedRegion"
            :options="region"
            selectionMode="multiple"
            :metaKeySelection="false"
            placeholder="4. Select regions"
            class="w-full md:w-20rem"
          />
        </div>
        <div>
          <AutoComplete
            v-model="selectedGenes"
            optionLabel="name"
            multiple
            :suggestions="suggestedGenes"
            @complete="searchGenes"
            placeholder="Limit search to these genes..."
            class="w-full md:w-20rem"
          />
        </div>
        <div class="grid grid-cols-3 gap-4">
          <div>
            <Dropdown
              v-model="selectedChrom"
              :options="chroms"
              optionLabel="name"
              placeholder="Chromosome"
            />
          </div>
          <!-- <div>
               <InputMask id="coordStart" v-model="rangeChromStart" mask="9?99999" placeholder="9?99999" />
               </div>
               <div>
               <InputMask id="coordEnd" v-model="rangeChromEnd" mask="9?99999" placeholder="9?99999" />
               </div> -->
        </div>
      </div>
    </SectionLayout>

    <SectionLayout>
      <ul>
        <li v-for="check in Object.keys(selectedModification || {})">
          {{check}}
        </li>
      </ul>
    <p>SELECTED MODS:{{ selectedModification }}</p>
    <ul>
      <li v-for="check in Object.keys(selectedTechnology || {})">
        {{check}}
      </li>
    </ul>
    <p>SELECTED TECHS:{{ selectedTechnology }}</p>
    <!-- <ul>
         <li v-for="check in technology.keys(selectedTechnology || {})">
         {{ check }}
         </li>
         </ul> -->
    <p>SELECTED SPECIES:{{ selectedSpecies }}</p>
    <p>SELECTED REGIONS:{{ selectedRegion }}</p>
    </SectionLayout>

    <!-- results table -->
    <SectionLayout>
      <div class="card">
        <DataTable
          :value="sampleResultsTable"
          ref="dt"
          stripedRows
          removableSort
          sortMode="multiple"
          :multiSortMeta="[{field: 'chrom', order: 1}, {field: 'start', order: 1}]"
          paginator
          :rows="5"
          tableStyle="min-width: 50rem">
          <template #header>
            <div style="text-align:left">
              <MultiSelect
                :modelValue="selectedColumns"
                :options="columns"
                optionLabel="header"
                @update:modelValue="onToggle"
                display="chip"
                placeholder="Select Columns"
              />
            </div>
            <div style="text-align: right">
              <Button icon="pi pi-external-link" label="Export" @click="exportCSV($event)" />
            </div>
          </template>
          <Column field="chrom" header="Chrom" sortable exportHeader="Chromosome" style="width: 20%"></Column>
          <Column field="start" header="Start" sortable style="width: 20%"></Column>
          <Column field="end" header="End" sortable style="width: 20%"></Column>
          <Column field="name" header="Name" style="width: 20%"></Column>
          <Column field="score" header="Score" sortable style="width: 20%"></Column>
          <Column field="strand" header="Strand" style="width: 20%"></Column>
          <Column field="coverage" header="Coverage" sortable style="width: 20%"></Column>
          <Column field="frequency" header="Frequency" sortable style="width: 20%"></Column>
          <Column v-for="(col, index) of selectedColumns" :field="col.field" :header="col.header" :key="col.field + '_' + index"></Column>
        </DataTable>
      </div>
    </SectionLayout>
  </DefaultLayout>
</template>

<style scoped>
</style>
