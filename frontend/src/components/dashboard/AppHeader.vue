<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import IconBase from './IconBase.vue'
import { isLoggedIn, isAdmin, setLoggedIn, setShowLoginScreen, userPlan } from '../../store/appState'
import { MAIN_BACKEND_URL } from '../../config'

const router = useRouter()

const isCurrentRouteAdmin = computed(() => {
  return isAdmin.value || router.currentRoute.value.path.startsWith('/admin')
})

const userName = computed(() => {
  return localStorage.getItem('user_name') || (isAdmin.value ? 'Admin User' : 'Jane Smith')
})

const planBadgeText = computed(() => {
  if (!userPlan.value) return 'BASIC Plan'
  return `${userPlan.value.toUpperCase()} Plan`
})

const goToPlan = () => {
  router.push('/plan')
}

const triggerLogin = () => {
  setShowLoginScreen(true)
}

const handleLogout = async () => {
  const storedEmail = localStorage.getItem('user_email')
  try {
    await fetch(`${MAIN_BACKEND_URL}/api/auth/logout`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: storedEmail || '',
        password: '' // empty password, backend will set status to false
      })
    })
  } catch (err) {
    console.error('Logout error:', err)
  }
  
  localStorage.removeItem('docpat_logged_in')
  localStorage.removeItem('user_email')
  localStorage.removeItem('user_name')
  setLoggedIn(false)
}
</script>

<template>
  <header class="topbar">
    <div class="controls">
      <!-- Subscription plan badge (hidden for admin) -->
      <button v-if="!isCurrentRouteAdmin" class="chip chip-plan" @click="goToPlan" style="cursor: pointer; background: #eff6ff; border-color: #bfdbfe; color: #1d6bf3; font-weight: 600;" title="Manage Subscription Plan">
        <IconBase name="sparkle" :size="15" class="sparkle-icon" />
        {{ planBadgeText }}
      </button>

      <button class="chip chip-location">
        <IconBase name="pin" :size="15" />
        United States
        <IconBase name="chevron-down" :size="14" />
      </button>

      <!-- If logged in, show user name and Sign Out -->
      <button v-if="isLoggedIn" class="user" @click="handleLogout" title="Click to Logout" style="cursor: pointer; padding: 6px 12px; display: flex; align-items: center; gap: 8px;">
        <span class="user-text" style="display: inline-block;">
          <span class="user-name">{{ userName }}</span>
        </span>
        <span style="font-size: 10px; color: #ef4444; font-weight: 600; border: 1px solid rgba(239, 68, 68, 0.2); background: rgba(239, 68, 68, 0.05); padding: 2px 6px; border-radius: 6px; white-space: nowrap;">Sign Out</span>
      </button>

      <!-- If logged out, show Sign In / Login button -->
      <button v-else class="btn-login-trigger" @click="triggerLogin" style="height: 38px; border: 1px solid rgba(37, 99, 235, 0.2); border-radius: 10px; padding: 0 16px; background-image: linear-gradient(135deg, #3b82f6, #1d4ed8); color: #fff; font-size: 0.85rem; font-weight: 600; display: flex; align-items: center; gap: 8px; cursor: pointer; transition: opacity .15s ease; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.15);">
        <IconBase name="sparkle" :size="15" /> Sign In / Login
      </button>
    </div>
  </header>
</template>

<style scoped>
.topbar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 20px;
  padding: 16px 28px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
}

.search {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #f3f6fb;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 9px 14px;
  width: min(420px, 34vw);
  color: var(--text-tertiary);
}

.search input {
  border: none;
  outline: none;
  background: transparent;
  font-size: 0.86rem;
  color: var(--text-primary);
  width: 100%;
}

.controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.chip {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 8px 14px;
  border: 1px solid var(--border);
  border-radius: 10px;
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
}

@keyframes iconSpin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.chip-plan:hover .sparkle-icon,
.chip-plan:hover :deep(.sparkle-icon),
.btn-login-trigger:hover :deep(svg),
.btn-login-trigger:hover svg {
  animation: iconSpin 3.5s linear infinite;
}

.chip:hover {
  background: #f7f9fc;
}

.icon-btn {
  position: relative;
  width: 38px;
  height: 38px;
  border-radius: 10px;
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
}

.icon-btn:hover {
  background: #f7f9fc;
}

.badge {
  position: absolute;
  top: -5px;
  right: -5px;
  background: var(--red);
  color: #fff;
  font-size: 0.62rem;
  font-weight: 700;
  min-width: 16px;
  height: 16px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--surface);
}

.user {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 5px 10px 5px 5px;
  border-radius: 12px;
  border: 1px solid var(--border);
}

.user:hover {
  background: #f7f9fc;
}

.user img {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  object-fit: cover;
}

.user-text {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  line-height: 1.25;
}

.user-name {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-primary);
}

.user-role {
  font-size: 0.68rem;
  color: var(--text-tertiary);
}

@media (max-width: 1100px) {
  .chip span {
    display: none;
  }
}
</style>
