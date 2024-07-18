<script setup>
import Dialog from 'primevue/dialog'

import SubTitle from '@/components/ui/SubTitle.vue'
import ModificationSiteTable from '@/components/modification/ModificationSiteTable.vue'

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
    <SubTitle :small="true">This site is also reported in the following datasets:</SubTitle>
    <ModificationSiteTable :coords="site" />
  </Dialog>
</template>
