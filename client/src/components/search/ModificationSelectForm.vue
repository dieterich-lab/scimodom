<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  type ModificationType,
  type Organism,
  modificationTypeCache,
  getTechnologyByModificationIdAndOrganimId,
  getSelectionsByIds,
  getOrganimsByModificationId,
  getTechnologiesByIds
} from '@/services/selection'
import {
  getOptionsForPrimvueCascadeSelect,
  type CascadeItem,
  getOptionsForPrimvueTreeSelect,
  type TreeNode
} from '@/utils/primevue'
import type { PrimarySearchParameters } from '@/utils/search'

const emit = defineEmits<{
  (e: 'change', params: PrimarySearchParameters | null): void
}>()

const modificationTypeOptions = ref<CascadeItem<ModificationType>[]>([])
const organismOptions = ref<CascadeItem<Organism>[]>([])
const technologyOptions = ref<TreeNode[]>([])

const selectedModification = ref<ModificationType>()
const selectedOrganism = ref<Organism>()
const selectedTechnologyIdsAsStrings = ref<string[]>([])
const results = ref<PrimarySearchParameters | null>(null)

function clearTechnologySelection() {
  selectedTechnologyIdsAsStrings.value = []
  if (results.value !== null) {
    results.value = null
    emit('change', results.value)
  }
}

function clearAll() {
  technologyOptions.value = []
  selectedOrganism.value = undefined
  clearTechnologySelection()
}

const resetDefaults = () => {
  selectedModification.value = undefined
  selectedOrganism.value = undefined
  selectedTechnologyIdsAsStrings.value = []
}

onMounted(async () => {
  const modificationTypes = [...(await modificationTypeCache.getData())]
  modificationTypeOptions.value = getOptionsForPrimvueCascadeSelect(modificationTypes, [
    'rna_name',
    'modomics_sname'
  ])
  resetDefaults()
})

async function updateOrganism(modification: ModificationType) {
  clearAll()
  const rawOrganisms = await getOrganimsByModificationId(modification.modification_id)
  const cookedOrganisms = rawOrganisms.map((x) => {
    return { ...x, kingdom: x.kingdom ? x.kingdom : x.domain }
  })
  organismOptions.value = getOptionsForPrimvueCascadeSelect(cookedOrganisms, [
    'kingdom',
    'taxa_sname',
    'cto'
  ])
}
async function updateTechnology(organism: Organism) {
  clearTechnologySelection()
  const modificationId = selectedModification.value?.modification_id

  if (modificationId !== undefined) {
    technologyOptions.value = getOptionsForPrimvueTreeSelect(
      await getTechnologyByModificationIdAndOrganimId(modificationId, organism.organism_id),
      ['meth', 'tech'],
      'technology_id'
    )
  } else {
    technologyOptions.value = []
  }
}
async function reportResults(techIds: string[]) {
  selectedTechnologyIdsAsStrings.value = techIds
  if (selectedModification.value && selectedOrganism.value) {
    const selections = await getSelectionsByIds(
      selectedModification.value.modification_id,
      selectedOrganism.value.organism_id,
      techIds.map((x) => +x)
    )
    const technologies = await getTechnologiesByIds(techIds.map((x) => +x))
    results.value = {
      selections,
      organism: selectedOrganism.value,
      modificationType: selectedModification.value,
      technologies
    }
    emit('change', results.value)
  }
}
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-10 gap-6">
    <div class="col-span-3">
      <Dropdown
        @change="updateOrganism($event.value)"
        v-model="selectedModification"
        :options="modificationTypeOptions"
        optionLabel="label"
        optionGroupLabel="label"
        optionGroupChildren="cChildren"
        placeholder="1. Select RNA modification"
        :pt="{
          root: { class: 'w-full md:w-full' }
        }"
        :ptOptions="{ mergeProps: true }"
      />
    </div>
    <div class="col-span-3">
      <CascadeSelect
        @change="updateTechnology($event.value)"
        v-model="selectedOrganism"
        :options="organismOptions"
        optionLabel="label"
        optionGroupLabel="label"
        :optionGroupChildren="['cChildren', 'cChildren']"
        placeholder="2. Select organism"
        :pt="{
          root: { class: 'w-full md:w-full' }
        }"
        :ptOptions="{ mergeProps: true }"
      />
    </div>
    <div class="col-span-3">
      <TreeSelect
        @change="reportResults($event)"
        v-model="selectedTechnologyIdsAsStrings"
        :options="technologyOptions"
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
</template>
