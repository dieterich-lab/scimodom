<script setup lang="ts">
import Button from 'primevue/button'
import { ScheduledUpload, UPLOAD_STATE } from '@/stores/UploadManager'

interface Style {
  icon: string
  bg: string
  text: string
  cancelText: string
}

const props = defineProps<{
  upload: ScheduledUpload
}>()

const style = getStyle(props.upload.state)
const icon = `pi ${style.icon}`
const classes = `relative ${style.bg} p-3 rounded-lg shadow-xl dark:shadow-surface-800/50`
const text =
  props.upload.state === UPLOAD_STATE.FAILED ? `Failed! ${props.upload.errorMessage}` : style.text
const text_color =
  props.upload.state === UPLOAD_STATE.FAILED ? 'text-white' : 'text-gray-500 dark:text-surface-400'
const text_classes = `${text_color} font-normal `

function getStyle(state: UPLOAD_STATE): Style {
  switch (state) {
    case UPLOAD_STATE.WAITING:
      return {
        icon: 'pi-hourglass',
        bg: 'bg-transparent',
        text: 'Waiting ...',
        cancelText: 'Abort'
      }
    case UPLOAD_STATE.RUNNING:
      return {
        icon: 'pi-cloud-upload',
        bg: 'bg-sky-500',
        text: 'Running ...',
        cancelText: 'Ignore'
      }
    case UPLOAD_STATE.DONE:
      return { icon: 'pi-check', bg: 'bg-green-500', text: 'Done.', cancelText: 'Dismiss' }
    case UPLOAD_STATE.FAILED:
      return { icon: 'pi-exclamation-triangle', bg: 'bg-red-500', text: '', cancelText: 'Dismiss' }
  }
}
</script>
<template>
  <div :class="classes">
    <div>
      <h5 class="mb-1 text-xl font-semibold tracking-tight text-gray-900 dark:text-white/80">
        <i :class="icon" class="p-0 px-1 dark:text-white/80" />
        {{ upload.file.name }}
        <span class="font-thin ml-4 text-gray-500 dark:text-surface-400">{{ upload.info }}</span>
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
