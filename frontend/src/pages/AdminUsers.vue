<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import IconBase from '../components/dashboard/IconBase.vue'
import { MAIN_BACKEND_URL } from '../config'

const router = useRouter()

// Toast state
const showToast = ref(false)
const toastMsg = ref('')
const triggerToast = (msg) => {
  toastMsg.value = msg
  showToast.value = true
  setTimeout(() => {
    showToast.value = false
  }, 3000)
}

// User state
const usersList = ref([])
const summaryStats = ref({
  totalUsers: 0,
  activeUsers: 0,
  proUsers: 0,
  basicUsers: 0,
  freeUsers: 0,
  nonPlanUsers: 0
})
const isLoading = ref(true)

// Filter & Search states
const searchQuery = ref('')
const selectedPlanFilter = ref('all') // 'all', 'pro', 'basic', 'free', 'none'

const fetchUsers = async () => {
  try {
    const res = await fetch(`${MAIN_BACKEND_URL}/api/admin/users`)
    if (res.ok) {
      const data = await res.json()
      usersList.value = data.users || []
      summaryStats.value = data.summary || {
        totalUsers: data.users.length,
        activeUsers: data.users.filter(u => u.status).length,
        proUsers: data.users.filter(u => u.plan === 'pro').length,
        basicUsers: data.users.filter(u => u.plan === 'basic').length,
        freeUsers: data.users.filter(u => u.plan === 'free').length,
        nonPlanUsers: data.users.filter(u => u.plan === 'none').length
      }
    }
  } catch (err) {
    console.error('Failed to fetch users from backend:', err)
  } finally {
    isLoading.value = false
  }
}

