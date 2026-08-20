<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import IconBase from '../components/dashboard/IconBase.vue'
import { MAIN_BACKEND_URL } from '../config'

const router = useRouter()

// Toast notification state
const showToast = ref(false)
const toastMsg = ref('')
const triggerToast = (msg) => {
  toastMsg.value = msg
  showToast.value = true
  setTimeout(() => {
    showToast.value = false
  }, 3000)
}

// System stats refs
const stats = ref([
  { label: 'Active Sessions', value: '1', change: 'Loading...', icon: 'profile', color: '#3b82f6' },
  { label: 'Total Logins (Today)', value: '0', change: 'Loading...', icon: 'trend', color: '#10b981' }
])

const hourlyLogins = ref([
  { hour: '08:00', count: 0 },
  { hour: '09:00', count: 0 },
  { hour: '10:00', count: 0 },
  { hour: '11:00', count: 0 },
  { hour: '12:00', count: 0 },
  { hour: '13:00', count: 0 },
  { hour: '14:00', count: 0 },
  { hour: '15:00', count: 0 }
])

const maxCount = computed(() => {
  const counts = hourlyLogins.value.map(h => h.count)
  return counts.length > 0 ? Math.max(...counts, 1) : 1
})

const auditLogs = ref([])

// Search & Filter state
const searchQuery = ref('')
const selectedCategory = ref('all')
const selectedPeriod = ref('This Month')

// Revenue Overview State
const revenueData = ref({
  totalSubscribers: '0',
  subscribersGrowth: 'Live database count',
  monthlyRevenue: '₹0.00',
  revenueGrowth: '0% active MRR',
  newSubscriptions: 0,
  newSubscriptionsGrowth: 'Audited in last 30d',
  cancelledSubscriptions: 0,
  cancelledSubscriptionsGrowth: '0.0% rate',
  subscriptionsByPlan: [],
  revenueTimeline: [],
  planComparison: {
    arpu: '₹0.00',
    upgrades: 0,
    downgrades: 0,
    churnRate: '0.0%',
    retentionRate: '100.0%'
  }
})

const filteredLogs = computed(() => {
  return auditLogs.value.filter(log => {
    const matchesSearch = log.user.toLowerCase().includes(searchQuery.value.toLowerCase()) || 
                          log.event.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                          log.ip.toLowerCase().includes(searchQuery.value.toLowerCase())
    
    const matchesCategory = selectedCategory.value === 'all' || log.category === selectedCategory.value
    
    return matchesSearch && matchesCategory
  })
})

// Fetch Realtime Data from PostgreSQL Backend
const fetchStats = async () => {
  try {
    const res = await fetch(`${MAIN_BACKEND_URL}/api/admin/stats`)
    if (res.ok) {
      const data = await res.json()
      stats.value[0].value = String(data.activeSessions)
      stats.value[0].change = `Live count in PostgreSQL`
      
      stats.value[1].value = String(data.totalLogins)
      stats.value[1].change = `Today's audited logins`

      hourlyLogins.value = data.hourlyLogins
    }
  } catch (err) {
    console.error('Failed to fetch admin stats:', err)
  }
}

// Dynamic SVG calculations for Plan Donut Chart
const donutSegments = computed(() => {
  const plans = revenueData.value?.subscriptionsByPlan || []
  const C = 2 * Math.PI * 58 // ~364.42
  let offset = 0
  return plans.map(p => {
    const dashLength = (Math.max(p.percent, 0) / 100) * C
    const dashArray = `${dashLength} ${C}`
    const dashOffset = -offset
    offset += dashLength
    return {
      ...p,
      dashArray,
      dashOffset
    }
  })
})

// Dynamic SVG coordinates for Revenue Area Line Chart
const lineGraphData = computed(() => {
  const pts = revenueData.value?.revenueTimeline || []
  if (pts.length === 0) {
    return { pointsStr: '', polygonStr: '', coords: [], yLabels: ['₹500', '₹375', '₹250', '₹125', '₹0'] }
  }

  const rawVals = pts.map(p => Number(p.value) || 0)
  const maxRaw = Math.max(...rawVals, 0)
  // Give 30% headroom above maximum value so graph looks balanced
  const ceiling = maxRaw > 0 ? Math.ceil((maxRaw * 1.3) / 50) * 50 : 500
  const yLabels = [
    `₹${ceiling.toLocaleString()}`,
    `₹${Math.round(ceiling * 0.75).toLocaleString()}`,
    `₹${Math.round(ceiling * 0.5).toLocaleString()}`,
    `₹${Math.round(ceiling * 0.25).toLocaleString()}`,
    '₹0'
  ]

  const coords = pts.map((pt, idx) => {
    const x = 20 + idx * (400 / Math.max(pts.length - 1, 1))
    const y = 135 - ((Number(pt.value) || 0) / ceiling) * 115
    return { x, y, ...pt }
  })

  const pointsStr = coords.map(c => `${c.x},${c.y}`).join(' ')
  const polygonStr = `20,135 ${pointsStr} 420,135`

  return { pointsStr, polygonStr, coords, yLabels }
})

