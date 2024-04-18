<script setup>
import { ref } from 'vue'

import { useRouter } from 'vue-router'

const router = useRouter()
const props = defineProps(['projectForm'])
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
        The project form has been successfully validated. Click
        <span class="inline font-semibold">"Submit"</span> to finalise the submission. A
        notification will be sent to your email address as soon as the project is created.
      </h3>
      <pre id="json" class="mt-3 mb-3 text-xl font-semibold">
          {{ JSON.stringify(projectForm, undefined, 2) }}
        </pre
      >
      <div class="flex justify-center">
        <Button label="Submit" size="large" @click="router.push({ name: 'home' })" />
      </div>
    </div>
  </SectionLayout>
</template>
