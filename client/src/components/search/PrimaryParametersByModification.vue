<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import {
  type ModificationType,
  type Cto,
  type Technology,
  getSelectionsByIds
} from '@/services/selection'
import type { PrimarySearchParameters } from '@/utils/search'
import ModificationTypeSelection from '@/components/ui/ModificationTypeSelection.vue'
import CtoSelection from '@/components/ui/CtoSelection.vue'
import MultiTechnologySelection from '@/components/ui/MultiTechnologySelection.vue'

const emit = defineEmits<{
  (e: 'change', params: PrimarySearchParameters | null): void
}>()

const modificationIds = ref<number[]>([])

const selectedModificationType = ref<ModificationType>()
const selectedCto = ref<Cto>()
const selectedTechnologies = ref<Technology[]>([])
const results = ref<PrimarySearchParameters | null>(null)

const disableCtoSelection = computed(() => selectedModificationType.value === undefined)
const disableTechnologySelection = computed(() => selectedCto.value === undefined)

function clearTechnologySelection() {
  selectedTechnologies.value = []
  if (results.value !== null) {
    results.value = null
    emit('change', results.value)
  }
}

function clearAll() {
  selectedCto.value = undefined
  clearTechnologySelection()
}

const resetDefaults = () => {
  selectedModificationType.value = undefined
  selectedCto.value = undefined
}

onMounted(async () => {
  resetDefaults()
})

async function selectModificationType(modificationType: ModificationType) {
  modificationIds.value = [modificationType.modification_id]
  clearAll()
}
async function selectCto() {
  clearTechnologySelection()
}
async function reportResults(technologies: Technology[]) {
  if (selectedModificationType.value && selectedCto.value && technologies.length > 0) {
    const selections = await getSelectionsByIds(
      selectedModificationType.value.modification_id,
      selectedCto.value.organism_id,
      technologies.map((x) => x.technology_id)
    )
    results.value = {
      selections,
      taxa: { ...selectedCto.value },
      cto: selectedCto.value,
      modificationType: selectedModificationType.value,
      technologies,
      rna_type: 'WTS'
    }
  } else {
    results.value = null
  }
  emit('change', results.value)
}
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-10 gap-6">
    <div class="col-span-3">
      <ModificationTypeSelection
        v-model="selectedModificationType"
        placeholder="1. Select RNA modification"
        @change="selectModificationType"
      />
    </div>
    <div class="col-span-3">
      <CtoSelection
        v-model="selectedCto"
        placeholder="2. Select organism"
        :modification-ids="modificationIds"
        :disabled="disableCtoSelection"
        @change="selectCto"
      />
    </div>
    <div class="col-span-3">
      <MultiTechnologySelection
        v-model="selectedTechnologies"
        :modification-ids="modificationIds"
        :organism-id="selectedCto?.organism_id"
        placeholder="3. Select technology"
        :disabled="disableTechnologySelection"
        @change="reportResults"
      />
    </div>
    <div></div>
  </div>
</template>
