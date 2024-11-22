<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import Message from 'primevue/message'
import Button from 'primevue/button'
import { type ProjectPostRequest, postProject } from '@/services/management'
import { useDialogState } from '@/stores/DialogState'
import SectionLayout from '@/components/layout/SectionLayout.vue'

const props = defineProps<{
  data?: ProjectPostRequest
}>()

const dialogState = useDialogState()
const router = useRouter()
const message = ref<string>()

const submitForm = () => {
  if (props.data) {
    postProject(props.data, dialogState)
      .then(() => {
        router.push({ name: 'home' })
      })
      .catch(() => {})
  } else {
    throw new Error('Project submission without data - this should never happen!')
  }
}

const dropForm = () => {
  router.push({ name: 'home' })
}
</script>

<template>
  <SectionLayout>
    <div>
      <div class="flex flex-col mx-auto">
        <div class="text-center -mt-4 mb-4 text-xl font-semibold dark:text-white/80">
          Project submission
        </div>
      </div>
      <h3 class="mt-0 mb-4 dark:text-white/80">
        Click <span class="inline font-semibold">"Submit"</span> to send a project request. A
        notification will be sent to your email address as soon as the project is created. Click
        <span class="inline font-semibold">"Cancel"</span> to drop the request. In the latter case,
        all information that you entered will be lost.
      </h3>
      <div v-if="message" class="flex m-4 justify-center">
        <Message severity="error" :closable="false">{{ message }}</Message>
      </div>
      <div class="flex flow-row justify-center gap-4">
        <Button label="Submit" size="large" @click="submitForm" />
        <Button label="Cancel" size="large" severity="danger" @click="dropForm" />
      </div>
    </div>
  </SectionLayout>
</template>
