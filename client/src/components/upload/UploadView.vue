<script setup lang="ts">
import Divider from 'primevue/divider'
import TabPanel from 'primevue/tabpanel'
import TabView from 'primevue/tabview'
import DatasetUploadForm from '@/components/upload/DatasetUploadForm.vue'
import StyledHeadline from '@/components/ui/StyledHeadline.vue'
import SubTitle from '@/components/ui/SubTitle.vue'
import AttachBamForm from '@/components/upload/AttachBamForm.vue'
import { useAccessToken } from '@/stores/AccessToken'
import DefaultLayout from '@/components/layout/DefaultLayout.vue'
import SectionLayout from '@/components/layout/SectionLayout.vue'

const accessToken = useAccessToken()
</script>

<template>
  <DefaultLayout>
    <div v-if="accessToken.token == null">Not logged in.</div>
    <div v-else>
      <SectionLayout>
        <StyledHeadline text="Upload dataset" />
        <SubTitle>Upload a dataset to the database</SubTitle>

        <Divider />

        <p class="indent-4 text-lg leading-relaxed mt-2 mb-4 dark:text-white/80">
          To upload a bedRMod file, you need to select the project to which your dataset belongs. If
          there is no project yet for this dataset, create one with the
          <RouterLink :to="{ name: 'project' }" class="text-primary-500 hover:text-secondary-500">
            project template request
            <i class="pi pi-arrow-up-right -ml-4 text-sm" />
          </RouterLink>
        </p>
        <p class="indent-4 text-lg leading-relaxed mt-2 mb-4 dark:text-white/80">
          To attach files to a dataset, first upload a dataset.
        </p>
        <TabView>
          <TabPanel>
            <template #header>
              <div class="flex items-center gap-2">
                <i class="pi pi-file-arrow-up" />
                <span class="font-bold whitespace-nowrap">Upload bedRMod</span>
              </div>
            </template>
            <DatasetUploadForm />
          </TabPanel>
          <TabPanel>
            <template #header>
              <div class="flex items-center gap-2">
                <i class="pi pi-paperclip" />
                <span class="font-bold whitespace-nowrap">Attach BAM files</span>
              </div>
            </template>
            <AttachBamForm />
          </TabPanel>
        </TabView>
      </SectionLayout>
    </div>
  </DefaultLayout>
</template>
