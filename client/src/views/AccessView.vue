<script setup>
import { ref, onMounted } from 'vue'
import { useAccessToken } from '@/stores/AccessToken.js'
import { DIALOG, useDialogState } from '@/stores/DialogState.js'
import { loadProjects } from '@/services/project'

import StyledHeadline from '@/components/ui/StyledHeadline.vue'
import SubTitle from '@/components/ui/SubTitle.vue'
import LabeledItem from '@/components/ui/LabeledItem.vue'
import ItemBox from '@/components/ui/ItemBox.vue'

const accessToken = useAccessToken()
const dialogState = useDialogState()

const records = ref()

function changePassword() {
  dialogState.$patch({
    state: DIALOG.CHANGE_PASSWORD,
    message: null,
    email: accessToken.email,
    token: null
  })
}

onMounted(() => {
  // only list my projects
  loadProjects(records, null, true)
})
</script>

<template>
  <DefaultLayout>
    <SectionLayout>
      <StyledHeadline text="User account" />
      <SubTitle>Manage settings</SubTitle>

      <Divider />

      <ItemBox>
        <LabeledItem label="Email">
          {{ accessToken.email }}
        </LabeledItem>
        <LabeledItem label="Password">
          <Button label="Change" @click="changePassword()" size="small" />
        </LabeledItem>
      </ItemBox>
    </SectionLayout>
    <SectionLayout>
      <SubTitle>Projects created upon request</SubTitle>
      <Divider />
      <DataTable :value="records" tableStyle="min-width: 50rem">
        <Column field="project_id" header="SMID" />
        <Column field="project_title" header="Title" />
        <Column field="date_added" header="Added" />
      </DataTable>
    </SectionLayout>
  </DefaultLayout>
</template>