let pollTimer = null
onMounted(() => {
  fetchUsers()
  pollTimer = setInterval(fetchUsers, 8000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

// Filtered Users Computed List
const filteredUsers = computed(() => {
  return usersList.value.filter(user => {
    // 1. Search Query filter (Name, Email, ID)
    const q = searchQuery.value.trim().toLowerCase()
    const matchesSearch = !q || 
      (user.name && user.name.toLowerCase().includes(q)) ||
      (user.email && user.email.toLowerCase().includes(q)) ||
      String(user.id).includes(q)

    // 2. Plan filter ('all', 'pro', 'basic', 'free', 'none')
    const matchesPlan = selectedPlanFilter.value === 'all' || user.plan === selectedPlanFilter.value

    return matchesSearch && matchesPlan
  })
})

// Helper for Initials
const getInitials = (name) => {
  if (!name) return 'U'
  const parts = name.trim().split(' ')
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase()
  }
  return name.substring(0, 2).toUpperCase()
}

// Color generator based on name
const getAvatarColor = (name) => {
  const colors = [
    '#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#ec4899', '#06b6d4', '#6366f1'
  ]
  if (!name) return colors[0]
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  return colors[Math.abs(hash) % colors.length]
}

// Helper to format UTC to local time string
const formatLocalTime = (utcStr) => {
  if (!utcStr || utcStr === 'N/A') return 'N/A'
  try {
    const dateStr = utcStr.includes('Z') || utcStr.includes('+') ? utcStr : (utcStr.replace(' ', 'T') + 'Z')
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) return utcStr

    const y = date.getFullYear()
    const m = String(date.getMonth() + 1).padStart(2, '0')
    const d = String(date.getDate()).padStart(2, '0')
    let hours = date.getHours()
    const minutes = String(date.getMinutes()).padStart(2, '0')
    const ampm = hours >= 12 ? 'PM' : 'AM'
    hours = hours % 12
    hours = hours ? hours : 12
    const hrStr = String(hours).padStart(2, '0')

    return `${y}-${m}-${d} ${hrStr}:${minutes} ${ampm}`
  } catch (e) {
    return utcStr
  }
}

// Export CSV of Users
const exportUsersCSV = () => {
  if (filteredUsers.value.length === 0) {
    triggerToast('No user data to export')
    return
  }

  const headers = ['User ID', 'Full Name', 'Email', 'Plan', 'Validity', 'Subscribed At', 'Online Status', 'Registered At', 'Last Login']
  const rows = filteredUsers.value.map(u => [
    u.id,
    u.name,
    u.email,
    u.plan.toUpperCase(),
    u.validity,
    u.subscribed_at || 'N/A',
    u.status ? 'Online' : 'Offline',
    u.created_at || 'N/A',
    u.last_login || 'N/A'
  ])

  const csvContent = [headers.join(','), ...rows.map(e => e.map(val => `"${val}"`).join(','))].join('\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.setAttribute('href', url)
  link.setAttribute('download', `careequity_users_${Date.now()}.csv`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  triggerToast('Exported users dataset to CSV')
}
</script>

<template>
  <div class="admin-users-page">
    <!-- Toast notification -->
    <Transition name="fade">
      <div v-if="showToast" class="toast-popup">
        <IconBase name="shield" :size="14" />
        <span>{{ toastMsg }}</span>
      </div>
    </Transition>

    <div class="main-layout">
      <div class="content-body">
        
        <!-- Page Header -->
        <header class="page-header">
          <div>
            <h1 class="page-title">User Management Directory</h1>
            <p class="description">
              View registered users in PostgreSQL, monitor subscription statuses, and filter by membership plan.
            </p>
          </div>
          <div class="header-actions">
            <button class="export-btn" @click="exportUsersCSV" title="Export users table to CSV">
              <IconBase name="download" :size="15" />
              <span>Export CSV</span>
            </button>
          </div>
        </header>

        <!-- KPI Metrics Grid (5 Cards) -->
        <section class="kpi-grid">
          <!-- Total Users -->
          <div class="kpi-card" :class="{ 'card-active': selectedPlanFilter === 'all' }" @click="selectedPlanFilter = 'all'">
            <div class="kpi-top">
              <span class="kpi-icon icon-blue">
                <IconBase name="users" :size="18" />
              </span>
              <span class="kpi-badge">Registered</span>
            </div>
            <h3 class="kpi-val">{{ summaryStats.totalUsers }}</h3>
            <p class="kpi-lbl">Total Users</p>
          </div>

          <!-- PRO Plan -->
          <div class="kpi-card" :class="{ 'card-active': selectedPlanFilter === 'pro' }" @click="selectedPlanFilter = 'pro'">
            <div class="kpi-top">
              <span class="kpi-icon icon-purple">
                <IconBase name="sparkle" :size="18" />
              </span>
              <span class="kpi-badge badge-purple">PRO Tier</span>
            </div>
            <h3 class="kpi-val">{{ summaryStats.proUsers }}</h3>
            <p class="kpi-lbl">PRO Subscribers</p>
          </div>

          <!-- BASIC Plan -->
          <div class="kpi-card" :class="{ 'card-active': selectedPlanFilter === 'basic' }" @click="selectedPlanFilter = 'basic'">
            <div class="kpi-top">
              <span class="kpi-icon icon-blue-sub">
                <IconBase name="shield" :size="18" />
              </span>
              <span class="kpi-badge badge-blue">BASIC Tier</span>
            </div>
            <h3 class="kpi-val">{{ summaryStats.basicUsers }}</h3>
            <p class="kpi-lbl">BASIC Subscribers</p>
          </div>

          <!-- FREE Trial -->
          <div class="kpi-card" :class="{ 'card-active': selectedPlanFilter === 'free' }" @click="selectedPlanFilter = 'free'">
            <div class="kpi-top">
              <span class="kpi-icon icon-teal">
                <IconBase name="hand-heart" :size="18" />
              </span>
              <span class="kpi-badge badge-teal">15-Day Trial</span>
            </div>
            <h3 class="kpi-val">{{ summaryStats.freeUsers }}</h3>
            <p class="kpi-lbl">Free Trial Users</p>
          </div>

          <!-- Non-Plan Users -->
          <div class="kpi-card" :class="{ 'card-active': selectedPlanFilter === 'none' }" @click="selectedPlanFilter = 'none'">
            <div class="kpi-top">
              <span class="kpi-icon icon-slate">
                <IconBase name="pin" :size="18" />
              </span>
              <span class="kpi-badge badge-slate">Unsubscribed</span>
            </div>
            <h3 class="kpi-val">{{ summaryStats.nonPlanUsers }}</h3>
            <p class="kpi-lbl">Non-Plan Users</p>
          </div>
        </section>

        <!-- Search & Plan Filter Bar -->
        <section class="table-card">
          <div class="filter-toolbar">
            <!-- Plan Filter Pills -->
            <div class="plan-pills">
              <button 
                class="pill-btn" 
                :class="{ active: selectedPlanFilter === 'all' }"
                @click="selectedPlanFilter = 'all'"
              >
                All Users ({{ summaryStats.totalUsers }})
              </button>
              <button 
                class="pill-btn pill-pro" 
                :class="{ active: selectedPlanFilter === 'pro' }"
                @click="selectedPlanFilter = 'pro'"
              >
                👑 PRO Plan ({{ summaryStats.proUsers }})
              </button>
              <button 
                class="pill-btn pill-basic" 
                :class="{ active: selectedPlanFilter === 'basic' }"
                @click="selectedPlanFilter = 'basic'"
              >
                🛡️ BASIC Plan ({{ summaryStats.basicUsers }})
              </button>
              <button 
                class="pill-btn pill-free" 
                :class="{ active: selectedPlanFilter === 'free' }"
                @click="selectedPlanFilter = 'free'"
              >
                🎁 FREE Trial ({{ summaryStats.freeUsers }})
              </button>
              <button 
                class="pill-btn pill-none" 
                :class="{ active: selectedPlanFilter === 'none' }"
                @click="selectedPlanFilter = 'none'"
              >
                ⚪ Non-Plan Users ({{ summaryStats.nonPlanUsers }})
              </button>
            </div>

            <!-- Search and Status Controls -->
            <div class="controls-right">
              <div class="search-box">
                <IconBase name="search" :size="14" class="search-icon" />
                <input 
                  v-model="searchQuery" 
                  type="text" 
                  placeholder="Search by name, email, or ID..." 
                />
                <button v-if="searchQuery" class="clear-search" @click="searchQuery = ''">&times;</button>
              </div>
            </div>
          </div>

          <!-- Users Table -->
          <div class="table-responsive">
            <table class="users-table">
              <thead>
                <tr>
                  <th style="width: 70px;">ID</th>
                  <th>User Details (Name & Email)</th>
                  <th>Subscription Plan</th>
                  <th>Validity Cycle</th>
                  <th>Subscribed Date</th>
                  <th>Registered At</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in filteredUsers" :key="user.id">
                  <!-- User ID -->
                  <td class="id-col">
                    <span class="id-pill">#{{ user.id }}</span>
                  </td>

                  <!-- User Name & Email -->
                  <td class="user-cell">
                    <div class="user-info-row">
                      <div class="avatar" :style="{ backgroundColor: getAvatarColor(user.name) }">
                        {{ getInitials(user.name) }}
                      </div>
                      <div class="user-text-col">
                        <span class="user-name-text font-bold">{{ user.name || 'Unnamed User' }}</span>
                        <span class="user-email-text">{{ user.email }}</span>
                      </div>
                    </div>
                  </td>

                  <!-- Subscription Plan Badge -->
                  <td>
                    <span v-if="user.plan === 'pro'" class="plan-badge badge-pro">
                      <span class="plan-dot"></span> PRO Plan
                    </span>
                    <span v-else-if="user.plan === 'basic'" class="plan-badge badge-basic">
                      <span class="plan-dot"></span> BASIC Plan
                    </span>
                    <span v-else-if="user.plan === 'free'" class="plan-badge badge-free">
                      <span class="plan-dot"></span> FREE Trial (15 Days)
                    </span>
                    <span v-else class="plan-badge badge-none">
                      <span class="plan-dot dot-grey"></span> Non-Plan User
                    </span>
                  </td>

                  <!-- Validity -->
                  <td>
                    <span class="validity-tag" :class="user.validity">
                      {{ user.validity === 'monthly' ? 'Monthly Billed' : (user.validity === 'yearly' ? 'Yearly Billed' : (user.validity === '15_days' ? '15 Days Trial' : 'None / Free Tier')) }}
                    </span>
                  </td>

                  <!-- Subscribed Date -->
                  <td class="timestamp-cell">
                    <span v-if="user.subscribed_at" class="date-text">
                      {{ formatLocalTime(user.subscribed_at) }}
                    </span>
                    <span v-else class="text-muted">
                      Not Subscribed
                    </span>
                  </td>

                  <!-- Registered Date -->
                  <td class="timestamp-cell text-muted">
                    {{ formatLocalTime(user.created_at) }}
                  </td>
                </tr>

                <tr v-if="filteredUsers.length === 0">
                  <td colspan="6" class="empty-state">
                    <div class="empty-box">
                      <IconBase name="users" :size="32" class="empty-icon" />
                      <h4>No users found</h4>
                      <p>Try adjusting your search query or switching the plan filter.</p>
                      <button class="reset-filter-btn" @click="searchQuery = ''; selectedPlanFilter = 'all'">
                        Reset Filters
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-users-page {
  min-height: 100%;
  overflow-y: auto;
  background: #f8fafc;
  color: #1e293b;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  padding: 24px 36px 60px;
  box-sizing: border-box;
}

.main-layout {
  max-width: 1360px;
  margin: 0 auto;
}

/* Sub-Nav Bar */
.admin-sub-nav {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 6px;
  margin-bottom: 22px;
  width: fit-content;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
}

.sub-nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 18px;
  border-radius: 8px;
  color: #64748b;
  font-size: 0.88rem;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.2s ease;
}

.sub-nav-item:hover {
  color: #1d6bf3;
  background: #eff6ff;
}

.sub-nav-item.active {
  background: #1d6bf3;
  color: #ffffff;
  box-shadow: 0 4px 12px rgba(29, 107, 243, 0.25);
}

.nav-count-badge {
  background: rgba(255, 255, 255, 0.25);
  color: #ffffff;
  padding: 2px 7px;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 700;
}

.sub-nav-item:not(.active) .nav-count-badge {
  background: #e2e8f0;
  color: #475569;
}

/* Header */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.page-title {
  font-size: 1.85rem;
  font-weight: 800;
  color: #0f172a;
  margin: 0 0 4px;
  letter-spacing: -0.02em;
}

.description {
  font-size: 0.92rem;
  color: #64748b;
  margin: 0;
}

.export-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #ffffff;
  border: 1.5px solid #cbd5e1;
  border-radius: 10px;
  padding: 9px 18px;
  font-size: 0.88rem;
  font-weight: 600;
  color: #334155;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
  transition: all 0.2s ease;
}

.export-btn:hover {
  background: #f1f5f9;
  border-color: #94a3b8;
  transform: translateY(-1px);
}

/* KPI Grid */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.kpi-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 16px 18px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
  cursor: pointer;
  transition: all 0.2s ease;
}

