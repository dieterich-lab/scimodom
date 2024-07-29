<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { HTTP } from '@/services/API.js'

const props = defineProps({
  coords: {
    type: Object,
    required: true
  }
})

const router = useRouter()

const dt = ref()
const records = ref()

watch(
  () => props.coords,
  () => {
    load()
  },
  { immediate: true }
)

// table-related utilities
const getFileName = () => {
  let stamp = new Date()
  return 'scimodom_mirna_targets_' + stamp.toISOString().replaceAll(/:/g, '')
}

const onExport = () => {
  dt.value.exportCSV()
}

const navigateTo = (eufid) => {
  router.push({ name: 'browse', params: { eufid: eufid } })
}

function load(event) {
  HTTP.get('/modification/target/MIRNA', {
    params: {
      taxaId: props.coords.taxa_id,
      chrom: props.coords.chrom,
      start: props.coords.start,
      end: props.coords.end,
      strand: props.coords.strand
    },
    paramsSerializer: {
      indexes: null
    }
  })
    .then(function (response) {
      records.value = response.data.records.map(function (obj) {
        let name = obj.name.split(':')
        return {
          chrom: obj.chrom,
          start: obj.start,
          end: obj.end,
          strand: obj.strand,
          score: obj.score,
          source: name[0],
          target: name[1],
          mirna: name[2]
        }
      })
    })
    .catch((error) => {
      console.log(error)
    })
}
</script>

<template>
  <DataTable :value="records" dataKey="id" ref="dt" :exportFilename="getFileName()" stripedRows>
    <template #header>
      <div style="text-align: right">
        <Button
          icon="pi pi-external-link"
          size="small"
          label="Export"
          severity="secondary"
          raised
          @click="onExport($event)"
        />
      </div>
    </template>
    <template #empty>
      <p class="text-center text-secondary-500 font-semibold">
        No known miRNA target site affected by this modification!
      </p>
    </template>
    <Column field="mirna" header="miRNA"></Column>
    <Column field="target" header="Target"></Column>
    <Column field="source" header="Source"></Column>
    <Column field="start" header="Start"></Column>
    <Column field="end" header="End"></Column>
    <Column field="score" header="Score"></Column>
    <Column field="strand" header="strand"></Column>
  </DataTable>
</template>
