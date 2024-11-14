<script setup lang="ts">
import { ref } from 'vue'
import Divider from 'primevue/divider'
import TabPanel from 'primevue/tabpanel'
import TabView from 'primevue/tabview'

import DefaultLayout from '@/components/layout/DefaultLayout.vue'
import SectionLayout from '@/components/layout/SectionLayout.vue'
import TabButton from '@/components/compare/TabButton.vue'
import CompareStepA from '@/components/compare/CompareStepA.vue'
import CompareStepB from '@/components/compare/CompareStepB.vue'
import CompareStepC from '@/components/compare/CompareStepC.vue'
import CompareResults from '@/components/compare/CompareResults.vue'
import StyledHeadline from '@/components/ui/StyledHeadline.vue'
import SubTitle from '@/components/ui/SubTitle.vue'
import { type ComparisonParams } from '@/services/comparison'
import {
  ComparisonOperation,
  getCompareParams,
  type ResultStepA,
  type ResultStepB,
  type ResultStepC
} from '@/utils/comparison'

const tabIndex = ref<number>(0)
const resultStepA = ref<ResultStepA>()
const resultStepB = ref<ResultStepB>()
const resultStepC = ref<ResultStepC>()
const compareParams = ref<ComparisonParams>()
const operation = ref<ComparisonOperation>()
const queryRevision = ref<number>(0)
const loading = ref<boolean>(false)

function submit() {
  if (resultStepA.value && resultStepB.value && resultStepC.value) {
    compareParams.value = getCompareParams(resultStepA.value, resultStepB.value, resultStepC.value)
    operation.value = resultStepC.value.operation
    queryRevision.value += 1
  } else {
    throw new Error('Submit with incomplete parameters - this should never happen!')
  }
}

function resetResults() {
  compareParams.value = undefined
  queryRevision.value += 1
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
          <TabButton v-for="i in [0, 1, 2]" v-model="tabIndex" :tab-index="i" :key="i" />
        </div>

        <TabView v-model:activeIndex="tabIndex">
          <TabPanel header="1. Select reference dataset">
            <div class="h-52">
              <CompareStepA v-model="resultStepA" @change="resetResults" />
            </div>
          </TabPanel>
          <TabPanel header="2. Select dataset for comparison">
            <div class="h-52">
              <CompareStepB
                v-model="resultStepB"
                :result-step-a="resultStepA"
                @change="resetResults"
              />
            </div>
          </TabPanel>
          <TabPanel header="3. Select query criteria">
            <div class="h-52">
              <CompareStepC
                v-model="resultStepC"
                :result-step-a="resultStepA"
                :result-step-b="resultStepB"
                :loading="loading"
                @submit="submit"
              />
            </div>
          </TabPanel>
        </TabView>
      </div>
      <Divider />
      <div>
        <CompareResults
          v-model:loading="loading"
          :operation="operation"
          :params="compareParams"
          :key="queryRevision"
        />
      </div>
    </SectionLayout>
  </DefaultLayout>
</template>
