<script setup>
import { ref, onMounted } from 'vue'

import service from '@/services/index.js'
import CompareStepI from '@/components/compare/CompareStepI.vue'
import CompareStepII from '@/components/compare/CompareStepII.vue'

import { useToast } from 'primevue/usetoast'
import { useField, useForm } from 'vee-validate'

const { handleSubmit, resetForm } = useForm()
const { value: queryCriteria, errorMessage } = useField('value', (value) => !!value)
const toast = useToast()

const columns = [
  { field: 'chrom', header: 'Chrom', sortable: true },
  { field: 'start', header: 'Start', sortable: true },
  { field: 'end', header: 'End', sortable: false },
  { field: 'name', header: 'Name', sortable: false },
  { field: 'score', header: 'Score', sortable: true },
  { field: 'strand', header: 'Strand', sortable: false },
  { field: 'dataset_id', header: 'EUFID', sortable: false },
  { field: 'coverage', header: 'Coverage', sortable: true },
  { field: 'frequency', header: 'Frequency', sortable: true },
  { field: 'chrom_b', header: 'Chrom', sortable: true },
  { field: 'start_b', header: 'Start', sortable: true },
  { field: 'end_b', header: 'End', sortable: false },
  { field: 'name_b', header: 'Name', sortable: false },
  { field: 'score_b', header: 'Score', sortable: true },
  { field: 'strand_b', header: 'Strand', sortable: false },
  { field: 'dataset_id_b', header: 'EUFID', sortable: false },
  { field: 'coverage_b', header: 'Coverage', sortable: true },
  { field: 'frequency_b', header: 'Frequency', sortable: true },
  { field: 'distance', header: 'Distance', sortable: false }
]

// function validateField(value) {
//   if (!value) {
//     return 'Value is required.'
//   }
//   return true
// }

const selectOptions = ref()
const selectDataset = ref()

const selectedRefDataset = ref()
const selectedCompDataset = ref()

const selectedSpecies = ref()

const dt = ref()
const records = ref()

const operation = ref()

const active = ref(0)

const onSubmit = handleSubmit((submitted) => {
  if (submitted.value && submitted.value.length > 0) {
    toast.add({ severity: 'info', summary: 'Form Submitted', detail: submitted.value, life: 3000 })
    operation.value = submitted.value
    load()
    resetForm()
  }
})
const onExport = () => {
  dt.value.exportCSV()
}
onMounted(() => {
  service
    .getEndpoint('/selection')
    .then(function (response) {
      selectOptions.value = response.data
    })
    .catch((error) => {
      console.log(error)
    })
  service
    .getEndpoint('/compare/dataset')
    .then(function (response) {
      selectDataset.value = response.data
    })
    .catch((error) => {
      console.log(error)
    })
})

const setSpecies = (value) => {
  // console.log('SPECIES', value)
  selectedSpecies.value = value
}

const setDataset = (array) => {
  selectedRefDataset.value = array
  // console.log('REF DATASET', array)
  // lazyLoad()
}

const setDatasetII = (array) => {
  selectedCompDataset.value = array
  // lazyLoad()
  // console.log('COMP DATASET', array)
}

function load() {
  service
    .get('/compare/ops', {
      params: {
        datasetIdsA: selectedRefDataset.value,
        datasetIdsB: selectedCompDataset.value,
        operation: operation.value
      },
      paramsSerializer: {
        indexes: null
      }
    })
    .then(function (response) {
      records.value = response.data
    })
    .catch((error) => {
      console.log(error)
    })
}

// function setOrder(o) {
//   if (!Number.isInteger(o)) {
//     return o
//   }
//   return o === 1 ? 'asc' : 'desc'
// }
//
// function fmtOrder(array) {
//   if (!(array === undefined)) {
//     return array.map((d) =>
//       Object.entries(d)
//         .map(([k, v]) => setOrder(v))
//         .join('.')
//     )
//   }
//   return []
// }
</script>

