<script setup>
import { ref, onMounted } from 'vue'
import service from '@/services/index.js'

import { useRouter, useRoute } from 'vue-router'
import { RouterLink, RouterView } from 'vue-router'

const router = useRouter()
const route = useRoute()

const items = ref([
  {
    label: 'Select reference dataset',
    route: '/compare/reference'
  },
  {
    label: 'Select dataset for comparison',
    route: '/compare/comparison'
  },
  {
    label: 'Query criteria',
    route: '/compare/query'
  }
])

const isActive = (item) => {
  return item.route ? router.resolve(item.route).path === route.path : false
}
</script>

<template>
  <DefaultLayout>
    <SectionLayout>
      <h1 class="font-ham mb-4 text-3xl font-extrabold text-gray-900 md:text-5xl lg:text-6xl">
        <span
          class="text-transparent bg-clip-text bg-gradient-to-r from-crmapgreen2 from-10% via-crmapgreen1 via-40% via-crmapblue2 via-60% to-crmapblue4 to-100"
        >
          Compare
        </span>
        dataset
      </h1>
      <p class="text-lg font-normal text-gray-500 lg:text-xl">Perform complex queries</p>
      <Divider :pt="{ root: { class: 'bg-crmapgreen0' } }" />
      <div>
        <Steps
          :model="items"
          aria-label="Form Steps"
          :readonly="false"
          :pt="{
            action: { class: 'transition-none rounded-none focus:shadow-none' },
            step: ({ context }) => ({
              class:
                isActive(context.item) &&
                'font-semibold text-white bg-[#02b0edff] border-[#02b0edff]'
            })
          }"
        >
          <template #item="{ label, item, index, props }">
            <router-link v-if="item.route" v-slot="routerProps" :to="item.route" custom>
              <a
                :href="routerProps.href"
                v-bind="props.action"
                @click="($event) => routerProps.navigate($event)"
                @keydown.enter="($event) => routerProps.navigate($event)"
              >
                <span v-bind="props.step">{{ index + 1 }}</span>
                <span v-bind="props.label">{{ label }}</span>
              </a>
            </router-link>
            <span v-else v-bind="props.action">
              <span v-bind="props.step">{{ index + 1 }}</span>
              <span v-bind="props.label">{{ label }}</span>
            </span>
          </template>
        </Steps>

        <RouterView v-slot="{ Component }">
          <component :is="Component" />
        </RouterView>
      </div>
    </SectionLayout>
  </DefaultLayout>
</template>
