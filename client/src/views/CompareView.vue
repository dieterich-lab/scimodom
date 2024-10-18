<script setup lang="ts">
import { ref, computed } from 'vue'
import { useForm } from 'vee-validate'

import DefaultLayout from '@/components/layout/DefaultLayout.vue'
import SectionLayout from '@/components/layout/SectionLayout.vue'
import CompareStepA from '@/components/compare/CompareStepA.vue'
import CompareStepB from '@/components/compare/CompareStepB.vue'
import CompareStepC from '@/components/compare/CompareStepC.vue'
import CompareResults from '@/components/compare/CompareResults.vue'
import StyledHeadline from '@/components/ui/StyledHeadline.vue'
import SubTitle from '@/components/ui/SubTitle.vue'
import { useDialogState } from '@/stores/DialogState'
import { subtract, intersect, closest, type ComparisonParams } from '@/services/comparison'
import type { Dataset } from '@/services/dataset'
import type { UploadedFile } from '@/services/dataset_upload'
import { ComparisonOperation, getComparisonDisplayRecord } from '@/utils/comparison'

const dialogState = useDialogState()
const uploadMessage = ref<string>()
const active = ref(0)
const loading = ref<boolean>(false)
const disabledSubmit = computed(() => isIncomplete())
const isEUF = ref<boolean>(false)
const datasetsUpdated = ref<Dataset[]>([]) // ToDo: Do we need this? Seems to be just a copy of selectedDatasetsA
const datasetUploaded = ref<UploadedFile | null>()
const selectedDatasetsA = ref<Dataset[]>([])
const selectedDatasetsB = ref<Dataset[]>([])
const selectedOperation = ref<{ operation: ComparisonOperation; strandAware: boolean }>()

const records = ref()

const { handleSubmit, resetForm } = useForm()
const onSubmit = handleSubmit(() => {
  loading.value = true
  try {
    const params = getCompareParams(selectedOperation.value?.strandAware)
    switch (selectedOperation.value?.operation) {
      case ComparisonOperation.intersect:
        intersect(params, dialogState).then((data) => {
          records.value = data.map((x) => getComparisonDisplayRecord(x.a, x.b))
        })
        break

      case ComparisonOperation.closest:
        closest(params, dialogState).then((data) => {
          records.value = data.map((x) => getComparisonDisplayRecord(x.a, x.b, x.distance))
        })
        break

      case ComparisonOperation.subtract:
        subtract(params, dialogState).then((data) => {
          records.value = data.map((x) => getComparisonDisplayRecord(x))
        })
        break

      default:
        console.log(`Error: That should never happen!`)
    }
  } finally {
    loading.value = false
    resetForm()
  }
})

function getCompareParams(is_strand: boolean = true): ComparisonParams {
  return {
    reference: selectedDatasetsA.value.map((x) => x.dataset_id),
    comparison: selectedDatasetsB.value.map((x) => x.dataset_id),
    upload: datasetUploaded.value?.id,
    upload_name: datasetUploaded.value?.name,
    strand: is_strand,
    euf: isEUF.value
  }
}

function isIncomplete() {
  return (
    selectedDatasetsA.value.length === 0 ||
    (selectedDatasetsB.value.length === 0 && datasetUploaded.value === undefined)
  )
}

const buttonPt = {
  root: () => ({
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
            label="1"
            severity="secondary"
            :outlined="active !== 0"
            :pt="buttonPt"
            :ptOptions="{ mergeProps: true }"
          />
          <Button
            @click="active = 1"
            rounded
            label="2"
            severity="secondary"
            :outlined="active !== 1"
            :pt="buttonPt"
            :ptOptions="{ mergeProps: true }"
          />
          <Button
            @click="active = 2"
            rounded
            label="3"
            severity="secondary"
            :outlined="active !== 2"
            :pt="buttonPt"
            :ptOptions="{ mergeProps: true }"
          />
        </div>

        <TabView v-model:activeIndex="active">
          <TabPanel header="1. Select reference dataset">
            <div class="h-52">
              <div class="mb-4">
                Select one organism and choose up to three reference dataset. Use the dataset search
                bar to find records.^
              </div>
              <CompareStepA
                v-model="selectedDatasetsA"
                @datasets-updated="datasetsUpdated = $event"
              />
            </div>
          </TabPanel>
          <TabPanel header="2. Select dataset for comparison">
            <div class="h-52">
              <div class="mb-4">
                At least one reference dataset must be selected. Upload your own data or select up
                to three dataset for comparison. For upload, pay attention to the organism and/or
                the assembly of your data to avoid spurious comparison results.
              </div>
              <CompareStepB
                v-if="datasetsUpdated && selectedDatasetsA.length > 0"
                v-model="selectedDatasetsB"
                v-model:isEUF="isEUF"
                :selected-datasets="selectedDatasetsA"
                :datasets="datasetsUpdated"
                @dataset-uploaded="datasetUploaded = $event"
              />
            </div>
          </TabPanel>
          <TabPanel header="3. Select query criteria">
            <div>
              <form @submit="onSubmit">
                <div class="h-52">
                  <CompareStepC v-model="selectedOperation" />
                  <Button
                    icon="pi pi-sync"
                    size="small"
                    type="submit"
                    label="Submit"
                    :disabled="disabledSubmit"
                    :loading="loading"
                    class="mt-4"
                  />
                  <small id="text-error" class="p-4 select-none text-sm text-red-700">
                    <i
                      :class="[
                        uploadMessage ? 'pi pi-times-circle place-self-center text-red-700' : ''
                      ]"
                    />
                    {{ uploadMessage || '&nbsp;' }}
                  </small>
                </div>
              </form>
            </div>
          </TabPanel>
        </TabView>
      </div>
      <Divider />
      <div>
        <CompareResults v-model:records="records" v-model:loading="loading" />
      </div>
    </SectionLayout>
  </DefaultLayout>
</template>
