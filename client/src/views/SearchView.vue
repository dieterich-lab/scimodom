<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useConfirm } from 'primevue/useconfirm'
import { fmtOrder, fmtFilter } from '@/utils/index.js'
import {
  updModification,
  updOrganismFromMod,
  updTechnologyFromModAndOrg,
  updSelectionFromAll
} from '@/utils/selection.js'
import { HTTP } from '@/services/API.js'
import StyledHeadline from '@/components/ui/StyledHeadline.vue'
import SubTitle from '@/components/ui/SubTitle.vue'
import ModificationInfo from '@/components/modification/ModificationInfo.vue'

const router = useRouter()
const confirm = useConfirm()

const options = ref()
const biotypes = ref()
const selectedBiotypes = ref()
const features = ref()
const selectedFeatures = ref()
const rnaType = ref()
const modification = ref()
const selectedModification = ref()
const technology = ref()
const selectedTechnology = ref()
const selectedTechnologyIds = ref([])
const organism = ref()
const selectedOrganism = ref()
const selectionIds = ref([])
const taxaId = ref()
const taxaName = ref()
const genes = ref()
const selectedGene = ref()
const filteredGenes = ref()
const chroms = ref()
const selectedChrom = ref()
const selectedChromStart = ref()
const selectedChromEnd = ref()

const dt = ref()
const first = ref(0)
const rows = ref(10)
const records = ref()
const loading = ref(false)
const totalRecords = ref(0)
const lazyParams = ref({})
const showDetails = ref(false)
const selectedSite = ref({})

const disabled = computed(() => isAllSelected())
const confirmed = computed(() => isAnyExtraSelected())

// utilities to reset options/filters
const clearCoords = () => {
  selectedChromStart.value = undefined
  selectedChromEnd.value = undefined
}
const clearChrom = () => {
  selectedChrom.value = undefined
  clearCoords()
}
const clearSelected = (value) => {
  if (value < 1) {
    selectedOrganism.value = undefined
  }
  if (value < 2) {
    selectedTechnology.value = undefined
  }
  selectedGene.value = undefined
  selectedBiotypes.value = undefined
  selectedFeatures.value = undefined
}
const clearSelection = (value) => {
  if (value < 1) {
    technology.value = undefined
  }
  if (value < 2) {
    selectionIds.value = []
  }
  records.value = undefined
  rnaType.value = undefined
}
const clearAll = (value) => {
  clearSelected(value)
  clearSelection(value)
  clearChrom()
}

// search callbacks
const updateOrganism = () => {
  // on first filter (modification) change
  clearAll(0)
  organism.value = updOrganismFromMod(options.value, selectedModification.value)
}
const updateTechnology = () => {
  // on second filter (organism) change
  clearAll(1)
  technology.value = updTechnologyFromModAndOrg(
    options.value,
    selectedModification.value,
    selectedOrganism.value
  )
}
const updateSelection = () => {
  // on third filter (technology) change
  clearAll(2)
  let result = updSelectionFromAll(
    options.value,
    selectedModification.value,
    selectedOrganism.value,
    selectedTechnology.value
  )
  selectedTechnologyIds.value = result.technology
  selectionIds.value = result.selection
  taxaId.value = result.taxaId
  taxaName.value = result.taxaName
  rnaType.value = result.rna
  if (selectionIds.value.length == 0) {
    // handle the case where all checkboxes are unticked
    selectedTechnology.value = undefined
    chroms.value = undefined
  } else {
    // get chrom.sizes
    HTTP.get(`/chroms/${taxaId.value}`)
      .then(function (response) {
        chroms.value = response.data
      })
      .catch((error) => {
        console.log(error)
      })
    HTTP.get('/genes', {
      params: {
        selection: selectionIds.value
      },
      paramsSerializer: {
        indexes: null
      }
    })
      .then(function (response) {
        genes.value = response.data.sort()
      })
      .catch((error) => {
        console.log(error)
      })
    HTTP.get(`/annotation/${rnaType.value}`)
      .then(function (response) {
        biotypes.value = response.data.biotypes
        features.value = response.data.features
      })
      .catch((error) => {
        console.log(error)
      })
  }
}
const searchGene = (event) => {
  clearChrom()
  setTimeout(() => {
    if (!event.query.trim().length) {
      filteredGenes.value = [...genes.value]
    } else {
      filteredGenes.value = genes.value.filter((g) => {
        return g.toLowerCase().startsWith(event.query.toLowerCase())
      })
    }
  }, 250)
}
const confirmSearch = () => {
  if (confirmed.value) {
    lazyLoad()
  } else {
    confirm.require({
      message:
        'You can narrow down your search by selecting a gene or a genomic region (chromosome). Are you sure you want to proceed?',
      header: 'Broad search criteria may result in large, slow-running queries!',
      accept: () => {
        lazyLoad()
      },
      reject: () => {} // do nothing
    })
  }
}

