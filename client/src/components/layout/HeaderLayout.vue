<script setup>
import { ref, computed } from 'vue'
import { DIALOG, useDialogState } from '@/utils/DialogState.js'
import { useAccessToken } from '@/utils/AccessToken.js'
import { useRouter } from 'vue-router'
import ScimodomLogo from './ScimodomLogo.vue'
import NavigationBar from './NavigationBar.vue'

const router = useRouter()

const dialogState = useDialogState()
const accessToken = useAccessToken()

const isLoggedIn = computed(() => accessToken.get !== null)
const userName = computed(getUserName)

const menu = ref()
const items = ref([
  // {
  //   separator: true
  // },
  {
    label: 'Data',
    items: [
      {
        label: 'Project template',
        icon: 'pi pi-file-edit',
        command: () => {
          router.push({ name: 'project' })
        }
      },
      {
        label: 'Dataset upload',
        icon: 'pi pi-upload',
        command: () => {
          router.push({ name: 'upload' })
        }
      }
    ]
  },
  {
    label: 'Profile',
    items: [
      {
        label: 'Settings',
        icon: 'pi pi-cog',
        command: () => {
          router.push({ name: 'access' })
        }
      },
      {
        label: 'Logout',
        icon: 'pi pi-sign-out',
        command: () => {
          accessToken.unset()
          router.push({ name: 'home' })
        }
      }
    ]
  }
])

const toggle = (event) => {
  menu.value.toggle(event)
}

function login() {
  dialogState.$patch({
    state: DIALOG.LOGIN,
    email: null,
    message: null
  })
}

function signUp() {
  dialogState.$patch({
    state: DIALOG.REGISTER_ENTER_DATA,
    email: null,
    message: null
  })
}

function getUserName() {
  let result = accessToken.email || ''
  if (result.length > 23) {
    result = result.substring(0, 20) + '...'
  }
  return result
}
</script>

<template>
  <header
    class="top-0 z-20 sticky bg-white opacity-90 border-b border-surface-200 dark:bg-surface-900 dark:opacity-100 dark:border-surface-800"
  >
    <div
      class="p-1 bg-gradient-to-r from-gg-2 from-10% via-gg-1 via-40% via-gb-2 via-60% to-gb-4 to-100%"
    />
    <div class="mx-auto w-full max-w-screen-2xl p-2 py-6 lg:py-8 flex flex-wrap items-center">
      <div class="flex flex-wrap 2xl:w-4/5 xl:w-auto">
        <ScimodomLogo />
        <NavigationBar />
      </div>
      <div v-if="isLoggedIn" class="flex flex-wrap 2xl:w-1/5 xl:w-auto 2xl:pl-8 xl:pl-0 gap-4">
        <Button
          size="small"
          icon="pi pi-user-edit"
          :label="userName"
          @click="toggle"
          aria-haspopup="true"
          aria-controls="overlay_menu"
          raised
        />
        <Menu ref="menu" id="overlay_menu" :model="items" :popup="true">
          <template #start>
            <span class="inline-flex items-center gap-1 px-2 py-2 w-full sm:w-[10rem]">
              <span class="font-medium font-ham text-xl">
                Sci-<span class="text-primary-500 dark:text-primary-400">Mo</span>d<span
                  class="text-secondary-500 dark:text-secondary-400"
                  >oM</span
                >
              </span>
            </span>
          </template>
          <template #submenuheader="{ item }">
            <span class="text-base text-primary-500 dark:text-primary-400 font-bold leading-none">{{
              item.label
            }}</span>
          </template>
          <template #item="{ item, props }">
            <a class="flex items-center" v-bind="props.action">
              <span :class="item.icon" />
              <span class="ml-2">{{ item.label }}</span>
            </a>
          </template>
        </Menu>
      </div>
      <div v-else class="flex flex-wrap 2xl:w-1/5 xl:w-auto 2xl:pl-8 xl:pl-0 gap-4">
        <Button label="Login" @click="login()" icon="pi pi-user" size="small" raised />
        <Button
          label="Sign Up"
          @click="signUp()"
          icon="pi pi-user-plus"
          size="small"
          severity="secondary"
          raised
        />
      </div>
    </div>
  </header>
</template>
