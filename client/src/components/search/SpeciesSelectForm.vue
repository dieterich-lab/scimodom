<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { organismCache, type Organism, getSelectionsByOrganismId } from '@/services/selection'
import { type CascadeItem, getOptionsForPrimvueCascadeSelect } from '@/utils/primevue'
import type { PrimarySearchParameters } from '@/utils/search'

const emit = defineEmits<{
  (e: 'change', params: PrimarySearchParameters): void
}>()

const organismOptions = ref<CascadeItem<Organism>[]>([])

const selectedOrganism = ref<Organism>()

onMounted(async () => {
  const rawOrganisms = await organismCache.getData()
  const cookedOrganisms = rawOrganisms.map((x) => {
    return { ...x, kingdom: x.kingdom ? x.kingdom : x.domain }
  })
  organismOptions.value = getOptionsForPrimvueCascadeSelect(cookedOrganisms, [
    'kingdom',
    'taxa_sname',
    'cto'
  ])
})

async function changeOrganism(organism?: Organism) {
  if (organism) {
    emit('change', {
      selections: await getSelectionsByOrganismId(organism.organism_id),
      organism: organism
    })
  }
}
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-10 gap-6">
    <div class="col-span-3">
      <CascadeSelect
        @change="changeOrganism($event.value)"
        v-model="selectedOrganism"
        :options="organismOptions"
        optionLabel="label"
        optionGroupLabel="label"
        :optionGroupChildren="['cChildren']"
        placeholder="1. Select organism"
        :pt="{
          root: { class: 'w-full md:w-full' }
        }"
        :ptOptions="{ mergeProps: true }"
      />
    </div>
    <div class="col-span-3" />
    <div class="col-span-3" />
    <div />
  </div>
</template>
