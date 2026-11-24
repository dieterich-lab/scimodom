<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import SunburstChart from '@/components/ui/SunburstChart.vue'
import { trashRequestErrors } from '@/services/API.js'
import SectionLayout from '@/components/layout/SectionLayout.vue'
import { useDialogState } from '@/stores/DialogState'
import { getDatasetCount } from '@/services/dataset'
import { getSitesCount } from '@/services/modification'
import { type Annotation, annotationCache } from '@/services/annotation'
import { taxaSelectionCache } from '@/services/selection'
import { formatAssemblies, formatReleases } from '@/utils/annotation'

const dialogState = useDialogState()
const sites = ref()
const datasets = ref()
// the counts change with every upload, the reference data does not:
// the former are fetched, the latter comes from the cache
const annotations = ref<readonly Annotation[]>([])
const taxaIdsWithData = ref<ReadonlySet<number>>(new Set())

// const assemblies = computed(() => formatAssemblies(annotations.value))
// const releases = computed(() => formatReleases(annotations.value))
// the sentence is scoped by the counts above it, so it must name
// the organisms that contribute to them, not every organism
// installed: a selection exists only once a dataset was uploaded,
// cf. DatasetService
const contributing = computed(() =>
  annotations.value.filter((x) => taxaIdsWithData.value.has(x.taxa_id))
)
const assemblies = computed(() => formatAssemblies(contributing.value))
const releases = computed(() => formatReleases(contributing.value))

onMounted(() => {
  Promise.all([getSitesCount(dialogState), getDatasetCount(dialogState)])
    .then(([modificationCount, datasetCount]) => {
      sites.value = modificationCount.count
      datasets.value = datasetCount.count
    })
    .catch((e) => trashRequestErrors(e))
  // the sentence reads without it, so a failure here must not take
  // the counts with it
  Promise.all([annotationCache.getData(), taxaSelectionCache.getData()])
    .then(([installed, withData]) => {
      annotations.value = installed
      taxaIdsWithData.value = new Set(withData.map((x) => x.taxa_id))
    })
    .catch((e) => trashRequestErrors(e))
})
</script>

<template>
  <SectionLayout :secondary="false">
    <div>
      <div class="px-4 py-8 md:px-6 lg:px-8 text-center">
        <h1 class="font-ham text-4xl font-semibold m-auto p-4 dark:text-white/80">
          <span>Release</span>
        </h1>
        <p class="leading-loose text-xl font-medium text-gray-600 pt-4 pb-2 dark:text-surface-400">
          Sci-ModoM contains {{ sites }} reported sites with stoichiometric information across
          {{ datasets }} datasets<template v-if="assemblies"
            >, for genome assemblies <br />
            {{ assemblies }}</template
          ><template v-if="releases">, annotated using {{ releases }}</template
          >.
        </p>
        <div class="flex flex-row pt-12">
          <div class="basis-1/2">
            <SunburstChart type="search" />
          </div>
          <div class="basis-1/2">
            <SunburstChart type="browse" />
          </div>
        </div>
      </div>
    </div>
  </SectionLayout>
</template>
