<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import Button from 'primevue/button'
import {
  type ResultStepA,
  type ResultStepB,
  type ResultStepC,
  type OperationSpec,
  ComparisonOperation,
  isUpload
} from '@/utils/comparison'
import OperationButton from '@/components/compare/OperationButton.vue'

const props = defineProps<{
  resultStepA?: ResultStepA
  resultStepB?: ResultStepB
  loading: boolean
}>()
const model = defineModel<ResultStepC>()
const emit = defineEmits<{
  (e: 'submit', data: ResultStepC)
}>()

const selectedOperation = ref<OperationSpec>()

const doneWithStepA = computed(() => !!props.resultStepA?.datasets.length)
const doneWithStepB = computed(
  () => props.resultStepB && (isUpload(props.resultStepB) || !!props.resultStepB.datasets?.length)
)
const doneWithStepC = computed(() => doneWithStepA.value && doneWithStepB.value && model.value)

watch(
  () => props.resultStepB,
  () => {
    model.value = undefined
  }
)

function submit() {
  if (model.value) {
    emit('submit', model.value)
  }
}
</script>

<template>
  <div v-if="!doneWithStepA">Select reference dataset in step 1 to continue.</div>
  <div v-else-if="!doneWithStepB">Select dataset in step 2 to continue.</div>
  <div v-else>
    <div class="flex flex-col gap-4">
      <div class="flex flex-row">
        <div class="w-1/2" v-for="strandAware in [true, false]" :key="String(strandAware)">
          <OperationButton
            v-model="model"
            :value="{ operation: ComparisonOperation.intersect, strandAware: strandAware }"
          >
            overlaps between <span class="font-semibold">1</span> and
            <span class="font-semibold">2</span>
          </OperationButton>
        </div>
      </div>

      <div class="flex flex-row">
        <div class="w-1/2" v-for="strandAware in [true, false]" :key="String(strandAware)">
          <OperationButton
            v-model="model"
            :value="{ operation: ComparisonOperation.closest, strandAware: strandAware }"
          >
            closest non-overlaps in <span class="font-semibold">2</span> (wrt.
            <span class="font-semibold">1</span>)
          </OperationButton>
        </div>
      </div>

      <div class="flex flex-row">
        <div class="w-1/2" v-for="strandAware in [true, false]" :key="String(strandAware)">
          <OperationButton
            v-model="model"
            :value="{ operation: ComparisonOperation.subtract, strandAware: strandAware }"
          >
            strict non-overlaps in reference (modifications in
            <span class="font-semibold">1</span> but not in <span class="font-semibold">2</span>)
          </OperationButton>
        </div>
      </div>
    </div>

    <Button
      icon="pi pi-sync"
      size="small"
      type="submit"
      label="Submit"
      :disabled="!doneWithStepC"
      :loading="loading"
      class="mt-4"
      @click="submit"
    />
  </div>
</template>
