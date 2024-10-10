<script setup lang="ts">
import { useId } from 'vue'
import { type DetectionMethod } from '@/services/detection_method'
import FormFieldWrapper from '@/components/ui/FormFieldWrapper.vue'
import DetectionMethodSelection from '@/components/ui/DetectionMethodSelection.vue'
import { type FormFieldProps, FORM_FIELD_DEFAULTS } from '@/utils/ui_style'

withDefaults(defineProps<FormFieldProps>(), FORM_FIELD_DEFAULTS)

const model = defineModel<DetectionMethod>()

const emit = defineEmits<{ (e: 'change', method: DetectionMethod): void }>()

function change(method: DetectionMethod): void {
  emit('change', method)
}

const id = useId()
</script>
<template>
  <FormFieldWrapper :field-id="id" :error="error" :ui-style="uiStyle">
    <template v-slot:label>Method</template>
    <template v-slot:field>
      <DetectionMethodSelection
        v-model="model"
        :id="id"
        :markAsError="!!error"
        :ui-style="uiStyle"
        @change="change"
      />
    </template>
  </FormFieldWrapper>
</template>
