<script setup>
import Dialog from 'primevue/dialog'

import SubTitle from '@/components/ui/SubTitle.vue'
import ModificationContext from '@/components/modification/ModificationContext.vue'
import ModificationSiteTable from '@/components/modification/ModificationSiteTable.vue'
import MicroRNASiteTable from '@/components/modification/MicroRNASiteTable.vue'
import RBPSiteTable from '@/components/modification/RBPSiteTable.vue'

const props = defineProps({
  site: {
    type: Object,
    required: true
  }
})
const modelVisible = defineModel('visible')

const header = () => {
  return (
    'Information for modification site ' +
    props.site.chrom +
    ':' +
    props.site.start +
    '-' +
    props.site.end
  )
}
</script>

<template>
  <Dialog
    v-model:visible="modelVisible"
    :header="header()"
    :modal="true"
    :pt="{
      root: { class: 'w-fit' },
      closeButton: { class: 'focus:ring-secondary-400 dark:focus:ring-secondary-300' }
    }"
    :ptOptions="{ mergeProps: true }"
  >
    <SubTitle :small="true"> Genomic context: <ModificationContext :coords="site" /> </SubTitle>
    <SubTitle :small="true" :padding="true"
      >This site is also reported in the following datasets:</SubTitle
    >
    <ModificationSiteTable :coords="site" />
    <SubTitle :small="true" :padding="true"
      >The following miRNA target sites may be affected by this modification:</SubTitle
    >
    <MicroRNASiteTable :coords="site" />
    <SubTitle :small="true" :padding="true"
      >The following RBP binding sites may be affected by this modification:</SubTitle
    >
    <RBPSiteTable :coords="site" />
  </Dialog>
</template>
