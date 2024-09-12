<script setup>
import { ref, computed } from 'vue'
import { useConfirm } from 'primevue/useconfirm'
import StyledHeadline from '@/components/ui/StyledHeadline.vue'
import SubTitle from '@/components/ui/SubTitle.vue'
import ModificationSelect from '@/components/search/ModificationSelect.vue'
import SpeciesSelect from '@/components/search/SpeciesSelect.vue'
import GeneSelect from '@/components/search/GeneSelect.vue'
import BiotypeSelect from '@/components/search/BiotypeSelect.vue'
import FeatureSelect from '@/components/search/FeatureSelect.vue'
import ChromSelect from '@/components/search/ChromSelect.vue'
import SearchResults from '@/components/search/SearchResults.vue'

const confirm = useConfirm()

const selectedModification = ref()
const selectedTechnology = ref([])
const selectedOrganism = ref()
const selectionIds = ref([])
const selectedBiotypes = ref()
const selectedFeatures = ref()
const selectedGene = ref()
const selectedChrom = ref()
const selectedChromStart = ref()
const selectedChromEnd = ref()
const rnaType = ref('')
const taxaId = ref(0)
const taxaName = ref()

const isConfirmed = ref(false)
const updateCount = ref(0)

const toggleValue = ref('Modification')
const toggleOptions = ref(['Modification', 'Gene'])

const optionsDisabled = computed(
  () => selectionIds.value.length === 0 && toggleValue.value === 'Modification'
)
const queryButtonDisabled = computed(
  () =>
    optionsDisabled.value ||
    ((taxaName.value == null || needsConfirm.value) && toggleValue.value === 'Gene')
)
const needsConfirm = computed(
  () =>
    selectedGene.value == null &&
    (selectedChromStart.value == null || selectedChromEnd.value == null)
)
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
    technology: selectedTechnology.value,
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

const confirmSearch = () => {
  if (needsConfirm.value) {
    confirm.require({
      message:
        'You can narrow down your search by selecting a gene or a genomic region (chromosome start and end). Are you sure you want to proceed?',
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
</script>

<template>
  <DefaultLayout>
    <!-- SECTION -->
    <SectionLayout>
      <StyledHeadline text="Search RNA modifications" />
      <SubTitle>Select filters and query the database</SubTitle>
      <!-- TOGGLE - SEARCH SELECTION BY MODIFICATION OR GENE -->
      <Divider />
      <div>
        <SelectButton v-model="toggleValue" :options="toggleOptions" :allowEmpty="false" />
      </div>
      <Divider />
      <!-- FILTER 1 -->
      <div v-if="toggleValue === 'Modification'">
        <ModificationSelect
          v-model:selected-modification="selectedModification"
          v-model:selected-organism="selectedOrganism"
          v-model:selected-technology="selectedTechnology"
          v-model:selection-ids="selectionIds"
          v-model:selected-gene="selectedGene"
          v-model:selected-biotypes="selectedBiotypes"
          v-model:selected-features="selectedFeatures"
          v-model:selected-chrom="selectedChrom"
          v-model:selected-chrom-start="selectedChromStart"
          v-model:selected-chrom-end="selectedChromEnd"
          v-model:taxa-id="taxaId"
          v-model:taxa-name="taxaName"
          v-model:rna-type="rnaType"
        />
      </div>
      <div v-else>
        <SpeciesSelect
          v-model:selected-modification="selectedModification"
          v-model:selected-organism="selectedOrganism"
          v-model:selected-technology="selectedTechnology"
          v-model:selection-ids="selectionIds"
          v-model:selected-gene="selectedGene"
          v-model:selected-biotypes="selectedBiotypes"
          v-model:selected-features="selectedFeatures"
          v-model:selected-chrom="selectedChrom"
          v-model:selected-chrom-start="selectedChromStart"
          v-model:selected-chrom-end="selectedChromEnd"
          v-model:taxa-id="taxaId"
          v-model:taxa-name="taxaName"
          v-model:rna-type="rnaType"
        />
      </div>
      "MOD:" {{ selectedModification }} "ORG:" {{ selectedOrganism }} "TECH:"
      {{ selectedTechnology }} "SEL:" {{ selectionIds }} "TAXID:" {{ taxaId }} "NAME:"
      {{ taxaName }} "RNA:" {{ rnaType }} "SELGENE:" {{ selectedGene }} "CONFIRMED:"
      {{ isConfirmed }}, "QBD:" {{ queryButtonDisabled }}
      <!-- FILTER 2 -->
      <Divider />
      <div class="grid grid-cols-1 md:grid-cols-10 gap-6 mt-6">
        <div class="col-span-3">
          <GeneSelect
            :placeholder="
              toggleValue === 'Modification' ? 'Select gene (optional)' : '2. Select gene'
            "
            v-model="selectedGene"
            :selection-ids="selectionIds"
            :disabled="optionsDisabled || selectionIds.length === 0"
            @change="clearChrom()"
          />
        </div>
        <div class="col-span-3">
          <BiotypeSelect
            placeholder="Select biotype (optional)"
            v-model="selectedBiotypes"
            :rna-type="rnaType"
            :disabled="optionsDisabled"
          />
        </div>
        <div class="col-span-3">
          <FeatureSelect
            placeholder="Select feature (optional)"
            v-model="selectedFeatures"
            :rna-type="rnaType"
            :disabled="optionsDisabled"
          />
        </div>
        <div></div>
      </div>
      <!-- FILTER 3 -->
      <div class="grid grid-cols-1 md:grid-cols-10 gap-6 mt-6">
        <div class="col-span-3">
          <ChromSelect
            :placeholder="
              toggleValue === 'Modification'
                ? 'Select chromosome (optional)'
                : '2. Select chromosome'
            "
            v-model="selectedChrom"
            :taxa-id="taxaId"
            :disabled="optionsDisabled || !(selectedGene == null) || selectionIds.length === 0"
            @change="clearCoords()"
          />
        </div>
        <div class="col-span-3">
          <InputNumber
            @input="selectedChromEnd = null"
            v-model="selectedChromStart"
            inputId="minmax"
            :placeholder="
              toggleValue === 'Modification'
                ? 'Enter chromosome start (optional)'
                : 'Enter chromosome start'
            "
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
            :placeholder="
              toggleValue === 'Modification'
                ? 'Enter chromosome end (optional)'
                : 'Enter chromosome end'
            "
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