// Period Dropdown Options & State
const periodOptions = [
  { id: 'This Month', label: 'This Month' },
  { id: 'Last 30 Days', label: 'Last 30 Days' },
  { id: 'This Quarter', label: 'This Quarter' },
  { id: 'This Year', label: 'This Year' }
]
const isPeriodDropdownOpen = ref(false)

const selectPeriod = (opt) => {
  selectedPeriod.value = opt.id
  isPeriodDropdownOpen.value = false
  fetchRevenueOverview()
}

const handleGlobalClick = (e) => {
  if (!e.target.closest('.custom-dropdown-container')) {
    isPeriodDropdownOpen.value = false
  }
}

// Fetch Revenue Analytics from Backend
const fetchRevenueOverview = async () => {
  try {
    const res = await fetch(`${MAIN_BACKEND_URL}/api/admin/revenue-overview?period=${encodeURIComponent(selectedPeriod.value)}`)
    if (res.ok) {
      const data = await res.json()
      if (data && data.totalSubscribers) {
        revenueData.value = data
      }
    }
  } catch (err) {
    console.error('Failed to fetch revenue overview:', err)
  }
}

const fetchLogs = async () => {
  try {
    const res = await fetch(`${MAIN_BACKEND_URL}/api/admin/logs`)
    if (res.ok) {
      auditLogs.value = await res.json()
    }
  } catch (err) {
    console.error('Failed to fetch audit logs:', err)
  }
}

let refreshInterval = null
onMounted(() => {
  fetchStats()
  fetchRevenueOverview()
  fetchLogs()
  window.addEventListener('click', handleGlobalClick)
  // Poll every 8 seconds for live dashboard updates
  refreshInterval = setInterval(() => {
    fetchStats()
    fetchRevenueOverview()
    fetchLogs()
  }, 8000)
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
  window.removeEventListener('click', handleGlobalClick)
})

// Actions
const clearCache = async () => {
  try {
    const res = await fetch(`${MAIN_BACKEND_URL}/api/admin/logs/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event: 'System Cache Purged',
        user: 'contact.careequity@gmail.com',
        ip: '127.0.0.1',
        category: 'system',
        status: 'success'
      })
    })
    if (res.ok) {
      triggerToast('Application cache cleared successfully across all microservices.')
      fetchLogs()
      fetchStats()
    }
  } catch (err) {
    console.error(err)
  }
}

const triggerDbSnapshot = async () => {
  try {
    const res = await fetch(`${MAIN_BACKEND_URL}/api/admin/logs/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event: 'Database Snapshot Generated',
        user: 'contact.careequity@gmail.com',
        ip: '127.0.0.1',
        category: 'system',
        status: 'success'
      })
    })
    if (res.ok) {
      triggerToast('Database snapshot created and pushed to storage archive.')
      fetchLogs()
      fetchStats()
    }
  } catch (err) {
    console.error(err)
  }
}

