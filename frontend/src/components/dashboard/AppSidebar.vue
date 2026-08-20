<script setup>
import { ref, computed } from 'vue'
import IconBase from './IconBase.vue'
import { isAdmin } from '../../store/appState'

const isCollapsed = ref(false)

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

const nav = computed(() => {
  if (isAdmin.value) {
    return [
      { name: 'Admin Panel', icon: 'shield', to: '/admin' },
      { name: 'Users', icon: 'users', to: '/admin/users' },
      { name: 'Plans', icon: 'subscription', to: '/admin/plans' }
    ]
  }
  return [
    { name: 'Overview', icon: 'home', gif: '/assets/home.gif', to: '/' },
    { name: 'Equity Map', icon: 'map', gif: '/assets/map.gif', to: '/equity-map' },
    { name: 'SDOH Insights', icon: 'pulse', gif: '/assets/statistics.gif', to: '/sdoh-insights' },
    { name: 'Predictive Analytics', icon: 'trend', gif: '/assets/analysis.gif', to: '/predictive-analytics' },
    { name: 'Community Resources', icon: 'hand-heart', gif: '/assets/community.gif', to: '/community-resources' },
    { name: 'Interventions', icon: 'bulb', gif: '/assets/idea.gif', to: '/interventions' },
    { name: 'Reports', icon: 'report', gif: '/assets/report.gif', to: '/reports' },
  ]
})
</script>

<template>
  <aside class="sidebar" :class="{ collapsed: isCollapsed }">
    <div class="brand">
      <div class="brand-info">
        <img src="/assets/careequity_logo.png" class="brand-logo" alt="CareEquity Logo" />
        <div class="brand-text" v-show="!isCollapsed">
          <img src="/assets/careequity_name.png" class="brand-name-img" alt="CareEquity" />
        </div>
      </div>
      <button class="toggle-collapse-btn" @click="toggleCollapse" :title="isCollapsed ? 'Expand' : 'Collapse'">
        <IconBase :name="isCollapsed ? 'chevron-right' : 'chevron-left'" :size="16" />
      </button>
    </div>

    <nav class="nav">
      <router-link 
        v-for="item in nav" 
        :key="item.name" 
        :to="item.to" 
        class="nav-item" 
        exact-active-class="active" 
        :title="isCollapsed ? item.name : ''"
      >
        <img v-if="item.gif" :src="item.gif" class="nav-icon-gif" alt="" />
        <IconBase v-else :name="item.icon" :size="18" />
        <span class="nav-label" v-show="!isCollapsed">{{ item.name }}</span>
      </router-link>
    </nav>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 232px;
  flex-shrink: 0;
  background: var(--surface);
  border-right: 1px solid var(--border);
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1), padding 0.3s ease;
  padding: 22px 16px;
  box-sizing: border-box;
}

.sidebar.collapsed {
  width: 72px;
  padding: 22px 8px;
}

.brand {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 0 6px 22px;
  transition: padding 0.3s ease, flex-direction 0.3s ease;
}

.sidebar.collapsed .brand {
  flex-direction: column;
  padding: 0 0 16px;
  gap: 8px;
}

.brand-info {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.brand-logo {
  width: 32px;
  height: 32px;
  object-fit: contain;
  flex-shrink: 0;
}

.brand-text {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.brand-name-img {
  height: 60px;
  object-fit: contain;
  display: block;
}

.brand-sub {
  margin: 2px 0 0;
  font-size: 0.7rem;
  color: var(--text-tertiary);
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
}

.toggle-collapse-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  transition: background-color 0.15s ease, color 0.15s ease;
  flex-shrink: 0;
}

.toggle-collapse-btn:hover {
  background-color: #f3f4f6;
  color: var(--text-primary);
}

.nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 10px 12px;
  border-radius: 10px;
  color: var(--text-secondary);
  font-size: 0.86rem;
  font-weight: 500;
  transition: background 0.15s ease, color 0.15s ease, justify-content 0.3s ease, padding 0.3s ease;
  text-decoration: none;
}

.sidebar.collapsed .nav-item {
  justify-content: center;
  padding: 10px 0;
}

.nav-item:hover {
  background: #f5f7fb;
  color: var(--text-primary);
}

.nav-item.active {
  background: var(--brand-light);
  color: var(--brand-dark);
  font-weight: 600;
}

.nav-label {
  white-space: nowrap;
}

.nav-icon-gif {
  width: 24px;
  height: 24px;
  object-fit: contain;
  flex-shrink: 0;
}
</style>
