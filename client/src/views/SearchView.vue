<script setup>
import { ref, computed, onMounted } from 'vue'
import { useConfirm } from 'primevue/useconfirm'
import {
  updModification,
  updOrganismFromMod,
  updTechnologyFromModAndOrg,
  updSelectionFromAll
} from '@/utils/selection.js'
import { HTTP } from '@/services/API.js'
import StyledHeadline from '@/components/ui/StyledHeadline.vue'
import SubTitle from '@/components/ui/SubTitle.vue'
import GeneSelect from '@/components/search/GeneSelect.vue'
import BiotypeSelect from '@/components/search/BiotypeSelect.vue'
import FeatureSelect from '@/components/search/FeatureSelect.vue'
import ChromSelect from '@/components/search/ChromSelect.vue'
import SearchResults from '@/components/search/SearchResults.vue'

const confirm = useConfirm()

const all_selections = ref()
const selectedBiotypes = ref()
const selectedFeatures = ref()
const rnaType = ref('')
const modification = ref()
const selectedModification = ref()
const technology = ref()
const selectedTechnology = ref()
const selectedTechnologyIds = ref([])
const organism = ref()
const selectedOrganism = ref()
const selectionIds = ref([])
const taxaId = ref(0)
const taxaName = ref()
const selectedGene = ref()
const selectedChrom = ref()
const selectedChromStart = ref()
const selectedChromEnd = ref()

const isConfirmed = ref(false)
const updateCount = ref(0)

const queryButtonDisabled = computed(
  () =>
    selectedModification.value == null ||
    selectedTechnology.value == null ||
    selectedOrganism.value == null
)
const needsConfirm = computed(() => selectedGene.value == null && selectedChrom.value == null)
const resultsDisabled = computed(() => queryButtonDisabled.value || !isConfirmed.value)
const searchParameters = computed(() => getSearchParameters())

function getSearchParameters() {
  const chromEnd =
    selectedChromEnd.value != null
      ? selectedChromEnd.value
      : selectedChrom.value != null
      ? selectedChrom.value.size
      : null
  return {
    modification: selectedModification.value?.key,
    organism: selectedOrganism.value?.key,
    technology: selectedTechnologyIds.value,
    rnaType: rnaType.value,
    taxaId: taxaId.value,
    chrom: selectedChrom.value == null ? null : selectedChrom.value.chrom,
    chromStart: selectedChromStart.value == null ? 0 : selectedChromStart.value,
    chromEnd: chromEnd,
    geneName: selectedGene.value === undefined ? null : selectedGene.value,
    geneBiotype: selectedBiotypes.value === undefined ? null : selectedBiotypes.value,
    feature: selectedFeatures.value === undefined ? null : selectedFeatures.value
  }
}

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
  isConfirmed.value = false
}
const clearSelection = (value) => {
  if (value < 1) {
    technology.value = undefined
  }
  if (value < 2) {
    selectionIds.value = []
  }
  rnaType.value = ''
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
  organism.value = updOrganismFromMod(all_selections.value, selectedModification.value)
}
const updateTechnology = () => {
  // on second filter (organism) change
  clearAll(1)
  technology.value = updTechnologyFromModAndOrg(
    all_selections.value,
    selectedModification.value,
    selectedOrganism.value
  )
}
const updateSelection = () => {
  // on third filter (technology) change
  clearAll(2)
  let result = updSelectionFromAll(
    all_selections.value,
    selectedModification.value,
    selectedOrganism.value,
    selectedTechnology.value
  )
  selectedTechnologyIds.value = result.technology
  selectionIds.value = result.selection
  taxaId.value = result.taxaId
  taxaName.value = result.taxaName
  rnaType.value = result.rna
  if (selectionIds.value.length === 0) {
    // handle the case where all checkboxes are unticked
    selectedTechnology.value = undefined
  }
}

const confirmSearch = () => {
  if (needsConfirm.value) {
    confirm.require({
      message:
        'You can narrow down your search by selecting a gene or a genomic region (chromosome). Are you sure you want to proceed?',
      header: 'Broad search criteria may result in large, slow-running queries!',
      accept: () => {
        isConfirmed.value = true
        updateCount.value += 1
      },
      reject: () => {} // do nothing
    })
  } else {
    isConfirmed.value = true
    updateCount.value += 1
  }
}

// functions

onMounted(() => {
  HTTP.get('/selections')
    .then(function (response) {
      all_selections.value = response.data
      modification.value = updModification(all_selections.value)
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
          <GeneSelect
            placeholder="4. Select gene (optional)"
            v-model="selectedGene"
            :selection-ids="selectionIds"
            :disabled="queryButtonDisabled"
            @change="clearChrom()"
          />
        </div>
        <div class="col-span-3">
          <BiotypeSelect
            placeholder="5. Select biotype (optional)"
            v-model="selectedBiotypes"
            :rna-type="rnaType"
            :disabled="queryButtonDisabled"
          />
        </div>
        <div class="col-span-3">
          <FeatureSelect
            placeholder="6. Select feature (optional)"
            v-model="selectedFeatures"
            :rna-type="rnaType"
            :disabled="queryButtonDisabled"
          />
        </div>
        <div></div>
      </div>
      <!-- FILTER 3 -->
      <div class="grid grid-cols-1 md:grid-cols-10 gap-6 mt-6">
        <div class="col-span-3">
          <ChromSelect
            placeholder="7. Select chromosome (optional)"
            v-model="selectedChrom"
            :taxa-id="taxaId"
            :disabled="queryButtonDisabled || !(selectedGene == null)"
            @change="clearCoords()"
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
            :disabled="queryButtonDisabled"
            @click="confirmSearch()"
          />
        </div>
      </div>
    </SectionLayout>
    <!-- SECTION -->
    <SectionLayout>
      <SearchResults
        :search-parameters="searchParameters"
        :taxa-name="taxaName"
        :disabled="resultsDisabled"
        :key="updateCount"
      />
    </SectionLayout>
  </DefaultLayout>
</template>

<style scoped></style>
