import { createRouter, createWebHistory } from 'vue-router'
import Overview from '../pages/Overview.vue'
import EquityMap from '../pages/EquityMap.vue'
import SDOHInsights from '../pages/SDOHInsights.vue'
import PredictiveAnalytics from '../pages/PredictiveAnalytics.vue'
import CommunityResources from '../pages/CommunityResources.vue'
import Interventions from '../pages/Interventions.vue'
import Reports from '../pages/Reports.vue'
import Login from '../pages/Login.vue'
import DataSetup from '../pages/DataSetup.vue'
import Admin from '../pages/Admin.vue'
import { isAnalyzed, isLoggedIn, isAdmin } from '../store/appState'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/setup',
      name: 'setup',
      component: DataSetup,
    },
    {
      path: '/login',
      name: 'login',
      component: Login,
    },
    {
      path: '/admin',
      name: 'admin',
      component: Admin,
    },
    {
      path: '/',
      name: 'overview',
      component: Overview,
    },
    {
      path: '/equity-map',
      name: 'equity-map',
      component: EquityMap,
    },
    {
      path: '/sdoh-insights',
      name: 'sdoh-insights',
      component: SDOHInsights,
    },
    {
      path: '/predictive-analytics',
      name: 'predictive-analytics',
      component: PredictiveAnalytics,
    },
    {
      path: '/community-resources',
      name: 'community-resources',
      component: CommunityResources,
    },
    {
      path: '/interventions',
      name: 'interventions',
      component: Interventions,
    },
    {
      path: '/reports',
      name: 'reports',
      component: Reports,
    },
  ],
})

router.beforeEach((to, from, next) => {
  if (isLoggedIn.value && isAdmin.value) {
    // Admin is strictly restricted to /admin (or logout/login route path)
    if (to.name === 'admin' || to.name === 'login') {
      next()
    } else {
      next({ name: 'admin' })
    }
  } else {
    // Normal user / guest flow
    if (to.name === 'admin') {
      next({ name: 'login' })
    } else if (to.name !== 'setup' && to.name !== 'login' && !isAnalyzed.value) {
      next({ name: 'setup' })
    } else if (to.name === 'setup' && isAnalyzed.value) {
      isAnalyzed.value = false
      next()
    } else {
      next()
    }
  }
})

export default router
