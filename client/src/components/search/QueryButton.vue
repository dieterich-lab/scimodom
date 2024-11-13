<script setup lang="ts">
import { computed } from 'vue'
import Button from 'primevue/button'
import { useConfirm } from 'primevue/useconfirm'
import ConfirmDialog from 'primevue/confirmdialog'
import {
  type DummySearchParameters,
  type SearchParameters,
  isSearchParameter
} from '@/utils/search'

const model = defineModel<SearchParameters | DummySearchParameters>()

const confirm = useConfirm()

const emit = defineEmits<{
  (e: 'submit')
}>()

const disabled = computed(
  () => !isSearchParameter(model.value) || (needsConfirm() && model.value.searchBy === 'Gene/Chrom')
)

function needsConfirm(): boolean {
  const p = model.value
  return !p?.gene && (!p?.chromStart || !p?.chromEnd)
}

function confirmSearch() {
  if (needsConfirm()) {
    confirm.require({
      message:
        'You can narrow down your search by selecting a gene or a genomic region (chromosome start and end). Are you sure you want to proceed?',
      header: 'Broad search criteria may result in large, slow-running queries!',
      accept: () => {
        emit('submit')
      }
    })
  } else {
    emit('submit')
  }
}
</script>
<template>
  <ConfirmDialog />
  <Button
    type="button"
    size="small"
    icon="pi pi-sync"
    label="Query"
    :disabled="disabled"
    @click="confirmSearch()"
  />
</template>
