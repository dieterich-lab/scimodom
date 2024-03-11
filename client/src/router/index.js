import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import SearchView from '@/views/SearchView.vue'
import BrowseView from '@/views/BrowseView.vue'
import CompareView from '@/views/CompareView.vue'
import DownloadView from '@/views/DownloadView.vue'
import DocumentationView from '@/views/DocumentationView.vue'
import AccessView from '@/views/AccessView.vue'
import HomeRoadmap from '@/components/home/HomeRoadmap.vue'

import { useAccessToken } from '@/utils/AccessToken.js'
import { DIALOG, useDialogState } from '@/utils/DialogState.js'
import { HTTPSecure } from '@/services'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/',
      name: 'search',
      component: SearchView
    },
    {
      path: '/:eufid?',
      name: 'browse',
      props: true,
      component: BrowseView
    },
    {
      path: '/',
      name: 'compare',
      component: CompareView
    },
    {
      path: '/',
      name: 'download',
      component: DownloadView
    },
    {
      path: '/',
      name: 'documentation',
      component: DocumentationView
    },
    {
      path: '/',
      name: 'access',
      component: AccessView,
      meta: { requiresAuth: true }
    },
    {
      path: '/',
      name: 'roadmap',
      component: HomeRoadmap
    }
    // {
    //   path: '/about',
    //   name: 'about',
    //   // route level code-splitting
    //   // this generates a separate chunk (About.[hash].js) for this route
    //   // which is lazy-loaded when the route is visited.
    //   component: () => import('../views/AboutView.vue'),
    // },
  ],
  scrollBehavior(to, from, savedPosition) {
    // always scroll to top
    return { top: 0 }
  }
})

router.beforeEach((to, from) => {
  const accessToken = useAccessToken()
  HTTPSecure.interceptors.request.use(
    (config) => {
      const token = accessToken.token
      const auth = token ? `Bearer ${token}` : ''
      config.headers.Authorization = auth
      return config
    },
    (error) => Promise.reject(error)
  )
  if (to.meta.requiresAuth && accessToken.get == null) {
    const dialogState = useDialogState()
    dialogState.state = DIALOG.LOGIN
  }
})

export default router
