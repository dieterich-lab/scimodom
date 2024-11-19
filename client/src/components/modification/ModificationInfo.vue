<script setup lang="ts">
import Dialog from 'primevue/dialog'

import SubTitle from '@/components/ui/SubTitle.vue'
import ModificationContext from '@/components/modification/ModificationContext.vue'
import ModificationSiteTable from '@/components/modification/ModificationSiteTable.vue'
import MicroRNASiteTable from '@/components/modification/MicroRNASiteTable.vue'
import RBPSiteTable from '@/components/modification/RBPSiteTable.vue'
import type { Modification } from '@/services/modification'

const props = defineProps<{ modification?: Modification }>()

const visible = defineModel<boolean>('visible')
function header() {
  if (props.modification) {
    const m = props.modification
    return `Information for modification site ${m.chrom}:${m.start}-${m.end}`
  } else {
    return ''
  }
}
</script>

<template>
  <Dialog
    v-model:visible="visible"
    :header="header()"
    :modal="true"
    :pt="{
      root: { class: 'w-fit' },
      closeButton: { class: 'focus:ring-secondary-400 dark:focus:ring-secondary-300' }
    }"
    :ptOptions="{ mergeProps: true }"
  >
    <SubTitle :small="true">
      Genomic context: <ModificationContext :modification="modification" />
    </SubTitle>

    <SubTitle :small="true" :padding="true"
      >This site is also reported in the following datasets:</SubTitle
    >

    <ModificationSiteTable :modification="modification" />

    <SubTitle :small="true" :padding="true">
      The following miRNA target sites may be affected by this modification:
    </SubTitle>

    <MicroRNASiteTable :modification="modification" />

    <SubTitle :small="true" :padding="true">
      The following RBP binding sites may be affected by this modification:
    </SubTitle>

    <RBPSiteTable :modification="modification" />
  </Dialog>
</template>
