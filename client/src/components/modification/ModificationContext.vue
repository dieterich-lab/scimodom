<script setup lang="ts">
import { ref, watch } from 'vue'
import { getGenomicContext, type Modification } from '@/services/modification'
import { useDialogState } from '@/stores/DialogState'
import { trashRequestErrors } from '@/services/API'

const DEFAULT_CONTEXT_INDEX = 5

const props = defineProps<{ modification?: Modification }>()
const dialogState = useDialogState()
const sequence = ref<string[]>([])

watch(
  () => props.modification,
  () => {
    if (props.modification) {
      const context_index = DEFAULT_CONTEXT_INDEX
      const modification = props.modification
      getGenomicContext(props.modification, context_index, dialogState)
        .then((x) => {
          sequence.value = getSequenceFromContext(modification, x, context_index)
        })
        .catch((e) => trashRequestErrors(e))
    } else {
      sequence.value = []
    }
  },
  { immediate: true }
)

function getSequenceFromContext(
  modification: Modification,
  context: string,
  context_index: number
): string[] {
  const span = context_index + modification.end - modification.start
  return [context.slice(0, context_index), context.slice(context_index, span), context.slice(span)]
}
</script>

<template>
  <span class="font-semibold"
    >{{ sequence[0] }}<span class="text-primary-500">{{ sequence[1] }}</span
    >{{ sequence[2] }}</span
  >
</template>
