<script setup lang="ts">
import { ref } from 'vue'
import { type Taxa, getSelectionsByTaxaId } from '@/services/selection'
import type { PrimarySearchParameters } from '@/utils/search'
import TaxaSelection from '@/components/ui/TaxaSelection.vue'

const emit = defineEmits<{
  (e: 'change', params: PrimarySearchParameters): void
}>()

const selectedOrganism = ref<Taxa>()

async function selectTaxa(taxa?: Taxa) {
  if (taxa) {
    emit('change', {
      selections: await getSelectionsByTaxaId(taxa.taxa_id),
      taxa,
      rna_type: 'WTS'
    })
  }
}
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-10 gap-6">
    <div class="col-span-3">
      <TaxaSelection
        v-model="selectedOrganism"
        placeholder="1. Select organism"
        @change="selectTaxa"
      />
    </div>
    <div class="col-span-3" />
    <div class="col-span-3" />
    <div />
  </div>
</template>
