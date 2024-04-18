<script setup>
import { ref } from 'vue'
import ProjectForm from '@/components/project/ProjectForm.vue'
import ProjectMetaData from '@/components/project/ProjectMetaData.vue'
import ProjectSubmission from '@/components/project/ProjectSubmission.vue'

const projectInfo = ref()
const projectData = ref()

const active = ref(0)
const completed = ref(false)
const products = ref()
const name = ref()
const email = ref()
const password = ref()
const option1 = ref(false)
const option2 = ref(false)
const option3 = ref(false)
const option4 = ref(false)
const option5 = ref(false)
const option6 = ref(false)
const option7 = ref(false)
const option8 = ref(false)
const option9 = ref(false)
const option10 = ref(false)
</script>

<template>
  <DefaultLayout>
    <SectionLayout>
      <h1
        class="font-ham mb-4 text-3xl font-extrabold text-gray-900 dark:text-white/80 md:text-5xl lg:text-6xl"
      >
        <span
          class="text-transparent bg-clip-text bg-gradient-to-r from-gg-2 from-10% via-gg-1 via-40% via-gb-2 via-60% to-gb-4 to-100"
        >
          Project
        </span>
        creation
      </h1>
      <p class="text-lg font-normal text-gray-500 dark:text-surface-400 lg:text-xl">
        Fill the template and request to create a new project
      </p>
      <Divider />
      <p class="text-lg leading-relaxed mt-2 mb-4 dark:text-white/80">
        To upload data to an existing project, use the
        <RouterLink :to="{ name: 'upload' }" class="text-primary-500 hover:text-secondary-500">
          dataset upload form
          <i class="pi pi-arrow-up-right text-sm" />
        </RouterLink>
        <br />
        To create a new project, complete the form below.
      </p>
      <Stepper v-model:activeStep="active">
        <!-- ProjectForm  -->
        <StepperPanel>
          <template #header="{ index, clickCallback }">
            <span
              :class="[
                'rounded-md border-2 w-[3rem] h-[3rem] inline-flex items-center justify-center',
                {
                  'bg-primary-500 dark:bg-primary-400 border-primary*500 dark:border-primary-400':
                    index <= active,
                  'border-surface-200 dark:border-surface-700': index > active
                }
              ]"
            >
              <i class="pi pi-file-edit" />
            </span>
          </template>
          <template #content="{ nextCallback }">
            <ProjectForm :nextCallback="nextCallback" v-model="projectInfo" />
          </template>
        </StepperPanel>
        <!-- ProjectMetadata  -->
        <StepperPanel>
          <template #header="{ index, clickCallback }">
            <span
              :class="[
                'rounded-md border-2 w-[3rem] h-[3rem] inline-flex items-center justify-center',
                {
                  'bg-primary-500 dark:bg-primary-400 border-primary*500 dark:border-primary-400':
                    index <= active,
                  'border-surface-200 dark:border-surface-700': index > active
                }
              ]"
            >
              <i class="pi pi-file-plus" />
            </span>
          </template>
          <template #content="{ prevCallback, nextCallback }">
            <ProjectMetaData
              :nextCallback="nextCallback"
              :prevCallback="prevCallback"
              v-model="projectData"
            />
          </template>
        </StepperPanel>
        <!-- Submission  -->
        <StepperPanel>
          <template #header="{ index, clickCallback }">
            <span
              :class="[
                'rounded-md border-2 w-[3rem] h-[3rem] inline-flex items-center justify-center',
                {
                  'bg-primary-500 dark:bg-primary-400 border-primary*500 dark:border-primary-400':
                    index <= active,
                  'border-surface-200 dark:border-surface-700': index > active
                }
              ]"
            >
              <i class="pi pi-file-export" />
            </span>
          </template>
          <template #content="{ prevCallback }">
            <ProjectSubmission :projectForm="{ ...projectInfo, ...projectData }" />
          </template>
        </StepperPanel>
      </Stepper>
    </SectionLayout>
  </DefaultLayout>
</template>
