<script setup>
import UploadForm from '@/components/upload/UploadForm.vue'
import StyledHeadline from '@/components/ui/StyledHeadline.vue'
import SubTitle from '@/components/ui/SubTitle.vue'
</script>

<template>
  <DefaultLayout>
    <SectionLayout>
      <StyledHeadline text="Upload dataset" />
      <SubTitle>Upload a dataset to the database</SubTitle>

      <Divider />

      <p class="indent-4 text-lg leading-relaxed mt-2 mb-4 dark:text-white/80">
        During upload you need to select the project to which your dataset belongs. If there is no
        project yet for this dataset, create one with the
        <RouterLink :to="{ name: 'project' }" class="text-primary-500 hover:text-secondary-500">
          project template request
          <i class="pi pi-arrow-up-right -ml-4 text-sm" />
        </RouterLink>
      </p>
      <TabView>
        <TabPanel>
          <template #header>
            <div class="flex items-center gap-2">
              <i class="pi pi-file-arrow-up" />
              <span class="font-bold whitespace-nowrap">Upload EUF (bedRMod)</span>
            </div>
          </template>
          <UploadForm />
        </TabPanel>
        <TabPanel>
          <template #header>
            <div class="flex items-center gap-2">
              <i class="pi pi-paperclip" />
              <span class="font-bold whitespace-nowrap">Attach other files</span>
            </div>
          </template>
          <p class="m-0">
            Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
            incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud
            exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure
            dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
            Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt
            mollit anim id est laborum.
          </p>
        </TabPanel>
      </TabView>
    </SectionLayout>
  </DefaultLayout>
</template>
