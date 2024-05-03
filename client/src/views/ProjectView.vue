<script setup>
import { ref } from 'vue'
import ProjectForm from '@/components/project/ProjectForm.vue'
import ProjectMetaData from '@/components/project/ProjectMetaData.vue'
import ProjectSubmission from '@/components/project/ProjectSubmission.vue'
import StyledHeadline from '@/components/ui/StyledHeadline.vue'
import SubTitle from '@/components/ui/SubTitle.vue'

const projectInfo = ref()
const projectData = ref()
const active = ref(0)
const completed = ref(false)
</script>

<template>
  <DefaultLayout>
    <SectionLayout>
      <StyledHeadline text="Project creation" />
      <SubTitle>Fill the template and request to create a new project</SubTitle>

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
