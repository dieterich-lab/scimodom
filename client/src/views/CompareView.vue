<script setup>
import { ref, computed, onMounted } from 'vue'
import { useField, useForm } from 'vee-validate'
import service from '@/services/index.js'
import CompareStepA from '@/components/compare/CompareStepA.vue'
import CompareStepB from '@/components/compare/CompareStepB.vue'

const active = ref(0)
const disabled = computed(() => isAandB())

const options = ref()
const dataset = ref()
const selectedDSA = ref()
const selectedDSB = ref()
const selectedDSU = ref()
const selectedSpecies = ref()

const dt = ref()
const records = ref()
const columns = [
  { field: 'chrom', header: 'Chrom', exportHeader: 'chrom', sortable: true },
  { field: 'start', header: 'Start', exportHeader: 'chromStart', sortable: true },
  { field: 'end', header: 'End', exportHeader: 'chromEnd', sortable: false },
  { field: 'name', header: 'Name', exportHeader: 'name', sortable: false },
  { field: 'score', header: 'Score', exportHeader: 'score', sortable: true },
  { field: 'strand', header: 'Strand', exportHeader: 'strand', sortable: false },
  { field: 'dataset_id', header: 'EUFID', exportHeader: 'eufid', sortable: false },
  { field: 'coverage', header: 'Coverage', exportHeader: 'coverage', sortable: true },
  { field: 'frequency', header: 'Frequency', exportHeader: 'frequency', sortable: true },
  { field: 'chrom_b', header: 'Chrom', exportHeader: 'chromB', sortable: true },
  { field: 'start_b', header: 'Start', exportHeader: 'chromStartB', sortable: true },
  { field: 'end_b', header: 'End', exportHeader: 'chromEndB', sortable: false },
  { field: 'name_b', header: 'Name', exportHeader: 'nameB', sortable: false },
  { field: 'score_b', header: 'Score', exportHeader: 'scoreB', sortable: true },
  { field: 'strand_b', header: 'Strand', exportHeader: 'strandB', sortable: false },
  { field: 'dataset_id_b', header: 'EUFID', exportHeader: 'eufidB', sortable: false },
  { field: 'coverage_b', header: 'Coverage', exportHeader: 'coverageB', sortable: true },
  { field: 'frequency_b', header: 'Frequency', exportHeader: 'frequencyB', sortable: true },
  { field: 'distance', header: 'Distance', exportHeader: 'distance', sortable: false }
]

const { handleSubmit, resetForm } = useForm()
const { value: queryCriteria, errorMessage } = useField('value', validateField)
const onSubmit = handleSubmit((submitted) => {
  if (submitted.value && submitted.value.length > 0) {
    load(submitted.value)
    resetForm()
  }
})

const onExport = () => {
  dt.value.exportCSV()
}

function load(operation) {
  records.value = undefined
  service
    .get('/compare/ops', {
      params: {
        datasetIdsA: selectedDSA.value,
        datasetIdsB: selectedDSB.value,
        datasetUpload: selectedDSU.value,
        queryOperation: operation
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

function validateField(value) {
  if (!value) {
    return 'Query criteria undefined!'
  }
  return true
}

function isAandB() {
  var isA = Object.is(selectedDSA.value, undefined) || selectedDSA.value.length === 0 ? true : false
  var isB = Object.is(selectedDSB.value, undefined) || selectedDSB.value.length === 0 ? true : false
  var isU = Object.is(selectedDSU.value, undefined) || selectedDSU.value.length === 0 ? true : false
  return isA || (isB && isU)
}

onMounted(() => {
  service
    .getEndpoint('/selection')
    .then(function (response) {
      options.value = response.data
    })
    .catch((error) => {
      console.log(error)
    })
  service
    .getEndpoint('/compare/dataset')
    .then(function (response) {
      dataset.value = response.data
    })
    .catch((error) => {
      console.log(error)
    })
})
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
            severity="secondary"
            :outlined="active !== 0"
            :pt="{
              root: ({ props, context }) => ({
                class: ['h-12 w-12 p-0 shadow']
              })
            }"
            :ptOptions="{ mergeProps: true }"
          />
          <Button
            @click="active = 1"
            rounded
            label="B"
            severity="secondary"
            :outlined="active !== 1"
            :pt="{
              root: ({ props, context }) => ({
                class: ['h-12 w-12 p-0 shadow']
              })
            }"
            :ptOptions="{ mergeProps: true }"
          />
          <Button
            @click="active = 2"
            rounded
            label="C"
            severity="secondary"
            :outlined="active !== 2"
            :pt="{
              root: ({ props, context }) => ({
                class: ['h-12 w-12 p-0 shadow']
              })
            }"
            :ptOptions="{ mergeProps: true }"
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
            <CompareStepA
              v-if="options && dataset"
              :options="options"
              :dataset="dataset"
              @selected-species="selectedSpecies = $event"
              @selected-dataset="selectedDSA = $event"
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
            <CompareStepB
              v-if="options && dataset && selectedSpecies && selectedDSA"
              :options="options"
              :dataset="dataset"
              :reference-dataset="selectedDSA"
              :selected-species="selectedSpecies"
              @selected-dataset="selectedDSB = $event"
              @uploaded-dataset="selectedDSU = $event"
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
                    :disabled="disabled"
                  />
                  <small
                    id="text-error"
                    class="p-4 select-none font-semibold text-base text-crmg"
                    >{{ errorMessage || '&nbsp;' }}</small
                  >
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
                severity="secondary"
                raised
                @click="onExport($event)"
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
              <Column field="chrom" header="Chrom" sortable style="w-{1/19}"></Column>
              <Column field="start" header="Start" sortable style="w-{1/19}"></Column>
              <Column field="end" header="End" style="w-{1/19}"></Column>
              <Column field="name" header="Name" style="w-{1/19}"></Column>
              <Column field="score" header="Score" sortable style="w-{1/19}"></Column>
              <Column field="strand" header="Strand" style="w-{1/19}"></Column>
              <Column field="dataset_id" header="EUFID" style="w-{1/19}"></Column>
              <Column field="coverage" header="Coverage" style="w-{1/19}" sortable></Column>
              <Column field="frequency" header="Frequency" sortable style="w-{1/19}"></Column>
              <Column field="chrom_b" header="Chrom" sortable style="w-{1/19}"></Column>
              <Column field="start_b" header="Start" sortable style="w-{1/19}"></Column>
              <Column field="end_b" header="End" style="w-{1/19}"></Column>
              <Column field="name_b" header="Name" style="w-{1/19}"></Column>
              <Column field="score_b" header="Score" sortable style="w-{1/19}"></Column>
              <Column field="strand_b" header="Strand" style="w-{1/19}"></Column>
              <Column field="dataset_id_b" header="EUFID" style="w-{1/19}"></Column>
              <Column field="coverage_b" header="Coverage" sortable style="w-{1/19}"></Column>
              <Column field="frequency_b" header="Frequency" sortable style="w-{1/19}"></Column>
              <Column field="distance" header="Distance" style="w-{1/19}"></Column>
            </Row>
          </ColumnGroup>
          <Column
            v-for="col of columns"
            :key="col.field"
            :field="col.field"
            :exportHeader="col.exportHeader"
            style="w-{1/19}"
          >
          </Column>
        </DataTable>
      </div>
    </SectionLayout>
  </DefaultLayout>
</template>
