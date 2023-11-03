import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import SearchView from '@/views/SearchView.vue'
import BrowseView from '@/views/BrowseView.vue'
import CompareView from '@/views/CompareView.vue'
import DownloadView from '@/views/DownloadView.vue'
import DocumentationView from '@/views/DocumentationView.vue'
import StepsReference from '@/components/steps/StepsReference.vue'
import StepsComparison from '@/components/steps/StepsComparison.vue'
import StepsQuery from '@/components/steps/StepsQuery.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/search',
      name: 'search',
      component: SearchView
    },
    {
      path: '/browse',
      name: 'browse',
      component: BrowseView
    },
    {
      path: '/compare',
      name: 'compare',
      component: CompareView,
      children: [
        {
          path: 'reference',
          name: 'reference',
          component: StepsReference
        },
        {
          path: 'comparison',
          name: 'comparison',
          component: StepsComparison
        },
        {
          path: 'query',
          name: 'query',
          component: StepsQuery
        }
      ]
    },
    {
      path: '/download',
      name: 'download',
      component: DownloadView
    },
    {
      path: '/documentation',
      name: 'documentation',
      component: DocumentationView
    }
    // {
    //   path: '/about',
    //   name: 'about',
    //   // route level code-splitting
    //   // this generates a separate chunk (About.[hash].js) for this route
    //   // which is lazy-loaded when the route is visited.
    //   component: () => import('../views/AboutView.vue'),
    // },
  ]
})

export default router