.kpi-card:hover {
  transform: translateY(-2px);
  border-color: #93c5fd;
  box-shadow: 0 8px 20px rgba(37, 99, 235, 0.08);
}

.kpi-card.card-active {
  border-color: #1d6bf3;
  box-shadow: 0 0 0 2px rgba(29, 107, 243, 0.15);
  background: #f0f7ff;
}

.kpi-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.kpi-icon {
  width: 36px;
  height: 36px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-blue { background: #eff6ff; color: #2563eb; }
.icon-green { background: #ecfdf5; color: #059669; }
.icon-purple { background: #f5f3ff; color: #7c3aed; }
.icon-blue-sub { background: #e0f2fe; color: #0284c7; }
.icon-teal { background: #f0fdfa; color: #0d9488; }
.icon-slate { background: #f1f5f9; color: #64748b; }

.kpi-badge {
  font-size: 0.72rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 6px;
  background: #f1f5f9;
  color: #475569;
}

.badge-green { background: #d1fae5; color: #065f46; }
.badge-purple { background: #ede9fe; color: #5b21b6; }
.badge-blue { background: #dbeafe; color: #1e40af; }
.badge-teal { background: #ccfbf1; color: #115e59; }
.badge-slate { background: #f1f5f9; color: #475569; }

.kpi-val {
  font-size: 1.6rem;
  font-weight: 800;
  color: #0f172a;
  margin: 0 0 4px;
}

.kpi-lbl {
  font-size: 0.8rem;
  color: #64748b;
  font-weight: 500;
  margin: 0;
}

/* Table Section Card */
.table-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.03);
  overflow: hidden;
}

.filter-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: #fcfdfe;
  border-bottom: 1px solid #e2e8f0;
  gap: 16px;
  flex-wrap: wrap;
}

.plan-pills {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.pill-btn {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 9999px;
  padding: 6px 14px;
  font-size: 0.82rem;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s ease;
}

.pill-btn:hover {
  background: #f8fafc;
  border-color: #94a3b8;
}

.pill-btn.active {
  background: #1d6bf3;
  border-color: #1d6bf3;
  color: #ffffff;
  box-shadow: 0 2px 8px rgba(29, 107, 243, 0.25);
}

.controls-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 12px;
  color: #94a3b8;
}

.search-box input {
  padding: 8px 32px 8px 34px;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  font-size: 0.84rem;
  outline: none;
  width: 240px;
  transition: border-color 0.2s ease;
}

.search-box input:focus {
  border-color: #1d6bf3;
  box-shadow: 0 0 0 3px rgba(29, 107, 243, 0.1);
}

.clear-search {
  position: absolute;
  right: 10px;
  background: transparent;
  border: none;
  font-size: 1.1rem;
  color: #94a3b8;
  cursor: pointer;
}

.status-select {
  padding: 8px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  font-size: 0.84rem;
  font-weight: 500;
  color: #334155;
  outline: none;
  background: #ffffff;
  cursor: pointer;
}

/* Users Table */
.table-responsive {
  width: 100%;
  overflow-x: auto;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 0.88rem;
}

.users-table th {
  padding: 13px 18px;
  background: #f8fafc;
  color: #475569;
  font-weight: 700;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border-bottom: 1px solid #e2e8f0;
}

.users-table td {
  padding: 14px 18px;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: middle;
}

.users-table tr:hover {
  background: #f8fbff;
}

.id-pill {
  font-family: monospace;
  font-weight: 700;
  color: #64748b;
  background: #f1f5f9;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 0.8rem;
}

.user-info-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 0.85rem;
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.user-text-col {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
}

.user-name-text {
  color: #0f172a;
  font-weight: 700;
  font-size: 0.92rem;
}

.user-email-text {
  color: #64748b;
  font-size: 0.8rem;
}

/* Plan Badges */
.plan-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 9999px;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.plan-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
}

.badge-pro {
  background: #f5f3ff;
  color: #7c3aed;
  border: 1px solid #ddd6fe;
}

.badge-basic {
  background: #eff6ff;
  color: #1d6bf3;
  border: 1px solid #bfdbfe;
}

.badge-free {
  background: #ecfdf5;
  color: #059669;
  border: 1px solid #a7f3d0;
}

.badge-none {
  background: #f1f5f9;
  color: #64748b;
  border: 1px solid #e2e8f0;
}

.dot-grey {
  background: #94a3b8;
}

.validity-tag {
  font-size: 0.82rem;
  color: #334155;
  font-weight: 600;
}

.timestamp-cell {
  font-size: 0.82rem;
  color: #475569;
}

.text-muted {
  color: #94a3b8;
  font-size: 0.8rem;
}

/* Status Chip */
.status-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border-radius: 9999px;
  font-size: 0.76rem;
  font-weight: 700;
}

.status-chip.online {
  background: #dcfce7;
  color: #15803d;
}

.status-ping {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #16a34a;
  box-shadow: 0 0 0 2px rgba(22, 163, 74, 0.3);
}

.status-chip.offline {
  background: #f1f5f9;
  color: #94a3b8;
}

/* Empty State */
.empty-state {
  padding: 48px 16px !important;
  text-align: center;
}

.empty-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.empty-icon {
  color: #cbd5e1;
  margin-bottom: 4px;
}

.empty-box h4 {
  font-size: 1.1rem;
  color: #334155;
  margin: 0;
}

.empty-box p {
  font-size: 0.86rem;
  color: #64748b;
  margin: 0 0 12px;
}

.reset-filter-btn {
  background: #1d6bf3;
  color: #ffffff;
  border: none;
  border-radius: 8px;
  padding: 7px 16px;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
}

/* Toast */
.toast-popup {
  position: fixed;
  top: 24px;
  right: 24px;
  background: #0f172a;
  color: #ffffff;
  padding: 10px 18px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  z-index: 9999;
}

@media (max-width: 1024px) {
  .kpi-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 640px) {
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
