<script setup>
import { ref, computed } from 'vue'
import { useField, useForm } from 'vee-validate'
import { HTTP } from '@/services/API.js'

import CompareStepA from '@/components/compare/CompareStepA.vue'
import CompareStepB from '@/components/compare/CompareStepB.vue'
import CompareStepC from '@/components/compare/CompareStepC.vue'
import StyledHeadline from '@/components/ui/StyledHeadline.vue'
import SubTitle from '@/components/ui/SubTitle.vue'
import { handleRequestWithErrorReporting } from '@/utils/request'
import { useDialogState } from '@/stores/DialogState'

const dialogState = useDialogState()
const uploadMessage = ref()
const active = ref(0)
const loading = ref(false)
const disabled = computed(() => isAandB())
const isEUF = ref(false)
const datasetUpdated = ref()
const datasetUploaded = ref()
const selectedDatasetA = ref([])
const selectedDatasetB = ref([])

const dt = ref()
const records = ref()
const columns = [
  { field: 'a.chrom', header: 'Chrom', exportHeader: 'chrom', sortable: true },
  { field: 'a.start', header: 'Start', exportHeader: 'chromStart', sortable: true },
  { field: 'a.end', header: 'End', exportHeader: 'chromEnd', sortable: false },
  { field: 'a.name', header: 'Name', exportHeader: 'name', sortable: false },
  { field: 'a.score', header: 'Score', exportHeader: 'score', sortable: true },
  { field: 'a.strand', header: 'Strand', exportHeader: 'strand', sortable: false },
  { field: 'a.eufid', header: 'EUFID', exportHeader: 'eufid', sortable: false },
  { field: 'a.coverage', header: 'Coverage', exportHeader: 'coverage', sortable: true },
  { field: 'a.frequency', header: 'Frequency', exportHeader: 'frequency', sortable: true },
  { field: 'b.chrom', header: 'Chrom', exportHeader: 'chromB', sortable: true },
  { field: 'b.start', header: 'Start', exportHeader: 'chromStartB', sortable: true },
  { field: 'b.end', header: 'End', exportHeader: 'chromEndB', sortable: false },
  { field: 'b.name', header: 'Name', exportHeader: 'nameB', sortable: false },
  { field: 'b.score', header: 'Score', exportHeader: 'scoreB', sortable: true },
  { field: 'b.strand', header: 'Strand', exportHeader: 'strandB', sortable: false },
  { field: 'b.eufid', header: 'EUFID', exportHeader: 'eufidB', sortable: false },
  { field: 'b.coverage', header: 'Coverage', exportHeader: 'coverageB', sortable: true },
  { field: 'b.frequency', header: 'Frequency', exportHeader: 'frequencyB', sortable: true },
  { field: 'distance', header: 'Distance', exportHeader: 'distance', sortable: false }
]

const { handleSubmit, resetForm } = useForm()
const { value: queryCriteria, errorMessage } = useField('value', validateField)
const onSubmit = handleSubmit((submitted) => {
  loading.value = true
  if (submitted.value && submitted.value.length > 0) {
    switch (submitted.value) {
      case 'intersect-true':
        intersect(true)
        break
      case 'intersect-false':
        intersect(false)
        break
      case 'closest-true':
        closest(true)
        break
      case 'closest-false':
        closest(false)
        break
      case 'subtract-true':
        subtract(true)
        break
      case 'subtract-false':
        subtract(false)
        break
      default:
        console.log(`Error: Got bad value '${submitted.value}'`)
    }
    resetForm()
  }
})

function intersect(is_strand) {
  handleRequestWithErrorReporting(
    HTTP.get('/dataset/intersect', {
      params: getCompareParams(is_strand),
      paramsSerializer: {
        indexes: null
      }
    }),
    'Failed to do intersect',
    dialogState
  ).then((data) => {
    records.value = data.records.map((x) => {
      return {
        a: x.a,
        b: x.b,
        distance: ''
      }
    })
    loading.value = false
  })
}

function getCompareParams(is_strand) {
  return {
    reference: selectedDatasetA.value,
    comparison: selectedDatasetB.value,
    upload: datasetUploaded.value,
    strand: is_strand,
    euf: isEUF.value
  }
}

function closest(is_strand) {
  handleRequestWithErrorReporting(
    HTTP.get('/dataset/closest', {
      params: getCompareParams(is_strand),
      paramsSerializer: {
        indexes: null
      }
    }),
    'Failed to do closest',
    dialogState
  ).then((data) => {
    records.value = data.records
    loading.value = false
  })
}

function subtract(is_strand) {
  handleRequestWithErrorReporting(
    HTTP.get('/dataset/subtract', {
      params: getCompareParams(is_strand),
      paramsSerializer: {
        indexes: null
      }
    }),
    'Failed to do intersect',
    dialogState
  ).then((data) => {
    records.value = data.records.map((x) => {
      return {
        a: x,
        b: {
          chrom: '',
          start: '',
          end: '',
          name: '',
          score: '',
          strand: '',
          eufid: '',
          coverage: '',
          frequency: ''
        },
        distance: ''
      }
    })
    loading.value = false
  })
}

const onExport = () => {
  dt.value.exportCSV()
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

const buttonPt = {
  root: ({ props, context }) => ({
    class: ['h-12 w-12 p-0 shadow']
  })
}
// https://github.com/primefaces/primevue-tailwind/issues/168
const tablePt = {
  virtualScrollerSpacer: {
    class: 'flex'
  }
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
              <CompareStepA v-model="selectedDatasetA" @dataset-updated="datasetUpdated = $event" />
            </div>
          </TabPanel>
          <TabPanel header="Select dataset for comparison">
            <div class="h-52">
              <div class="mb-4">
                At least one reference dataset must be selected. Upload your own data or select up
                to three dataset for comparison. For upload, pay attention to the organism and/or
                the assembly of your data to avoid spurious comparison results.
              </div>
              <CompareStepB
                v-if="datasetUpdated && selectedDatasetA.length > 0"
                v-model="selectedDatasetB"
                v-model:isEUF="isEUF"
                :selected-datasets="selectedDatasetA"
                :datasets="datasetUpdated"
                @dataset-uploaded="datasetUploaded = $event"
              />
            </div>
          </TabPanel>
          <TabPanel header="Select query criteria">
            <div>
              <form @submit="onSubmit">
                <div class="h-52">
                  <CompareStepC v-model="queryCriteria" />
                  <Button
                    icon="pi pi-sync"
                    size="small"
                    type="submit"
                    label="Submit"
                    :disabled="disabled"
                    :loading="loading"
                    class="mt-4"
                  />
                  <small id="text-error" class="p-4 select-none text-sm text-red-700">
                    <i
                      :class="[
                        errorMessage || uploadMessage
                          ? 'pi pi-times-circle place-self-center text-red-700'
                          : ''
                      ]"
                    />
                    {{ errorMessage || uploadMessage || '&nbsp;' }}
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
          :loading="loading"
          :pt="tablePt"
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
          <template #loading>
            <ProgressSpinner style="width: 60px; height: 60px" strokeWidth="6" />
          </template>
          <ColumnGroup type="header">
            <Row>
              <Column header="Reference dataset A" :colspan="9" />
              <Column header="Comparison dataset B" :colspan="10" />
            </Row>
            <Row>
              <Column
                v-for="col of columns"
                :key="col.field"
                :field="col.field"
                :sortable="col.sortable"
                :header="col.header"
                style="w-{1/19}"
              >
              </Column>
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
