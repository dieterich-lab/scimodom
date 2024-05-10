<script setup>
import { ScheduledUpload, UPLOAD_STATE } from '@/stores/UploadManager'

const props = defineProps({
  upload: {
    type: ScheduledUpload,
    required: true
  }
})

const STYLE_BY_STATE = new Map([
  [
    UPLOAD_STATE.WAITING,
    { icon: 'pi-hourglass', bg: 'bg-transparent', text: 'Waiting ...', cancelText: 'Abort' }
  ],
  [
    UPLOAD_STATE.RUNNING,
    { icon: 'pi-cloud-upload', bg: 'bg-sky-500', text: 'Running ...', cancelText: 'Ignore' }
  ],
  [
    UPLOAD_STATE.DONE,
    { icon: 'pi-check', bg: 'bg-green-500', text: 'Done.', cancelText: 'Dismiss' }
  ],
  [
    UPLOAD_STATE.FAILED,
    { icon: 'pi-exclamation-triangle', bg: 'bg-red-500', text: '', cancelText: 'Dismiss' }
  ]
])

const style = STYLE_BY_STATE.get(props.upload.state)
const icon = `pi ${style.icon}`
const classes = `relative ${style.bg} p-3 rounded-lg shadow-xl dark:shadow-surface-800/50`
const text =
  props.upload.state === UPLOAD_STATE.FAILED ? `Failed! ${props.upload.errorMessage}` : style.text
const text_color =
  props.upload.state === UPLOAD_STATE.FAILED ? 'text-white' : 'text-gray-500 dark:text-surface-400'
const text_classes = `${text_color} font-normal `
</script>
<template>
  <div :class="classes">
    <div>
      <h5 class="mb-1 text-xl font-semibold tracking-tight text-gray-900 dark:text-white/80">
        <i :class="icon" class="p-0 px-1 dark:text-white/80" />
        {{ upload.file.name }}
      </h5>
      <p :class="text_classes">
        {{ text }}
      </p>
    </div>
    <div class="absolute right-3 bottom-3">
      <Button
        @click="upload.remove()"
        class="p-4 !w-24 text-secondary-50 border border-secondary-300 ring-secondary-800"
        severity="secondary"
      >
        {{ style.cancelText }}
      </Button>
    </div>
  </div>
</template>