// table-related utilities
const getFileName = () => {
  let stamp = new Date()
  return 'scimodom_search_' + stamp.toISOString().replaceAll(/:/g, '')
}

const onPage = (event) => {
  lazyParams.value = event
  if (!disabled.value) {
    lazyLoad(event)
  }
}
const onSort = (event) => {
  lazyParams.value = event
  if (!disabled.value) {
    lazyLoad(event)
  }
}
const onExport = () => {
  dt.value.exportCSV()
}

const navigateTo = (eufid) => {
  router.push({ name: 'browse', params: { eufid: eufid } })
}

const onOverlay = (record) => {
  selectedSite.value = { ...record }
  showDetails.value = true
}

// functions
function isAllSelected() {
  return (
    selectedModification.value == null ||
    selectedTechnology.value == null ||
    selectedOrganism.value == null
  )
}
function isAnyExtraSelected() {
  return selectedGene.value != null || selectedChrom.value != null
}

function addOne(value) {
  return value + 1
}

function lazyLoad(event) {
  loading.value = true
  lazyParams.value = { ...lazyParams.value, first: event?.first || first.value }
  // reformat filters for gene, biotypes and features as PV table filters
  let filters = {
    // matchMode is actually hard coded to "equal" in the BE; forceSelection is toggled
    gene_name: {
      value: selectedGene.value == undefined ? null : selectedGene.value,
      matchMode: 'startsWith'
    },
    gene_biotype: {
      value: selectedBiotypes.value == undefined ? null : selectedBiotypes.value,
      matchMode: 'in'
    },
    feature: {
      value: selectedFeatures.value == undefined ? null : selectedFeatures.value,
      matchMode: 'in'
    }
  }
  HTTP.get('/modification/', {
    params: {
      modification: selectedModification.value.key,
      organism: selectedOrganism.value.key,
      technology: selectedTechnologyIds.value,
      rnaType: rnaType.value,
      taxaId: taxaId.value,
      geneFilter: fmtFilter(filters),
      chrom: selectedChrom.value == null ? null : selectedChrom.value.chrom,
      chromStart: selectedChromStart.value == null ? 0 : selectedChromStart.value,
      chromEnd:
        selectedChromEnd.value == null
          ? selectedChrom.value == null
            ? null
            : selectedChrom.value.size
          : selectedChromEnd.value,
      firstRecord: lazyParams.value.first,
      maxRecords: lazyParams.value.rows,
      multiSort: fmtOrder(lazyParams.value.multiSortMeta)
    },
    paramsSerializer: {
      indexes: null
    }
  })
    .then(function (response) {
      records.value = response.data.records
      totalRecords.value = response.data.totalRecords
      loading.value = false
    })
    .catch((error) => {
      console.log(error)
    })
}

onMounted(() => {
  lazyParams.value = {
    first: first.value,
    rows: rows.value
  }
  HTTP.get('/selections')
    .then(function (response) {
      options.value = response.data
      modification.value = updModification(options.value)
    })
    .catch((error) => {
      console.log(error)
    })
})
</script>