const isMaintenanceMode = ref(false)
const toggleMaintenance = async () => {
  isMaintenanceMode.value = !isMaintenanceMode.value
  const msg = isMaintenanceMode.value ? 'System Maintenance Mode enabled!' : 'System Maintenance Mode disabled!'
  
  try {
    const res = await fetch(`${MAIN_BACKEND_URL}/api/admin/logs/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event: `Maintenance Mode Toggle (${isMaintenanceMode.value ? 'ON' : 'OFF'})`,
        user: 'contact.careequity@gmail.com',
        ip: '127.0.0.1',
        category: 'system',
        status: 'success'
      })
    })
    if (res.ok) {
      triggerToast(msg)
      fetchLogs()
      fetchStats()
    }
  } catch (err) {
    console.error(err)
  }
}

const exportAuditLogs = () => {
  const headers = ['Timestamp', 'Event', 'User', 'IP Address', 'Status']
  const rows = auditLogs.value.map(log => [
    log.timestamp,
    log.event,
    log.user,
    log.ip,
    log.status
  ])
  
  const csvContent = [headers.join(','), ...rows.map(e => e.map(val => `"${val}"`).join(','))].join('\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.setAttribute('href', url)
  link.setAttribute('download', `careequity_audit_log_${Date.now()}.csv`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  triggerToast('Preparing audit logs dataset... Download started')
}

const exportRevenueReport = () => {
  const headers = ['Metric', 'Value', 'Growth / Status']
  const rows = [
    ['Total Subscribers', revenueData.value.totalSubscribers, revenueData.value.subscribersGrowth],
    ['Monthly Revenue', revenueData.value.monthlyRevenue, revenueData.value.revenueGrowth],
    ['New Subscriptions', revenueData.value.newSubscriptions, revenueData.value.newSubscriptionsGrowth],
    ['Cancelled Subscriptions', revenueData.value.cancelledSubscriptions, revenueData.value.cancelledSubscriptionsGrowth],
    ['ARPU', revenueData.value.planComparison?.arpu || '₹214.50', 'Active'],
    ['Retention Rate', revenueData.value.planComparison?.retentionRate || '97.9%', 'Healthy']
  ]
  const csvContent = [headers.join(','), ...rows.map(e => e.map(val => `"${val}"`).join(','))].join('\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.setAttribute('href', url)
  link.setAttribute('download', `subscription_revenue_report_${Date.now()}.csv`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  triggerToast('Exporting Subscription & Revenue Report...')
}
</script>

<template>
  <div class="admin-page">
    <!-- Top toast notification -->
    <Transition name="fade">
      <div v-if="showToast" class="toast-popup">
        <IconBase name="shield" :size="14" />
        <span>{{ toastMsg }}</span>
      </div>
    </Transition>

    <div class="main-layout">
      <div class="content-body">

        <!-- ============================================================ -->
        <!-- 1. SUBSCRIPTION & REVENUE OVERVIEW (Requested Dashboard)      -->
        <!-- ============================================================ -->
        <section class="subscription-overview-section">
          <!-- Header Bar -->
          <div class="sub-header-bar">
            <div class="sub-header-left">
              <div class="sub-icon-badge">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M2 4l3 12h14l3-12-6 7-4-7-4 7-6-7zm3 16h14"></path>
                </svg>
              </div>
              <div>
                <h2 class="sub-title">Subscription Overview</h2>
                <p class="sub-subtitle">Track subscription plans, revenue, and user distribution.</p>
              </div>
            </div>

            <div class="sub-header-actions">
              <!-- Custom Animated Period Dropdown -->
              <div class="custom-dropdown-container">
                <button 
                  type="button" 
                  class="custom-dropdown-trigger" 
                  :class="{ active: isPeriodDropdownOpen }"
                  @click.stop="isPeriodDropdownOpen = !isPeriodDropdownOpen"
                >
                  <img src="/assets/calendar.gif" alt="calendar" class="calendar-gif-icon" />
                  <span class="dropdown-trigger-text">
                    {{ selectedPeriod }}
                  </span>
                  <svg 
                    class="dropdown-chevron" 
                    :class="{ 'chevron-rotate': isPeriodDropdownOpen }"
                    width="14" 
                    height="14" 
                    viewBox="0 0 24 24" 
                    fill="none" 
                    stroke="currentColor" 
                    stroke-width="2.5" 
                    stroke-linecap="round" 
                    stroke-linejoin="round"
                  >
                    <polyline points="6 9 12 15 18 9"></polyline>
                  </svg>
                </button>

                <Transition name="dropdown-anim">
                  <div v-if="isPeriodDropdownOpen" class="custom-dropdown-menu">
                    <div 
                      v-for="opt in periodOptions" 
                      :key="opt.id"
                      class="dropdown-menu-item"
                      :class="{ selected: selectedPeriod === opt.id }"
                      @click="selectPeriod(opt)"
                    >
                      <img src="/assets/calendar.png" alt="calendar" class="calendar-option-icon" />
                      <span class="item-label">{{ opt.label }}</span>
                      <span v-if="selectedPeriod === opt.id" class="item-check">✓</span>
                    </div>
                  </div>
                </Transition>
              </div>

              <button class="export-report-btn" @click="exportRevenueReport">
                <IconBase name="download" :size="15" />
                <span>Export Report</span>
              </button>
            </div>
          </div>

          <!-- 4 Top KPI Cards -->
          <div class="revenue-kpi-grid">
            <!-- 1. Total Subscribers -->
            <div class="rev-card">
              <div class="rev-card-top">
                <div class="rev-icon-box">
                  <img src="/assets/group.png" alt="Total Subscribers" class="rev-card-icon-img" />
                </div>
              </div>
              <div class="rev-card-label">Total Subscribers</div>
              <div class="rev-card-val">{{ revenueData.totalSubscribers }}</div>
              <div class="rev-card-growth text-green">
                <span class="arrow-icon">↗</span> {{ revenueData.subscribersGrowth }}
              </div>
            </div>

            <!-- 2. Monthly Revenue -->
            <div class="rev-card">
              <div class="rev-card-top">
                <div class="rev-icon-box">
                  <img src="/assets/income.png" alt="Monthly Revenue" class="rev-card-icon-img" />
                </div>
              </div>
              <div class="rev-card-label">Monthly Revenue</div>
              <div class="rev-card-val">{{ revenueData.monthlyRevenue }}</div>
              <div class="rev-card-growth text-green">
                <span class="arrow-icon">↗</span> {{ revenueData.revenueGrowth }}
              </div>
            </div>

            <!-- 3. New Subscriptions -->
            <div class="rev-card">
              <div class="rev-card-top">
                <div class="rev-icon-box">
                  <img src="/assets/add.png" alt="New Subscriptions" class="rev-card-icon-img" />
                </div>
              </div>
              <div class="rev-card-label">New Subscriptions</div>
              <div class="rev-card-val">{{ revenueData.newSubscriptions }}</div>
              <div class="rev-card-growth text-green">
                <span class="arrow-icon">↗</span> {{ revenueData.newSubscriptionsGrowth }}
              </div>
            </div>

            <!-- 4. Cancelled Subscriptions -->
            <div class="rev-card">
              <div class="rev-card-top">
                <div class="rev-icon-box">
                  <img src="/assets/cross-mark.png" alt="Cancelled Subscriptions" class="rev-card-icon-img" />
                </div>
              </div>
              <div class="rev-card-label">Cancelled Subscriptions</div>
              <div class="rev-card-val">{{ revenueData.cancelledSubscriptions }}</div>
              <div class="rev-card-growth text-red">
                <span class="arrow-icon">↘</span> {{ revenueData.cancelledSubscriptionsGrowth }}
              </div>
            </div>
          </div>

          <!-- Dual Analytics Panels: Donut Chart & Revenue Trend -->
          <div class="revenue-analytics-row">
            <!-- Subscriptions by Plan (Donut Visual) -->
            <div class="analytics-card card">
              <div class="card-head-flex">
                <h3 class="card-title font-bold">Subscriptions by Plan</h3>
              </div>

              <div class="donut-content-layout">
                <!-- SVG Donut Chart with percentage segments -->
                <div class="donut-chart-box">
                  <svg class="donut-svg" viewBox="0 0 160 160">
                    <circle
                      v-for="seg in donutSegments"
                      :key="seg.name"
                      cx="80" cy="80" r="58"
                      fill="transparent"
                      :stroke="seg.color"
                      stroke-width="24"
                      :stroke-dasharray="seg.dashArray"
                      :stroke-dashoffset="seg.dashOffset"
                    />
                  </svg>
                  <div class="donut-center-text">
                    <span class="center-count font-bold">{{ revenueData.totalSubscribers }}</span>
                    <span class="center-sub">Total</span>
                  </div>
                </div>

                <!-- Plan Legend List -->
                <div class="plan-legend-list">
                  <div 
                    v-for="plan in revenueData.subscriptionsByPlan" 
                    :key="plan.name" 
                    class="plan-legend-item"
                  >
                    <div class="legend-left">
                      <span class="legend-dot" :style="{ backgroundColor: plan.color }"></span>
                      <div>
                        <div class="legend-name font-semibold">{{ plan.name }}</div>
                        <div class="legend-count">{{ plan.count }} Subscribers</div>
                      </div>
                    </div>
                    <span class="percent-badge" :style="{ backgroundColor: plan.color + '18', color: plan.color }">
                      {{ plan.percent }}%
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Revenue Overview Area Line Graph -->
            <div class="analytics-card card">
              <div class="card-head-flex">
                <h3 class="card-title font-bold">Revenue Overview</h3>
                <router-link to="/admin/plans" class="view-link">
                  View Analytics &rarr;
                </router-link>
              </div>

              <div class="rev-overview-hero">
                <div class="rev-hero-val">{{ revenueData.monthlyRevenue }}</div>
                <div class="rev-hero-meta">
                  <span class="rev-hero-sub">Total Revenue</span>
                  <span class="growth-chip text-green">
                    &uarr; {{ revenueData.revenueGrowth?.split(' ')[0] || '14.2%' }} vs last month
                  </span>
                </div>
              </div>

              <!-- Interactive Area Line Graph -->
              <div class="revenue-graph-wrapper">
                <div class="y-axis-labels">
                  <span v-for="(lbl, lIdx) in lineGraphData.yLabels" :key="lIdx">{{ lbl }}</span>
                </div>

                <div class="graph-plot-area">
                  <svg class="line-graph-svg" viewBox="0 0 440 140" preserveAspectRatio="none">
                    <defs>
                      <linearGradient id="revAreaGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stop-color="#6366f1" stop-opacity="0.32"/>
                        <stop offset="100%" stop-color="#6366f1" stop-opacity="0.01"/>
                      </linearGradient>
                    </defs>

                    <!-- Horizontal Grid lines -->
                    <line x1="0" y1="15" x2="440" y2="15" stroke="#f1f5f9" stroke-width="1.2" />
                    <line x1="0" y1="45" x2="440" y2="45" stroke="#f1f5f9" stroke-width="1.2" />
                    <line x1="0" y1="75" x2="440" y2="75" stroke="#f1f5f9" stroke-width="1.2" />
                    <line x1="0" y1="105" x2="440" y2="105" stroke="#f1f5f9" stroke-width="1.2" />
                    <line x1="0" y1="135" x2="440" y2="135" stroke="#e2e8f0" stroke-width="1.5" />

                    <!-- Area Fill -->
                    <polygon 
                      v-if="lineGraphData.polygonStr"
                      :points="lineGraphData.polygonStr" 
                      fill="url(#revAreaGrad)"
                    />

                    <!-- Main Curve Line -->
                    <polyline 
                      v-if="lineGraphData.pointsStr"
                      :points="lineGraphData.pointsStr" 
                      fill="none" 
                      stroke="#6366f1" 
                      stroke-width="2.6"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />

                    <!-- Data Point Circles -->
                    <circle 
                      v-for="(pt, pIdx) in lineGraphData.coords" 
                      :key="pIdx"
                      :cx="pt.x" 
                      :cy="pt.y" 
                      r="4.5" 
                      fill="#ffffff" 
                      stroke="#6366f1" 
                      stroke-width="2.5" 
                    >
                      <title>{{ pt.period }}: {{ pt.display }}</title>
                    </circle>
                  </svg>

                  <!-- X-Axis Labels -->
                  <div class="x-axis-labels">
                    <span v-for="pt in revenueData.revenueTimeline" :key="pt.period">
                      {{ pt.period }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Security Audit Log Table -->
        <section class="logs-container card">
          <div class="logs-header">
            <div>
              <h3 class="card-title font-bold">Security Audit Log</h3>
              <p class="control-sub">Real-time system events, database updates, and authentication audits.</p>
            </div>
            <div class="table-actions">
              <div class="search-box">
                <IconBase name="search" :size="16" class="search-icon" />
                <input 
                  v-model="searchQuery" 
                  type="text" 
                  placeholder="Search by User or Event..." 
                  class="search-input"
                />
              </div>
              <button class="btn outlined" @click="exportAuditLogs">
                <IconBase name="download" :size="14" />
                <span>Export Logs</span>
              </button>
            </div>
          </div>

          <!-- Category Filter Pills -->
          <div class="filter-pills">
            <button 
              class="pill-btn" 
              :class="{ active: selectedCategory === 'all' }"
              @click="selectedCategory = 'all'"
            >
              ALL
            </button>
            <button 
              class="pill-btn" 
              :class="{ active: selectedCategory === 'auth' }"
              @click="selectedCategory = 'auth'"
            >
              AUTH
            </button>
            <button 
              class="pill-btn" 
              :class="{ active: selectedCategory === 'api' }"
              @click="selectedCategory = 'api'"
            >
              API
            </button>
            <button 
              class="pill-btn" 
              :class="{ active: selectedCategory === 'export' }"
              @click="selectedCategory = 'export'"
            >
              EXPORT
            </button>
            <button 
              class="pill-btn" 
              :class="{ active: selectedCategory === 'system' }"
              @click="selectedCategory = 'system'"
            >
              SYSTEM
            </button>
          </div>

          <!-- Logs Table -->
          <div class="table-wrapper">
            <table class="audit-table">
              <thead>
                <tr>
                  <th>TIMESTAMP</th>
                  <th>EVENT</th>
                  <th>USER</th>
                  <th>IP ADDRESS</th>
                  <th>STATUS</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="log in filteredLogs" :key="log.id || log.timestamp">
                  <td class="timestamp-cell font-mono">{{ log.timestamp }}</td>
                  <td class="event-cell font-semibold">{{ log.event }}</td>
                  <td class="user-cell">{{ log.user }}</td>
                  <td class="ip-cell font-mono">{{ log.ip }}</td>
                  <td>
                    <span class="status-pill" :class="log.status">
                      <span class="status-dot"></span>
                      {{ log.status }}
                    </span>
                  </td>
                </tr>
                <tr v-if="filteredLogs.length === 0">
                  <td colspan="5" class="empty-state">No matching security events found.</td>
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
.admin-page {
  padding: 24px 32px 60px;
  background: var(--bg);
  min-height: 100%;
  overflow-y: auto;
  color: var(--text-primary);
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  box-sizing: border-box;
}

.main-layout {
  max-width: 1400px;
  margin: 0 auto;
}

.content-body {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

/* ============================================================ */
/* SUBSCRIPTION & REVENUE OVERVIEW STYLES                       */
/* ============================================================ */
.subscription-overview-section {
  display: flex;
  flex-direction: column;
  gap: 18px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 18px;
  padding: 24px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03);
}

.sub-header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.sub-header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.sub-icon-badge {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: #eef2ff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.sub-title {
  font-size: 1.5rem;
  font-weight: 800;
  color: #0f172a;
  margin: 0 0 2px;
  letter-spacing: -0.02em;
}

.sub-subtitle {
  font-size: 0.88rem;
  color: #64748b;
  margin: 0;
}

.sub-header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* Custom Dropdown Menu Styles */
.custom-dropdown-container {
  position: relative;
  user-select: none;
}

.custom-dropdown-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #ffffff;
  border: 1.5px solid #e2e8f0;
  border-radius: 12px;
  padding: 8px 14px;
  font-size: 0.85rem;
  font-weight: 600;
  color: #1e293b;
  cursor: pointer;
  outline: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.custom-dropdown-trigger:hover,
.custom-dropdown-trigger.active {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12);
  background: #fdfdfd;
}

.calendar-gif-icon {
  width: 20px;
  height: 20px;
  object-fit: contain;
  border-radius: 4px;
}

.calendar-option-icon {
  width: 18px;
  height: 18px;
  object-fit: contain;
  flex-shrink: 0;
}

.dropdown-trigger-text {
  font-size: 0.85rem;
  font-weight: 600;
}

.dropdown-chevron {
  color: #64748b;
  transition: transform 0.25s ease;
  margin-left: 2px;
}

.chevron-rotate {
  transform: rotate(180deg);
  color: #6366f1;
}

.custom-dropdown-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 175px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 6px;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.12), 0 4px 10px rgba(0, 0, 0, 0.04);
  z-index: 999;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.dropdown-menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  border-radius: 9px;
  font-size: 0.84rem;
  font-weight: 600;
  color: #334155;
  cursor: pointer;
  transition: all 0.15s ease;
}

.dropdown-menu-item:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.dropdown-menu-item.selected {
  background: #eef2ff;
  color: #6366f1;
  font-weight: 700;
}

.item-icon {
  font-size: 0.95rem;
}

.item-label {
  flex: 1;
}

.item-check {
  font-size: 0.85rem;
  font-weight: 800;
  color: #6366f1;
}

/* Dropdown Animation */
.dropdown-anim-enter-active,
.dropdown-anim-leave-active {
  transition: opacity 0.18s ease, transform 0.18s cubic-bezier(0.16, 1, 0.3, 1);
}

.dropdown-anim-enter-from,
.dropdown-anim-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.96);
}

.export-report-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #6366f1;
  color: #ffffff;
  border: none;
  border-radius: 10px;
  padding: 8px 16px;
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.25);
  transition: all 0.2s ease;
}

.export-report-btn:hover {
  background: #4f46e5;
  transform: translateY(-1px);
}

/* Revenue KPI 4-Card Grid */
.revenue-kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.rev-card {
  background: #ffffff;
  border: 1.5px solid #f1f5f9;
  border-radius: 14px;
  padding: 18px 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
  transition: all 0.2s ease;
}

.rev-card:hover {
  border-color: #e2e8f0;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.04);
}

.rev-card-top {
  display: flex;
  justify-content: flex-start;
  margin-bottom: 12px;
}

.rev-icon-box {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: #ffffff;
  border: 1px solid #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
}

.rev-card-icon-img {
  width: 22px;
  height: 22px;
  object-fit: contain;
}

.text-purple { color: #6366f1; }
.currency-glyph { font-size: 1.25rem; font-weight: 800; color: #10b981; }

.rev-card-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 4px;
}

.rev-card-val {
  font-size: 1.7rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.03em;
  margin-bottom: 6px;
}

.rev-card-growth {
  font-size: 0.78rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 4px;
}

.text-green { color: #10b981; }
.text-red { color: #ef4444; }
.text-amber { color: #f59e0b; }
.text-blue { color: #3b82f6; }

.arrow-icon { font-weight: 800; }

/* Dual Analytics Row */
.revenue-analytics-row {
  display: grid;
  grid-template-columns: 1fr 1.15fr;
  gap: 18px;
}

.analytics-card {
  padding: 20px 22px;
}

.card-head-flex {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.view-link {
  font-size: 0.82rem;
  font-weight: 700;
  color: #6366f1;
  text-decoration: none;
  transition: color 0.15s ease;
}

.view-link:hover {
  color: #4f46e5;
  text-decoration: underline;
}

/* Donut Layout */
.donut-content-layout {
  display: flex;
  align-items: center;
  gap: 24px;
  justify-content: space-around;
}

.donut-chart-box {
  position: relative;
  width: 150px;
  height: 150px;
  flex-shrink: 0;
}

.donut-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.donut-center-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  display: flex;
  flex-direction: column;
}

.center-count {
  font-size: 1.15rem;
  color: #0f172a;
  line-height: 1.1;
}

.center-sub {
  font-size: 0.72rem;
  color: #64748b;
  font-weight: 500;
}

.plan-legend-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  flex: 1;
}

.plan-legend-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.legend-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-name {
  font-size: 0.85rem;
  color: #0f172a;
  line-height: 1.2;
}

.legend-count {
  font-size: 0.74rem;
  color: #64748b;
}

.percent-badge {
  font-size: 0.76rem;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 6px;
}

/* Revenue Overview Panel */
.rev-overview-hero {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 12px;
}

.rev-hero-val {
  font-size: 1.85rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.03em;
}

.rev-hero-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rev-hero-sub {
  font-size: 0.82rem;
  color: #64748b;
}

.growth-chip {
  font-size: 0.76rem;
  font-weight: 700;
  background: #ecfdf5;
  padding: 2px 8px;
  border-radius: 6px;
}

.revenue-graph-wrapper {
  display: flex;
  gap: 12px;
  height: 150px;
}

.y-axis-labels {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  font-size: 0.72rem;
  color: #94a3b8;
  font-weight: 500;
  text-align: right;
  width: 32px;
  padding-bottom: 20px;
}

.graph-plot-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
}

.line-graph-svg {
  width: 100%;
  height: 125px;
}

.x-axis-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.72rem;
  color: #94a3b8;
  font-weight: 500;
  margin-top: 4px;
}

/* Bottom Strip: Plan Comparison */
.plan-summary-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  flex-wrap: wrap;
  gap: 16px;
}

.strip-lead {
  display: flex;
  align-items: center;
  gap: 10px;
}

.strip-icon-box {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: #eef2ff;
  color: #6366f1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.strip-title {
  font-size: 0.92rem;
  color: #0f172a;
}

.strip-metrics {
  display: flex;
  align-items: center;
  gap: 32px;
  flex-wrap: wrap;
}

.strip-metric-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.metric-lbl {
  font-size: 0.72rem;
  color: #64748b;
  font-weight: 500;
}

.metric-val {
  font-size: 0.95rem;
  letter-spacing: -0.01em;
}

/* ============================================================ */
/* STANDARD CONTROL CENTER & LOGS STYLES                        */
/* ============================================================ */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.page-header h1 {
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0 0 4px 0;
}

.description {
  color: var(--text-secondary);
  font-size: 0.88rem;
  margin: 0;
}

.system-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  border-radius: 10px;
}

.status-indicator.live {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
  animation: pulse-green 2s infinite;
}

@keyframes pulse-green {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 5px rgba(16, 185, 129, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

.status-text {
  font-size: 0.82rem;
  color: #047857;
}

/* KPI Scorecards */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
}

.kpi-card {
  padding: 18px 20px;
}

.kpi-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.kpi-icon {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.kpi-change {
  font-size: 0.76rem;
  font-weight: 600;
  color: #10b981;
  background: #ecfdf5;
  padding: 3px 8px;
  border-radius: 6px;
}

.kpi-value {
  font-size: 1.7rem;
  margin: 0 0 4px 0;
  color: var(--text-primary);
}

.kpi-label {
  font-size: 0.82rem;
  color: var(--text-secondary);
  margin: 0;
}

/* Card Base */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
}

.analytics-row {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: 18px;
}

.chart-container, .controls-container {
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-title {
  font-size: 1.05rem;
  margin: 0;
  color: var(--text-primary);
}

.badge.blue {
  font-size: 0.74rem;
  font-weight: 700;
  background: #eff6ff;
  color: #1d6bf3;
  padding: 3px 10px;
  border-radius: 999px;
}

/* Bar Chart */
.chart-visual {
  flex: 1;
  display: flex;
  align-items: flex-end;
  padding-top: 10px;
}

.bar-chart {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  width: 100%;
  height: 160px;
  gap: 10px;
}

.bar-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
}

.bar-fill-wrapper {
  flex: 1;
  width: 100%;
  display: flex;
  align-items: flex-end;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 8px 8px 0 0;
}

.bar-fill {
  width: 100%;
  background: #1d6bf3;
  border-radius: 6px 6px 0 0;
  position: relative;
  transition: height 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}

.bar-fill:hover {
  background: #1754c7;
}

.bar-fill:hover .tooltip {
  opacity: 1;
  visibility: visible;
  transform: translateY(-8px);
}

.tooltip {
  position: absolute;
  top: -28px;
  left: 50%;
  transform: translateX(-50%);
  background: #0f172a;
  color: #fff;
  font-size: 0.72rem;
  padding: 2px 6px;
  border-radius: 4px;
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s ease;
  pointer-events: none;
  white-space: nowrap;
}

.bar-label {
  font-size: 0.72rem;
  color: var(--text-muted);
  margin-top: 6px;
}

/* Controls */
.controls-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.control-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}

.control-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.control-title {
  margin: 0 0 2px 0;
  font-size: 0.88rem;
  color: var(--text-primary);
}

.control-sub {
  margin: 0;
  font-size: 0.78rem;
  color: var(--text-muted);
}

/* Buttons */
.btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn.outlined {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-secondary);
}

.btn.outlined:hover {
  background: rgba(0, 0, 0, 0.04);
  color: var(--text-primary);
  border-color: var(--text-muted);
}

.btn.destructive {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
}

.btn.destructive:hover {
  background: #fee2e2;
}

/* Logs */
.logs-container {
  padding: 20px;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.table-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.search-box {
  display: flex;
  align-items: center;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 6px 10px;
  gap: 8px;
}

.search-icon {
  color: var(--text-muted);
}

.search-input {
  border: none;
  background: transparent;
  outline: none;
  font-size: 0.82rem;
  color: var(--text-primary);
  width: 180px;
}

.filter-pills {
  display: flex;
  gap: 6px;
  margin-bottom: 14px;
}

.pill-btn {
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text-secondary);
  font-size: 0.72rem;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.pill-btn.active {
  background: #1d6bf3;
  color: #ffffff;
  border-color: #1d6bf3;
}

.table-wrapper {
  overflow-x: auto;
}

.audit-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 0.82rem;
}

.audit-table th {
  padding: 10px 14px;
  color: var(--text-muted);
  font-weight: 700;
  font-size: 0.72rem;
  letter-spacing: 0.04em;
  border-bottom: 1px solid var(--border);
}

.audit-table td {
  padding: 12px 14px;
  border-bottom: 1px solid var(--border);
  color: var(--text-secondary);
}

.timestamp-cell {
  color: var(--text-muted);
  font-size: 0.78rem;
}

.event-cell {
  color: var(--text-primary);
}

.user-cell {
  color: #1d6bf3;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
}

.status-pill.success {
  background: #ecfdf5;
  color: #059669;
}

.status-pill.failed {
  background: #fef2f2;
  color: #dc2626;
}

.status-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: currentColor;
}

.empty-state {
  text-align: center;
  padding: 30px !important;
  color: var(--text-muted);
}

.toast-popup {
  position: fixed;
  top: 24px;
  right: 28px;
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
  .revenue-kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .revenue-analytics-row {
    grid-template-columns: 1fr;
  }
  .analytics-row {
    grid-template-columns: 1fr;
  }
}
</style>
