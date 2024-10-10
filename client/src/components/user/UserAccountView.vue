<script setup lang="ts">
import Divider from 'primevue/divider'
import Button from 'primevue/button'
import { useAccessToken } from '@/stores/AccessToken.js'
import { DIALOG, useDialogState } from '@/stores/DialogState.js'

import StyledHeadline from '@/components/ui/StyledHeadline.vue'
import SubTitle from '@/components/ui/SubTitle.vue'
import LabeledItem from '@/components/ui/LabeledItem.vue'
import ItemBox from '@/components/ui/ItemBox.vue'
import UserProjects from '@/components/user/UserProjects.vue'
import DefaultLayout from '@/components/layout/DefaultLayout.vue'
import SectionLayout from '@/components/layout/SectionLayout.vue'

const accessToken = useAccessToken()
const dialogState = useDialogState()

function changePassword() {
  dialogState.$patch({
    state: DIALOG.CHANGE_PASSWORD,
    message: null,
    email: accessToken.email,
    token: null
  })
}
</script>

<template>
  <DefaultLayout>
    <div v-if="accessToken.token == null">Not logged in.</div>
    <div v-else>
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
        <UserProjects :key="accessToken.token" />
      </SectionLayout>
    </div>
  </DefaultLayout>
</template>
