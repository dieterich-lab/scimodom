import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import SearchView from '@/views/SearchView.vue'
import BrowseView from '@/views/BrowseView.vue'
import CompareView from '@/views/CompareView.vue'
import DownloadView from '@/views/DownloadView.vue'
import DocumentationView from '@/views/TestDoc.vue'
// import DocumentationView from '@/views/DocumentationView.vue'
import DocAbout from '@/components/documentation/DocAbout.vue'
import DocSearch from '@/components/documentation/DocSearch.vue'
import DocBrowse from '@/components/documentation/DocBrowse.vue'
import DocCompare from '@/components/documentation/DocCompare.vue'
import DocManagement from '@/components/documentation/DocManagement.vue'
import DocFAQs from '@/components/documentation/DocFAQs.vue'

import HomeRoadmap from '@/components/home/HomeRoadmap.vue'

import PageMaintenance from '@/components/default/PageMaintenance.vue'
import PageNotFound from '@/components/default/PageNotFound.vue'

import UserAccountView from '@/views/UserAccountView.vue'
import ProjectView from '@/views/ProjectView.vue'
import UploadView from '@/views/UploadView.vue'

import { prepareAPI } from '@/services/API'

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
      path: '/browse/:eufid?',
      name: 'browse',
      props: true,
      component: BrowseView
    },
    {
      path: '/compare',
      name: 'compare',
      component: CompareView
    },
    {
      path: '/download',
      name: 'download',
      component: DownloadView,
      redirect: { name: 'PageNotFound' }
    },
    {
      path: '/documentation',
      component: DocumentationView,
      children: [
        {
          path: 'about',
          name: 'about-docs',
          component: DocAbout
        },
        {
          path: 'search',
          name: 'search-docs',
          component: DocSearch
        },
        {
          path: 'browse',
          name: 'browse-docs',
          component: DocBrowse
        },
        {
          path: 'compare',
          name: 'compare-docs',
          component: DocCompare
        },
        {
          path: 'management',
          name: 'management-docs',
          component: DocManagement
        },
        {
          path: 'faqs',
          name: 'faqs-docs',
          component: DocFAQs
        }
      ]
    },
    {
      path: '/roadmap',
      name: 'roadmap',
      component: HomeRoadmap
    },
    {
      path: '/user-account',
      name: 'user-account',
      component: UserAccountView,
      meta: { requiresAuth: true }
    },
    {
      path: '/project',
      name: 'project',
      component: ProjectView,
      meta: { requiresAuth: true }
    },
    {
      path: '/upload',
      name: 'upload',
      component: UploadView,
      meta: { requiresAuth: true }
    },
    {
      path: '/maintenance',
      name: 'maintenance',
      component: PageMaintenance
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'PageNotFound',
      component: PageNotFound
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
  linkActiveClass: 'text-primary-500',
  scrollBehavior(to, from, savedPosition) {
    // always scroll to top
    return { top: 0 }
  }
})

router.beforeEach((to, from) => {
  prepareAPI(to.meta.requiresAuth)
})

export default router
