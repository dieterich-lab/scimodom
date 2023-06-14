<script setup>
import { ref, onMounted } from 'vue'
// import axios from 'axios'
import axios from '@/services/axios.js'

const searchBy = ref('byRegions')

const selectedModifications = ref()
const modifications = ref(null)

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
      label: 'Quantification',
      optionDisabled: true
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
const suggestedGenes = ref([])

const searchGenes = (event) => {
  setTimeout(() => {
    if (!event.query.trim().length) {
      suggestedGenes.value = [...genes];
    } else {
      suggestedGenes.value = genes.filter((gene) => {
        return gene.name.toLowerCase().startsWith(event.query.toLowerCase());
      });
    }
  }, 250);
}

const chroms = [
  {name: 'chr1', id: 1, size: 200709},
  {name: 'chr2', id: 2, size: 300500},
  {name: 'chr3', id: 3, size: 400000},
  {name: 'chr4', id: 4, size: 546987}
]
const selectedChrom = ref(chroms[0])
const rangeChrom = ref([1, selectedChrom.size])

const sampleResultsTable = ref([
  {
      id: '1000',
      chrom: '1',
      chromStart: '25',
      chromEnd: '26',
      name: 'm6A',
      score: '500',
      strand: '+',
      coverage: '22',
      frequency: '30',
      gene: 'Agene',
      gene_id: 'AgeneId',
      technology: 'RiboMeth-seq',
      organism: 'H. Sapiens',
      label: 'Heart'
  },
  {
      id: '1001',
      chrom: '2',
      chromStart: '125',
      chromEnd: '126',
      name: 'm6A',
      score: '600',
      strand: '-',
      coverage: '52',
      frequency: '80',
      gene: 'Bgene',
      gene_id: 'BgeneId',
      technology: 'm6A-SAC-seq',
      organism: 'H. Sapiens',
      label: 'HEK293'
  },
  {
      id: '1002',
      chrom: '1',
      chromStart: '45',
      chromEnd: '46',
      name: 'm6A',
      score: '300',
      strand: '+',
      coverage: '22',
      frequency: '70',
      gene: 'Agene',
      gene_id: 'AgeneId',
      technology: 'DART-seq',
      organism: 'H. Sapiens',
      label: 'Heart'
  },
  {
      id: '1003',
      chrom: '15',
      chromStart: '5455',
      chromEnd: '5456',
      name: 'm5C',
      score: '560',
      strand: '+',
      coverage: '456',
      frequency: '60',
      gene: 'Cgene',
      gene_id: 'CgeneId',
      technology: 'RiboMeth-seq',
      organism: 'M. Musculus',
      label: 'Heart'
  },
  {
      id: '1004',
      chrom: '3',
      chromStart: '259',
      chromEnd: '260',
      name: 'm5C',
      score: '100',
      strand: '-',
      coverage: '2',
      frequency: '10',
      gene: 'Dgene',
      gene_id: 'DgeneId',
      technology: 'm6A-seq/MeRIP',
      organism: 'M. Musculus',
      label: 'mESCs'
  }
])


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