<template>
  <DefaultLayout>
    <SectionLayout>
      <h1 class="font-ham mb-4 text-3xl font-extrabold text-gray-900 md:text-5xl lg:text-6xl">
        <span
          class="text-transparent bg-clip-text bg-gradient-to-r from-crmgs-50 from-10% via-crmgs-25 via-40% via-crmbs-50 via-60% to-crmbs-100 to-100"
        >
          Compare
        </span>
        dataset
      </h1>
      <p class="text-lg font-normal text-gray-500 lg:text-xl">Perform complex queries</p>
      <Divider :pt="{ root: { class: 'bg-crmg' } }" />

      <div>
        <div class="flex mb-2 gap-2 justify-content-end">
          <Button
            @click="active = 0"
            rounded
            label="A"
            :outlined="active !== 0"
            :pt="{
              root: ({ props, context }) => ({
                class: [
                  'h-12 w-12 p-0 shadow',
                  {
                    'text-white bg-crmb border border-crmb hover:bg-crmb/75 hover:border-crmb/75 focus:shadow-[0_0_0_2px_rgba(255,255,255,1),0_0_0_4px_rgba(2,176,237,1),0_1px_2px_0_rgba(0,0,0,1)]':
                      !props.link &&
                      props.severity === null &&
                      !props.text &&
                      !props.outlined &&
                      !props.plain,
                    'text-crmb bg-transparent border border-crmb':
                      props.link || props.text || props.outlined || props.plain
                  }
                ]
              })
            }"
          />
          <Button
            @click="active = 1"
            rounded
            label="B"
            :outlined="active !== 1"
            :pt="{
              root: ({ props, context }) => ({
                class: [
                  'h-12 w-12 p-0 shadow',
                  {
                    'text-white bg-crmb border border-crmb hover:bg-crmb/75 hover:border-crmb/75 focus:shadow-[0_0_0_2px_rgba(255,255,255,1),0_0_0_4px_rgba(2,176,237,1),0_1px_2px_0_rgba(0,0,0,1)]':
                      !props.link &&
                      props.severity === null &&
                      !props.text &&
                      !props.outlined &&
                      !props.plain,
                    'text-crmb bg-transparent border border-crmb':
                      props.link || props.text || props.outlined || props.plain
                  }
                ]
              })
            }"
          />
          <Button
            @click="active = 2"
            rounded
            label="C"
            :outlined="active !== 2"
            :pt="{
              root: ({ props, context }) => ({
                class: [
                  'h-12 w-12 p-0 shadow',
                  {
                    'text-white bg-crmb border border-crmb hover:bg-crmb/75 hover:border-crmb/75 focus:shadow-[0_0_0_2px_rgba(255,255,255,1),0_0_0_4px_rgba(2,176,237,1),0_1px_2px_0_rgba(0,0,0,1)]':
                      !props.link &&
                      props.severity === null &&
                      !props.text &&
                      !props.outlined &&
                      !props.plain,
                    'text-crmb bg-transparent border border-crmb':
                      props.link || props.text || props.outlined || props.plain
                  }
                ]
              })
            }"
          />
        </div>

        <TabView v-model:activeIndex="active">
          <TabPanel
            header="Select reference dataset"
            :pt="{
              headeraction: ({ parent, context }) => ({
                class: [
                  'focus:shadow-none',
                  {
                    'border-gray-300 bg-white text-gray-700 hover:bg-white hover:border-gray-400 hover:text-gray-600':
                      parent.state.d_activeIndex !== context.index,
                    'bg-white border-crmb text-crmb': parent.state.d_activeIndex === context.index
                  }
                ]
              })
            }"
          >
            <CompareStepI
              v-if="selectOptions && selectDataset"
              :select-options="selectOptions"
              :select-dataset="selectDataset"
              @selected-species="setSpecies"
              @selected-dataset="setDataset"
            />
          </TabPanel>
          <TabPanel
            header="Select dataset for comparison"
            :pt="{
              headeraction: ({ parent, context }) => ({
                class: [
                  'focus:shadow-none',
                  {
                    'border-gray-300 bg-white text-gray-700 hover:bg-white hover:border-gray-400 hover:text-gray-600':
                      parent.state.d_activeIndex !== context.index,
                    'bg-white border-crmb text-crmb': parent.state.d_activeIndex === context.index
                  }
                ]
              })
            }"
          >
            <CompareStepII
              v-if="selectOptions && selectDataset && selectedSpecies && selectedRefDataset"
              :selected-species="selectedSpecies"
              :select-options="selectOptions"
              :select-dataset="selectDataset"
              :reference-dataset="selectedRefDataset"
              @selected-dataset="setDatasetII"
            />
          </TabPanel>
          <TabPanel
            header="Select query criteria"
            :pt="{
              headeraction: ({ parent, context }) => ({
                class: [
                  'focus:shadow-none',
                  {
                    'border-gray-300 bg-white text-gray-700 hover:bg-white hover:border-gray-400 hover:text-gray-600':
                      parent.state.d_activeIndex !== context.index,
                    'bg-white border-crmb text-crmb': parent.state.d_activeIndex === context.index
                  }
                ]
              })
            }"
          >
            <div>
              <form @submit="onSubmit" class="flex flex-col gap-4">
                <div class="flex flex-row">
                  <div class="w-1/2">
                    <RadioButton
                      v-model="queryCriteria"
                      inputId="criteria1"
                      name="step3"
                      value="intersectSTrue"
                    />
                    <label for="criteria1" class="ml-2">
                      <span class="inline font-bold">Intersection</span>
                    </label>
                    <p class="mt-0 ml-8 text-sm">
                      Search for overlaps between A and B on the same strand.
                    </p>
                  </div>
                  <div class="w-1/2">
                    <RadioButton
                      v-model="queryCriteria"
                      inputId="criteria2"
                      name="step3"
                      value="intersectSFalse"
                    />
                    <label for="criteria3" class="ml-2">
                      <span class="inline font-bold">Intersection (strand-unaware)</span>
                    </label>
                    <p class="mt-0 ml-8 text-sm">
                      Search for overlaps between A and B without respect to strand.
                    </p>
                  </div>
                </div>
                <div class="flex flex-row">
                  <div class="w-1/2">
                    <RadioButton
                      v-model="queryCriteria"
                      inputId="criteria3"
                      name="step3"
                      value="closestSTrue"
                    />
                    <label for="criteria3" class="ml-2">
                      <span class="inline font-bold">Closest</span>
                    </label>
                    <p class="mt-0 ml-8 text-sm">
                      Search for closest non-overlaps in B (wrt. A) on the same strand.
                    </p>
                  </div>
                  <div class="w-1/2">
                    <RadioButton
                      v-model="queryCriteria"
                      inputId="criteria4"
                      name="step3"
                      value="closestSFalse"
                    />
                    <label for="criteria3" class="ml-2">
                      <span class="inline font-bold">Closest (strand-unaware)</span>
                    </label>
                    <p class="mt-0 ml-8 text-sm">
                      Search for closest non-overlaps in B (wrt. A) without respect to strand.
                    </p>
                  </div>
                </div>
                <div class="flex flex-row">
                  <div class="w-1/2">
                    <RadioButton
                      v-model="queryCriteria"
                      inputId="criteria5"
                      name="step3"
                      value="subtractSTrue"
                    />
                    <label for="criteria5" class="ml-2">
                      <span class="inline font-bold">Difference</span>
                    </label>
                    <p class="mt-0 ml-8 text-sm">
                      Search for strict non-overlaps in A (modifications in A but not in B) on the
                      same strand.
                    </p>
                  </div>
                  <div class="w-1/2">
                    <RadioButton
                      v-model="queryCriteria"
                      inputId="criteria6"
                      name="step3"
                      value="subtractSFalse"
                    />
                    <label for="criteria6" class="ml-2">
                      <span class="inline font-bold">Difference (strand-unaware)</span>
                    </label>
                    <p class="mt-0 ml-8 text-sm">
                      Search for strict non-overlaps in A (modifications in A but not in B) without
                      respect to strand.
                    </p>
                  </div>
                </div>
                <div>
                  <Button
                    icon="pi pi-sync"
                    size="small"
                    type="submit"
                    label="Submit"
                    :pt="{
                      root: {
                        class:
                          'bg-crmg border-crmg hover:bg-crmg/75 hover:border-crmg/75 focus:ring-crmg/75 focus:outline-none focus:shadow-[0_0_0_2px_rgba(255,255,255,1),0_0_0_4px_rgba(0,176,81,1),0_1px_2px_0_rgba(0,0,0,1)]'
                      }
                    }"
                  />
                  <small id="text-error" class="p-4">{{ errorMessage || '&nbsp;' }}</small>
                </div>
              </form>
            </div>
          </TabPanel>
        </TabView>
      </div>

      <Divider :pt="{ root: { class: 'bg-crmg' } }" />
      <div>
        <DataTable
          :value="records"
          ref="dt"
          sortMode="multiple"
          removableSort
          scrollable
          scrollHeight="400px"
          :virtualScrollerOptions="{ itemSize: 46 }"
          tableStyle="min-w-{50rem}"
          stripedRows
        >
          <template #header>
            <div style="text-align: right">
              <Button
                icon="pi pi-external-link"
                size="small"
                label="Export"
                @click="onExport($event)"
                :pt="{
                  root: {
                    class:
                      'bg-crmb border-crmb hover:bg-crmb/75 hover:border-crmb/75 focus:ring-crmb/75 focus:outline-none focus:shadow-[0_0_0_2px_rgba(255,255,255,1),0_0_0_4px_rgba(2,176,237,1),0_1px_2px_0_rgba(0,0,0,1)]'
                  }
                }"
              />
            </div>
          </template>
          <ColumnGroup type="header">
            <Row>
              <Column header="Reference dataset A" :colspan="9" />
              <Column header="Comparison dataset B" :colspan="10" />
            </Row>
            <Row>
              <!-- pre-loaded, sort automatic, explicit columns required -->
              <Column field="chrom" header="Chrom" sortable exportHeader="chrom"></Column>
              <Column field="start" header="Start" sortable exportHeader="chromStart"></Column>
              <Column field="end" header="End" exportHeader="chromEnd"></Column>
              <Column field="name" header="Name" exportHeader="name"></Column>
              <Column field="score" header="Score" sortable exportHeader="score"></Column>
              <Column field="strand" header="Strand" exportHeader="strand"></Column>
              <Column field="dataset_id" header="EUFID" exportHeader="EUFID"></Column>
              <Column field="coverage" header="Coverage" sortable exportHeader="coverage"></Column>
              <Column
                field="frequency"
                header="Frequency"
                sortable
                exportHeader="frequency"
              ></Column>
              <Column field="chrom_b" header="Chrom" sortable exportHeader="chrom"></Column>
              <Column field="start_b" header="Start" sortable exportHeader="chromStart"></Column>
              <Column field="end_b" header="End" exportHeader="chromEnd"></Column>
              <Column field="name_b" header="Name" exportHeader="name"></Column>
              <Column field="score_b" header="Score" sortable exportHeader="score"></Column>
              <Column field="strand_b" header="Strand" exportHeader="strand"></Column>
              <Column field="dataset_id_b" header="EUFID" exportHeader="EUFID"></Column>
              <Column
                field="coverage_b"
                header="Coverage"
                sortable
                exportHeader="coverage"
              ></Column>
              <Column
                field="frequency_b"
                header="Frequency"
                sortable
                exportHeader="frequency"
              ></Column>
              <Column field="distance" header="Distance" exportHeader="distance"></Column>
            </Row>
          </ColumnGroup>
          <Column v-for="col of columns" :key="col.field" :field="col.field"></Column>
        </DataTable>
      </div>
    </SectionLayout>
  </DefaultLayout>
</template>
