<script setup>
import { ref, computed, onMounted } from 'vue'
import { useField, useForm } from 'vee-validate'
import { HTTP } from '@/services/API.js'
import { toTree, toCascade, nestedSort } from '@/utils/index.js'

import CompareStepA from '@/components/compare/CompareStepA.vue'
import CompareStepB from '@/components/compare/CompareStepB.vue'
import StyledHeadline from '@/components/ui/StyledHeadline.vue'
import SubTitle from '@/components/ui/SubTitle.vue'

const active = ref(0)
const disabled = computed(() => isAandB())
const taxid = ref()
const dataset = ref()
const datasetUpdated = ref()
const datasetUploaded = ref()
const selectedDatasetA = ref([])
const selectedDatasetB = ref([])

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
  HTTP.get('/compare/ops', {
    params: {
      datasetIdsA: selectedDatasetA.value,
      datasetIdsB: selectedDatasetB.value,
      datasetUpload: datasetUploaded.value,
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
  var isA = selectedDatasetA.value.length === 0 ? true : false
  var isB = selectedDatasetB.value.length === 0 ? true : false
  var isU = Object.is(datasetUploaded.value, undefined) ? true : false
  return isA || (isB && isU)
}

onMounted(() => {
  HTTP.get('/browse')
    .then(function (response) {
      dataset.value = response.data
    })
    .catch((error) => {
      console.log(error)
    })
  HTTP.get('/selection')
    .then(function (response) {
      let opts = response.data
      opts = opts.map((item) => {
        const kingdom = Object.is(item.kingdom, null) ? item.domain : item.kingdom
        return { ...item, kingdom }
      })
      taxid.value = toCascade(toTree(opts, ['kingdom', 'taxa_sname'], 'taxa_id'))
      nestedSort(taxid.value, ['child1'])
    })
    .catch((error) => {
      console.log(error)
    })
})

const buttonPt = {
  root: ({ props, context }) => ({
    class: ['h-12 w-12 p-0 shadow']
  })
}
</script>

<template>
  <DefaultLayout>
    <SectionLayout>
      <StyledHeadline text="Compare dataset" />
      <SubTitle>Perform complex queries</SubTitle>

      <Divider />

      <div>
        <div class="flex mb-2 gap-2 justify-content-end">
          <Button
            @click="active = 0"
            rounded
            label="A"
            severity="secondary"
            :outlined="active !== 0"
            :pt="buttonPt"
            :ptOptions="{ mergeProps: true }"
          />
          <Button
            @click="active = 1"
            rounded
            label="B"
            severity="secondary"
            :outlined="active !== 1"
            :pt="buttonPt"
            :ptOptions="{ mergeProps: true }"
          />
          <Button
            @click="active = 2"
            rounded
            label="C"
            severity="secondary"
            :outlined="active !== 2"
            :pt="buttonPt"
            :ptOptions="{ mergeProps: true }"
          />
        </div>

        <TabView v-model:activeIndex="active">
          <TabPanel header="Select reference dataset">
            <div class="h-52">
              <div class="mb-4">
                Select one organism and choose up to three reference dataset. Use the dataset search
                bar to find records.
              </div>
              <CompareStepA
                v-if="taxid && dataset"
                v-model="selectedDatasetA"
                :organism="taxid"
                :dataset="dataset"
                @dataset-updated="datasetUpdated = $event"
              />
            </div>
          </TabPanel>
          <TabPanel header="Select dataset for comparison">
            <div class="h-52">
              <div class="mb-4">
                At least one reference dataset must be selected. Upload your own data or select up
                to three dataset for comparison.
              </div>
              <CompareStepB
                v-if="datasetUpdated && selectedDatasetA.length > 0"
                v-model="selectedDatasetB"
                :selected="selectedDatasetA"
                :dataset="datasetUpdated"
                @dataset-uploaded="datasetUploaded = $event"
              />
            </div>
          </TabPanel>
          <TabPanel header="Select query criteria">
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
                  <small id="text-error" class="p-4 select-none text-sm text-red-700">
                    <i
                      :class="[
                        errorMessage ? 'pi pi-times-circle place-self-center text-red-700' : ''
                      ]"
                    />
                    {{ errorMessage || '&nbsp;' }}
                  </small>
                </div>
              </form>
            </div>
          </TabPanel>
        </TabView>
      </div>
      <Divider />
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