onMounted(() => {
  axios
    .getMods()
    .then((response) => {
      // console.log('modifications:', response.data)
      modifications.value = response.data
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
          <!-- <MultiSelect v-model="selectedModifications" :options="modifications" optionDisabled="optionDisabled" optionLabel="short_name" placeholder="Select RNA modifications"
               :maxSelectedLabels="3" class="w-full md:w-20rem" /> -->
          <TreeSelect v-model="selectedModifications" :options="modifications" selectionMode="checkbox" placeholder="Select RNA modifications" class="w-full md:w-20rem" />
        </div>
      <div>
        <TreeSelect v-model="selectedTechnologies" :options="technologies" selectionMode="checkbox" placeholder="Select technologies" class="w-full md:w-20rem" />
      </div>
      <div>
        <TreeSelect v-model="selectedSpecies" :options="species" selectionMode="checkbox" placeholder="Select organisms" class="w-full md:w-20rem" />
      </div>
      <div>
        <!-- display="chip" -->
        <MultiSelect v-model="selectedRegions" :options="regions" optionLabel="name" placeholder="select regions"
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
        <h1 v-if="searchBy === 'byGenes'">
          <div class="flex flex-row">
            <AutoComplete v-model="selectedGenes" optionLabel="name" multiple :suggestions="suggestedGenes" @complete="searchGenes" class="w-full" />
          </div>
        </h1>
        <h1 v-else-if="searchBy === 'byCoords'">
          <div class="grid grid-rows-3 grid-flow-col gap-4">
            <div class="row-span-3">
              <Dropdown v-model="selectedChrom" :options="chroms" optionLabel="name" placeholder="Chromosome" />
            </div>
            <div class="col-span-2 inline-block align-middle">
              Start: {{ rangeChrom[0] }}
              End: {{ rangeChrom[1] }}
            </div>
            <div class="row-span-2 col-span-2">
              <Slider v-model="rangeChrom" range :min="1" :max="selectedChrom.size" />
            </div>
          </div>
        </h1>
        <h1 v-else ></h1>
      </div>
    </div>
    </SectionLayout>

    <SectionLayout>
    <p>SELECTED MODS:{{ selectedModifications }}</p>
    <p>SELECTED TECHS:{{ selectedTechnologies }}</p>
    <ul>
      <li v-for="check in technologies.keys(selectedTechnologies || {})">
        {{ check }}
      </li>
    </ul>
    <p>SELECTED SPECIES:{{ selectedSpecies }}</p>
    </SectionLayout>

    <!-- results table -->
    <SectionLayout>
      <div class="card">

        <!-- <DataTable :value="sampleResultsTable" stripedRows tableStyle="min-width: 50rem">
             <template #header>
             <div style="text-align:left">
             <MultiSelect :modelValue="selectedColumns" :options="columns" optionLabel="header" @update:modelValue="onToggle"
             display="chip" placeholder="Select Columns" />
             </div>
             </template>
             <Column field="code" header="Code" style="width: 20%"></Column>
             <Column field="name" header="Name" style="width: 20%"></Column>
             <Column field="price" header="Price"></Column>
             <Column field="category" header="Category" style="width: 20%"></Column>
             <Column field="quantity" header="Quantity" style="width: 20%"></Column>
             </DataTable> -->
        <DataTable :value="sampleResultsTable" ref="dt" stripedRows removableSort sortMode="multiple" :multiSortMeta="[{field: 'chrom', order: 1}, {field: 'chromStart', order: 1}]" tableStyle="min-width: 50rem">
          <template #header>
            <div style="text-align:left">
              <MultiSelect :modelValue="selectedColumns" :options="columns" optionLabel="header" @update:modelValue="onToggle"
                display="chip" placeholder="Select Columns" />
            </div>
            <div style="text-align: right">
              <Button icon="pi pi-external-link" label="Export" @click="exportCSV($event)" />
            </div>
          </template>
          <Column field="chrom" header="Chrom" sortable exportHeader="Chromosome" style="width: 20%"></Column>
          <Column field="chromStart" header="Start" sortable style="width: 20%"></Column>
          <Column field="chromEnd" header="End" sortable style="width: 20%"></Column>
          <Column field="name" header="Name" style="width: 20%"></Column>
          <Column field="score" header="Score" sortable style="width: 20%"></Column>
          <Column field="strand" header="Strand" style="width: 20%"></Column>
          <Column field="coverage" header="Coverage" sortable style="width: 20%"></Column>
          <Column field="frequency" header="Frequency" sortable style="width: 20%"></Column>
          <!-- <Column field="name" header="Name" sortable style="width: 20%"></Column> -->
          <!-- <Column field="price" header="Price" :sortable="true">
               <template #body="slotProps">
               {{ formatCurrency(slotProps.data.price) }}
               </template>
               </Column> -->
          <!-- <Column field="category" header="Category" sortable style="width: 20%"></Column> -->
          <!-- <Column field="quantity" header="Quantity" sortable style="width: 20%"></Column> -->
          <Column v-for="(col, index) of selectedColumns" :field="col.field" :header="col.header" :key="col.field + '_' + index"></Column>
        </DataTable>
      </div>
    </SectionLayout>
  </DefaultLayout>
</template>

<style scoped>
</style>
