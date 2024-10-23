<script setup lang="ts">
import { ref, computed } from 'vue'
import { useConfirm } from 'primevue/useconfirm'
import StyledHeadline from '@/components/ui/StyledHeadline.vue'
import SubTitle from '@/components/ui/SubTitle.vue'
import DefaultLayout from '@/components/layout/DefaultLayout.vue'
import SectionLayout from '@/components/layout/SectionLayout.vue'
import ModificationSelectForm from '@/components/search/ModificationSelectForm.vue'
import SpeciesSelectForm from '@/components/search/SpeciesSelectForm.vue'
import SecondarySearchParametersForm from '@/components/search/SecondarySearchParametersForm.vue'
import SearchResults from '@/components/search/SearchResults.vue'
import {
  type SearchBy,
  type PrimarySearchParameters,
  type SearchParameters,
  type DummySearchParameters,
  isSearchParameter
} from '@/utils/search'

const DUMMY_SEARCH_PARAMETERS: DummySearchParameters = {
  searchBy: 'Modification',
  state: 'incomplete'
}

const SEARCH_BY_OPTIONS: SearchBy[] = ['Modification', 'Gene/Chrom']

const confirm = useConfirm()

const searchByValue = ref<SearchBy>('Modification')
const primarySearchParameters = ref<PrimarySearchParameters | null>(null)
const searchParameters = ref<SearchParameters | DummySearchParameters>(DUMMY_SEARCH_PARAMETERS)
const confirmedSearchParameters = ref<SearchParameters | null>(null)
const isConfirmed = ref(false)
const revision = ref<number>(0)

const queryButtonDisabled = computed(
  () =>
    primarySearchParameters.value === null ||
    (needsConfirm() && searchByValue.value === 'Gene/Chrom')
)

function needsConfirm() {
  const p = searchParameters.value
  return !(p?.gene || p?.biotypes || p?.chromStart || p?.chromEnd)
}

function updatePrimaryParameters(params: PrimarySearchParameters | null) {
  primarySearchParameters.value = params
  if (params === null) {
    resetSearchParameters()
  } else {
    revision.value += 1
    searchParameters.value = {
      ...params,
      searchBy: searchByValue.value,
      state: 'complete'
    }
  }
  parametersChanged()
}

function resetSearchParameters() {
  searchParameters.value = { ...DUMMY_SEARCH_PARAMETERS, searchBy: searchByValue.value }
}

function parametersChanged() {
  isConfirmed.value = false
}

function confirmSearch() {
  if (needsConfirm()) {
    confirm.require({
      message:
        'You can narrow down your search by selecting a gene or a genomic region (chromosome start and end). Are you sure you want to proceed?',
      header: 'Broad search criteria may result in large, slow-running queries!',
      accept: () => {
        isConfirmed.value = true
        if (isSearchParameter(searchParameters.value)) {
          confirmedSearchParameters.value = searchParameters.value
        }
      },
      reject: () => {
        isConfirmed.value = false
      }
    })
  } else {
    isConfirmed.value = true
  }
}
</script>

<template>
  <DefaultLayout>
    <!-- SECTION -->
    <SectionLayout>
      <StyledHeadline text="Search RNA modifications" />
      <SubTitle>Query by modification, gene or genomic region</SubTitle>
      <!-- TOGGLE - SEARCH SELECTION BY MODIFICATION OR GENE -->
      <Divider />
      <div>
        <SelectButton
          v-model="searchByValue"
          :options="SEARCH_BY_OPTIONS"
          :allowEmpty="false"
          @change="resetSearchParameters"
        />
      </div>
      <Divider />
      <!-- FILTER 1 -->
      <div v-if="searchByValue === 'Modification'">
        <ModificationSelectForm @change="updatePrimaryParameters" />
      </div>
      <div v-else>
        <SpeciesSelectForm @change="updatePrimaryParameters" />
      </div>
      <!-- FILTER 2 -->
      <Divider />
      <SecondarySearchParametersForm v-model="searchParameters" @change="parametersChanged" />
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
    </SectionLayout>
    <SectionLayout>
      <SearchResults :search-parameters="confirmedSearchParameters" :key="revision" />
    </SectionLayout>
  </DefaultLayout>
</template>
