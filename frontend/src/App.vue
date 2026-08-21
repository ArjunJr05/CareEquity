<script setup>
import { onMounted, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppSidebar from './components/dashboard/AppSidebar.vue'
import AppHeader from './components/dashboard/AppHeader.vue'
import FloatingChatbot from './components/dashboard/FloatingChatbot.vue'
import { isAnalyzed, isLoggedIn, isAdmin, showLoginScreen, setPatientData, syncUserSubscription } from './store/appState'
import { MAIN_BACKEND_URL } from './config'

const route = useRoute()
const router = useRouter()

const isAdminRoute = computed(() => route.path.startsWith('/admin'))

// Boot user from admin panel on logout
watch([isLoggedIn, isAdmin], ([newLoggedIn, newAdmin]) => {
  if (route.path === '/admin' && (!newLoggedIn || !newAdmin)) {
    router.push('/login')
  }
  if (newLoggedIn) {
    syncUserSubscription(MAIN_BACKEND_URL)
  }
})

// Sync showLoginScreen state with the active route path
watch(() => route.path, (newPath) => {
  if (newPath === '/login') {
    showLoginScreen.value = true
  } else {
    showLoginScreen.value = false
  }
}, { immediate: true })

let previousPath = null
// Sync state change to route navigation
watch(showLoginScreen, (newVal) => {
  if (newVal && route.path !== '/login') {
    previousPath = route.path
    router.push('/login')
  } else if (!newVal && route.path === '/login') {
    if (previousPath) {
      previousPath = null
      router.back()
    } else {
      router.push('/')
    }
  }
})

onMounted(async () => {
  try {
    syncUserSubscription(MAIN_BACKEND_URL)
  } catch (error) {
    console.warn('Backend server not reachable, using local fallback state:', error)
  }
})
</script>

<template>
  <!-- 1. Explicitly requested full-screen views (Login, DataSetup, Plan) -->
  <div v-if="route.path === '/login' || route.path === '/setup' || route.path === '/plan'" class="full-page-container">
    <router-view />
  </div>

  <!-- 2. Standard Dashboard layout (if analyzed, whether logged in or logged out) -->
  <div v-else class="shell">
    <AppSidebar />
    <div class="shell-main">
      <AppHeader />
      <div class="shell-body">
        <router-view />
      </div>
    </div>
    <FloatingChatbot v-if="!isAdminRoute" />
  </div>
</template>

<style scoped>
.full-page-container {
  min-height: 100vh;
  background: var(--bg);
}

.shell {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.shell-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.shell-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
}
</style>
