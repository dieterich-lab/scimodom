<script setup>
import { ref, onMounted } from 'vue'
import service from '@/services/index.js'
import CompareStepI from '@/components/compare/CompareStepI.vue'
import CompareStepII from '@/components/compare/CompareStepII.vue'

const selectOptions = ref()
const selectDataset = ref()

const selectedRefDataset = ref()
const selectedCompDataset = ref()

const selectedSpecies = ref()

const dt = ref()
const records = ref()
// const loading = ref(false)
// const totalRecords = ref(0)
// const lazyParams = ref({})

const active = ref(0)

const ingredient = ref('')

// const onPage = (event) => {
//   lazyParams.value = event
//   lazyLoad()
// }
//
// const onSort = (event) => {
//   lazyParams.value = event
//   lazyLoad()
// }

const onExport = () => {
  dt.value.exportCSV()
}
onMounted(() => {
  // lazyParams.value = {
  //   first: dt.value.first,
  //   rows: dt.value.rows
  // }
  // lazyLoad()
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

// function lazyLoad() {
//   loading.value = true
//   service
//     .get('/search', {
//       params: {
//         data: selectedRefDataset.value,
//         firstRecord: lazyParams.value.first,
//         maxRecords: lazyParams.value.rows,
//         multiSort: fmtOrder(lazyParams.value.multiSortMeta)
//       },
//       paramsSerializer: {
//         indexes: null
//       }
//     })
//     .then(function (response) {
//       records.value = response.data.records
//       totalRecords.value = response.data.totalRecords
//     })
//     .catch((error) => {
//       console.log(error)
//     })
//   loading.value = false
// }

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
          class="text-transparent bg-clip-text bg-gradient-to-r from-crmapgreen2 from-10% via-crmapgreen1 via-40% via-crmapblue2 via-60% to-crmapblue4 to-100"
        >
          Compare
        </span>
        dataset
      </h1>
      <p class="text-lg font-normal text-gray-500 lg:text-xl">Perform complex queries</p>
      <Divider :pt="{ root: { class: 'bg-crmapgreen0' } }" />

      <div>
        <div class="flex mb-2 gap-2 justify-content-end">
          <Button
            @click="active = 0"
            rounded
            label="1"
            :outlined="active !== 0"
            :pt="{
              root: ({ props, context }) => ({
                class: [
                  'h-12 w-12 p-0 shadow',
                  {
                    'text-white bg-crmapblue0 border border-crmapblue0 hover:bg-crmapblue2 hover:border-crmapblue2':
                      !props.link &&
                      props.severity === null &&
                      !props.text &&
                      !props.outlined &&
                      !props.plain,
                    'text-crmapblue0 bg-transparent border border-crmapblue0':
                      props.link || props.text || props.outlined || props.plain
                  }
                ]
              })
            }"
          />
          <Button
            @click="active = 1"
            rounded
            label="2"
            :outlined="active !== 1"
            :pt="{
              root: ({ props, context }) => ({
                class: [
                  'h-12 w-12 p-0 shadow',
                  {
                    'text-white bg-crmapblue0 border border-crmapblue0 hover:bg-crmapblue2 hover:border-crmapblue2':
                      !props.link &&
                      props.severity === null &&
                      !props.text &&
                      !props.outlined &&
                      !props.plain,
                    'text-crmapblue0 bg-transparent border border-crmapblue0':
                      props.link || props.text || props.outlined || props.plain
                  }
                ]
              })
            }"
          />
          <Button
            @click="active = 2"
            rounded
            label="3"
            :outlined="active !== 2"
            :pt="{
              root: ({ props, context }) => ({
                class: [
                  'h-12 w-12 p-0 shadow',
                  {
                    'text-white bg-crmapblue0 border border-crmapblue0 hover:bg-crmapblue2 hover:border-crmapblue2':
                      !props.link &&
                      props.severity === null &&
                      !props.text &&
                      !props.outlined &&
                      !props.plain,
                    'text-crmapblue0 bg-transparent border border-crmapblue0':
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
                    'bg-white border-crmapblue0 text-crmapblue0':
                      parent.state.d_activeIndex === context.index
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
                    'bg-white border-crmapblue0 text-crmapblue0':
                      parent.state.d_activeIndex === context.index
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
                    'bg-white border-crmapblue0 text-crmapblue0':
                      parent.state.d_activeIndex === context.index
                  }
                ]
              })
            }"
          >
            <div class="flex flex-col gap-4">
              <div>
                <RadioButton
                  v-model="ingredient"
                  inputId="criteria1"
                  name="step3"
                  value="Intersection"
                />
                <label for="criteria1" class="ml-2">
                  <span class="inline text-lg font-bold">Intersection</span>
                </label>
                <p class="mt-2 ml-8">
                  Search for overlaps between modifications in any of the reference dataset and
                  those from the other dataset.
                </p>
              </div>
              <div>
                <RadioButton
                  v-model="ingredient"
                  inputId="criteria2"
                  name="step3"
                  value="Difference"
                />
                <label for="criteria2" class="ml-2">
                  <span class="inline text-lg font-bold">Difference</span>
                </label>
                <p class="mt-2 ml-8">
                  Difference - Search for modifications in any of the reference dataset that are not
                  found in the other dataset.
                </p>
              </div>
            </div>
          </TabPanel>
        </TabView>
      </div>

      <Divider :pt="{ root: { class: 'bg-crmapgreen0' } }" />
      <div>
        <DataTable
          :value="records"
          paginator
          :first="0"
          :rows="10"
          ref="dt"
          @page="onPage($event)"
          @sort="onSort($event)"
          removableSort
          sortMode="multiple"
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
                      'bg-crmapblue0 border-crmapblue0 hover:bg-crmapblue2 hover:border-crmapblue2 focus:ring-crmapblue2 focus:outline-none'
                  }
                }"
              />
            </div>
          </template>
          <Column field="chrom" header="Chrom" sortable exportHeader="chrom"></Column>
          <Column field="start" header="Start" sortable exportHeader="chromStart"></Column>
          <Column field="end" header="End" exportHeader="chromEnd"></Column>
          <Column field="name" header="Name" exportHeader="name"></Column>
          <Column field="score" header="Score" sortable exportHeader="score"></Column>
          <Column field="strand" header="Strand" exportHeader="strand"></Column>
          <Column field="coverage" header="Coverage" sortable exportHeader="coverage"></Column>
          <Column field="frequency" header="Frequency" sortable exportHeader="frequency"></Column>
        </DataTable>
      </div>
    </SectionLayout>
  </DefaultLayout>
</template>
