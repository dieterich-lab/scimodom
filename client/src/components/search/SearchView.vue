<script setup lang="ts">
import { ref } from 'vue'
import Divider from 'primevue/divider'
import SelectButton from 'primevue/selectbutton'
import StyledHeadline from '@/components/ui/StyledHeadline.vue'
import SubTitle from '@/components/ui/SubTitle.vue'
import DefaultLayout from '@/components/layout/DefaultLayout.vue'
import SectionLayout from '@/components/layout/SectionLayout.vue'
import PrimaryParametersByModification from '@/components/search/PrimaryParametersByModification.vue'
import PrimaryParametersByGeneChrom from '@/components/search/PrimaryParametersByGeneChrom.vue'
import SecondarySearchParametersForm from '@/components/search/SecondarySearchParametersForm.vue'
import SearchResults from '@/components/search/SearchResults.vue'
import {
  type SearchBy,
  type PrimarySearchParameters,
  type SearchParameters,
  type DummySearchParameters
} from '@/utils/search'

const DUMMY_SEARCH_PARAMETERS: DummySearchParameters = {
  searchBy: 'Modification',
  state: 'incomplete'
}

const SEARCH_BY_OPTIONS: SearchBy[] = ['Modification', 'Gene/Chrom']

const searchByValue = ref<SearchBy>('Modification')
const primarySearchParameters = ref<PrimarySearchParameters | null>(null)
const searchParameters = ref<SearchParameters | DummySearchParameters>(DUMMY_SEARCH_PARAMETERS)
const confirmedSearchParameters = ref<SearchParameters | null>(null)
const queryRevision = ref<number>(0)

function updatePrimaryParameters(params: PrimarySearchParameters | null) {
  primarySearchParameters.value = params
  if (params === null) {
    resetSearchParameters()
  } else {
    searchParameters.value = {
      ...params,
      searchBy: searchByValue.value,
      state: 'complete'
    }
  }
}

function resetSearchParameters() {
  searchParameters.value = { ...DUMMY_SEARCH_PARAMETERS, searchBy: searchByValue.value }
}

function submit(params: SearchParameters) {
  confirmedSearchParameters.value = params
  queryRevision.value += 1
}

function changeSearchBy() {
  resetSearchParameters()
  confirmedSearchParameters.value = null
  queryRevision.value += 1
}
</script>

<template>
  <DefaultLayout>
    <!-- SECTION -->
    <SectionLayout>
      <StyledHeadline text="Search RNA modifications" />
      <SubTitle>Query by modification, gene or genomic region</SubTitle>
      <Divider />
      <div>
        <SelectButton
          v-model="searchByValue"
          :options="SEARCH_BY_OPTIONS"
          :allowEmpty="false"
          @change="changeSearchBy"
        />
      </div>
      <Divider />

      <div v-if="searchByValue === 'Modification'">
        <PrimaryParametersByModification @change="updatePrimaryParameters" />
      </div>
      <div v-else>
        <PrimaryParametersByGeneChrom @change="updatePrimaryParameters" />
      </div>

      <Divider />
      <SecondarySearchParametersForm v-model="searchParameters" @submit="submit" />
    </SectionLayout>
    <SectionLayout>
      <SearchResults :search-parameters="confirmedSearchParameters" :key="queryRevision" />
    </SectionLayout>
  </DefaultLayout>
</template>
