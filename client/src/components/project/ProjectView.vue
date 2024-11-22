<script setup lang="ts">
import { computed, ref } from 'vue'
import Divider from 'primevue/divider'
import Stepper from 'primevue/stepper'
import StepperPanel from 'primevue/stepperpanel'

import ProjectInfoTab, { type ProjectInfoTabModel } from '@/components/project/ProjectInfoTab.vue'
import ProjectMetaDataTab, {
  type ProjectMetaDataTabModel
} from '@/components/project/ProjectMetaDataTab.vue'
import ProjectSubmissionTab from '@/components/project/ProjectSubmissionTab.vue'
import StyledHeadline from '@/components/ui/StyledHeadline.vue'
import SubTitle from '@/components/ui/SubTitle.vue'
import { useAccessToken } from '@/stores/AccessToken'
import DefaultLayout from '@/components/layout/DefaultLayout.vue'
import SectionLayout from '@/components/layout/SectionLayout.vue'
import type { ProjectPostRequest } from '@/services/management'

const projectInfoData = ref<ProjectInfoTabModel>()
const projectMetaData = ref<ProjectMetaDataTabModel>()
const active = ref(0)

const projectData = computed<ProjectPostRequest | undefined>(() => {
  if (projectInfoData.value && projectMetaData.value) {
    return {
      ...projectInfoData.value,
      metadata: projectMetaData.value
    }
  } else {
    return undefined
  }
})

const accessToken = useAccessToken()
</script>

<template>
  <DefaultLayout>
    <div v-if="accessToken.token == null">Not logged in.</div>
    <div v-else>
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
            <template #header="{ index }">
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
              <ProjectInfoTab :nextCallback="nextCallback" v-model="projectInfoData" />
            </template>
          </StepperPanel>
          <!-- ProjectMetadata  -->
          <StepperPanel>
            <template #header="{ index }">
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
              <ProjectMetaDataTab
                :nextCallback="nextCallback"
                :prevCallback="prevCallback"
                v-model="projectMetaData"
              />
            </template>
          </StepperPanel>
          <!-- Submission  -->
          <StepperPanel>
            <template #header="{ index }">
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
            <template #content>
              <ProjectSubmissionTab :data="projectData" />
            </template>
          </StepperPanel>
        </Stepper>
      </SectionLayout>
    </div>
  </DefaultLayout>
</template>
