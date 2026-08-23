import { createRouter, createWebHashHistory } from 'vue-router'
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
import AdminUsers from '../pages/AdminUsers.vue'
import AdminPlans from '../pages/AdminPlans.vue'
import Plan from '../pages/Plan.vue'
import { isAnalyzed, isLoggedIn, isAdmin } from '../store/appState'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      name: 'setup',
      component: DataSetup,
    },
    {
      path: '/setup',
      redirect: '/',
    },
    {
      path: '/overview',
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
      path: '/admin/users',
      name: 'admin-users',
      component: AdminUsers,
    },
    {
      path: '/admin/plans',
      name: 'admin-plans',
      component: AdminPlans,
    },
    {
      path: '/plan',
      alias: '/plans',
      name: 'plan',
      component: Plan,
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
    if (to.name === 'admin' || to.name === 'admin-users' || to.name === 'admin-plans' || to.name === 'login') {
      next()
    } else {
      next({ name: 'admin' })
    }
  } else {
    if (to.name === 'admin' || to.name === 'admin-users' || to.name === 'admin-plans') {
      next({ name: 'login' })
    } else {
      next()
    }
  }
})

export default router
