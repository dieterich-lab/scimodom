<script setup>
import StyledHeadline from '@/components/ui/StyledHeadline.vue'
import SubTitle from '@/components/ui/SubTitle.vue'
import LabeledItem from '@/components/ui/LabeledItem.vue'
import ItemBox from '@/components/ui/ItemBox.vue'
import { useAccessToken } from '@/stores/AccessToken.js'
import { DIALOG, useDialogState } from '@/stores/DialogState.js'

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
  </DefaultLayout>
</template>