<template>
  <DefaultLayout>
    <!-- SECTION -->
    <SectionLayout>
      <StyledHeadline text="Search RNA modifications" />
      <SubTitle>Select filters and query the database</SubTitle>
      <!-- FILTER 1 -->
      <Divider />
      <div class="grid grid-cols-1 md:grid-cols-10 gap-6">
        <div class="col-span-3">
          <Dropdown
            @change="updateOrganism()"
            v-model="selectedModification"
            :options="modification"
            optionLabel="label"
            optionGroupLabel="label"
            optionGroupChildren="children"
            placeholder="1. Select RNA modification"
            :pt="{
              root: { class: 'w-full md:w-full' }
            }"
            :ptOptions="{ mergeProps: true }"
          />
        </div>
        <div class="col-span-3">
          <CascadeSelect
            @change="updateTechnology()"
            v-model="selectedOrganism"
            :options="organism"
            optionLabel="label"
            optionGroupLabel="label"
            :optionGroupChildren="['child1', 'child2']"
            placeholder="2. Select organism"
            :pt="{
              root: { class: 'w-full md:w-full' }
            }"
            :ptOptions="{ mergeProps: true }"
          />
        </div>
        <div class="col-span-3">
          <TreeSelect
            @change="updateSelection()"
            v-model="selectedTechnology"
            :options="technology"
            selectionMode="checkbox"
            :metaKeySelection="false"
            placeholder="3. Select technology"
            :pt="{
              root: { class: 'w-full md:w-full' }
            }"
            :ptOptions="{ mergeProps: true }"
          />
        </div>
        <div></div>
      </div>
      <!-- FILTER 2 -->
      <Divider />
      <div class="grid grid-cols-1 md:grid-cols-10 gap-6 mt-6">
        <div class="col-span-3">
          <AutoComplete
            v-model="selectedGene"
            :suggestions="filteredGenes"
            @complete="searchGene"
            forceSelection
            placeholder="4. Select gene (optional)"
            :disabled="disabled"
            :pt="{
              root: { class: 'w-full md:w-full' },
              input: { class: 'w-full md:w-full' }
            }"
            :ptOptions="{ mergeProps: true }"
          />
        </div>
        <div class="col-span-3">
          <MultiSelect
            v-model="selectedBiotypes"
            :options="biotypes"
            placeholder="5. Select biotype (optional)"
            :maxSelectedLabels="3"
            :disabled="disabled"
            :pt="{
              root: { class: 'w-full md:w-full' }
            }"
            :ptOptions="{ mergeProps: true }"
          >
          </MultiSelect>
        </div>
        <div class="col-span-3">
          <MultiSelect
            v-model="selectedFeatures"
            :options="features"
            placeholder="6. Select feature (optional)"
            :maxSelectedLabels="3"
            :disabled="disabled"
            :pt="{
              root: { class: 'w-full md:w-full' }
            }"
            :ptOptions="{ mergeProps: true }"
          >
          </MultiSelect>
        </div>
        <div></div>
      </div>
      <!-- FILTER 3 -->
      <div class="grid grid-cols-1 md:grid-cols-10 gap-6 mt-6">
        <div class="col-span-3">
          <Dropdown
            @change="clearCoords()"
            v-model="selectedChrom"
            :options="chroms"
            optionLabel="chrom"
            showClear
            :disabled="disabled || !(selectedGene == null)"
            placeholder="7. Select chromosome (optional)"
            :pt="{
              root: { class: 'w-full md:w-full' }
            }"
            :ptOptions="{ mergeProps: true }"
          />
        </div>
        <div class="col-span-3">
          <InputNumber
            @input="selectedChromEnd = null"
            v-model="selectedChromStart"
            inputId="minmax"
            placeholder="8. Enter chromosome start (optional)"
            :disabled="selectedChrom == null"
            :min="0"
            :max="selectedChrom == null ? 0 : selectedChrom.size - 1"
            :pt="{
              root: { class: 'w-full md:w-full' }
            }"
            :ptOptions="{ mergeProps: true }"
          />
        </div>
        <div class="col-span-3">
          <InputNumber
            v-model="selectedChromEnd"
            inputId="minmax"
            :disabled="selectedChromStart == null"
            placeholder="9. Enter chromosome end (optional)"
            :min="selectedChromStart == null ? 0 : selectedChromStart + 1"
            :max="selectedChrom == null ? 0 : selectedChrom.size"
            :pt="{
              root: { class: 'w-full md:w-full' }
            }"
            :ptOptions="{ mergeProps: true }"
          />
        </div>
        <ConfirmDialog></ConfirmDialog>
        <div class="place-self-end">
          <Button
            type="button"
            size="small"
            icon="pi pi-sync"
            label="Query"
            :disabled="disabled"
            :loading="loading"
            @click="confirmSearch()"
          />
        </div>
      </div>
    </SectionLayout>
    <!-- SECTION -->
    <SectionLayout>
      <!-- TABLE -->
      <div>
        <DataTable
          :value="records"
          dataKey="id"
          ref="dt"
          :exportFilename="getFileName()"
          lazy
          paginator
          :totalRecords="totalRecords"
          :loading="loading"
          :first="first"
          :rows="rows"
          @page="onPage($event)"
          @sort="onSort($event)"
          removableSort
          sortMode="multiple"
          stripedRows
        >
          <template #header>
            <div style="text-align: right">
              <Button
                icon="pi pi-external-link"
                size="small"
                label="Export"
                severity="secondary"
                raised
                @click="onExport($event)"
                :disabled="disabled"
              />
            </div>
          </template>
          <template #empty>
            <p class="text-center text-secondary-500 font-semibold">
              No records match your search criteria!
            </p>
          </template>
          <template #loading>
            <ProgressSpinner style="width: 60px; height: 60px" strokeWidth="6" />
          </template>
          <Column field="chrom" header="Chrom" sortable exportHeader="chrom"></Column>
          <Column field="start" header="Start" sortable exportHeader="chromStart">
            <template #body="{ data }">
              <a
                class="text-primary-500 hover:text-secondary-500"
                :href="
                  'https://www.ensembl.org/' +
                  taxaName.replace(/ /g, '_') +
                  '/Location/View?r=' +
                  data.chrom +
                  ':' +
                  data.start +
                  '-' +
                  addOne(data.end) +
                  ';db=core'
                "
                target="_blank"
                rel="noopener noreferrer"
                >{{ data.start }}
              </a>
            </template>
          </Column>
          <Column field="end" header="End" exportHeader="chromEnd"></Column>
          <Column field="name" header="Name" exportHeader="name">
            <template #body="{ data }">
              <a
                class="text-primary-500 hover:text-secondary-500"
                :href="'https://www.genesilico.pl/modomics/modifications/' + data.reference_id"
                target="_blank"
                rel="noopener noreferrer"
                >{{ data.name }}
              </a>
            </template>
          </Column>
          <Column field="score" header="Score" sortable exportHeader="score"></Column>
          <Column field="strand" header="Strand" exportHeader="strand"></Column>
          <Column field="coverage" header="Coverage" sortable exportHeader="coverage"></Column>
          <Column field="frequency" header="Frequency" sortable exportHeader="frequency"></Column>
          <Column field="dataset_id" header="EUFID" exportHeader="EUFID">
            <template #body="{ data }">
              <Button
                size="small"
                :label="data.dataset_id"
                severity="secondary"
                text
                @click="navigateTo(data.dataset_id)"
              />
            </template>
          </Column>
          <Column field="tech" header="Technology" exportHeader="Technology"></Column>
          <!-- export only -->
          <Column field="taxa_id" exportHeader="Organism" style="display: none"></Column>
          <Column field="cto" exportHeader="Cell/Tissue" style="display: none"></Column>
          <!-- export only -->
          <Column field="feature" header="Feature" exportHeader="Feature"></Column>
          <Column field="gene_name" header="Gene" exportHeader="Gene"></Column>
          <Column field="gene_biotype" header="Biotype" exportHeader="Biotype"></Column>
          <Column :exportable="false" style="width: 5%">
            <template #body="slotProps">
              <Button
                icon="pi pi-plus"
                outlined
                rounded
                severity="secondary"
                @click="onOverlay(slotProps.data)"
              />
            </template>
          </Column>
        </DataTable>
        <ModificationInfo v-model:visible="showDetails" :site="selectedSite" />
      </div>
    </SectionLayout>
  </DefaultLayout>
</template>

<style scoped></style>
