<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
const microscopeSrc = ref(`/assets/magnifying-glass-fingerprint.gif?t=${Date.now()}`)
import IconBase from '../components/dashboard/IconBase.vue'
import { patientData, mlPredictionResults, predictionModelResults, isAnalyzed } from '../store/appState'

const patientSidebarData = computed(() => {
  const risk = mlPredictionResults.value?.risk_scores || { diabetes: 0.5, hypertension: 0.5, heart_disease: 0.5, asthma: 0.5 }
  const avgRisk = Object.values(risk).reduce((a, b) => a + b, 0) / Object.values(risk).length
  return {
    equityScore: Math.round((1 - avgRisk) * 100),
    equityLevel: avgRisk > 0.7 ? 'Critical' : (avgRisk > 0.5 ? 'High Risk' : (avgRisk > 0.3 ? 'Moderate' : 'Low Risk')),
  }
})

const diseaseMeta = {
  diabetes: {
    name: 'Diabetes',
    iconColor: '#3b82f6',
    bgColor: '#eff6ff',
    barColor: '#3b82f6',
    iconSvg: `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22a7 7 0 0 0 7-7c0-4.3-7-11-7-11S5 10.7 5 15a7 7 0 0 0 7 7z"/></svg>`
  },
  hypertension: {
    name: 'Hypertension',
    iconColor: '#10b981',
    bgColor: '#ecfdf5',
    barColor: '#10b981',
    iconSvg: `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>`
  },
  heart_disease: {
    name: 'Heart Disease',
    iconColor: '#f97316',
    bgColor: '#fff7ed',
    barColor: '#f97316',
    iconSvg: `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>`
  },
  asthma: {
    name: 'Asthma',
    iconColor: '#a855f7',
    bgColor: '#faf5ff',
    barColor: '#a855f7',
    iconSvg: `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3c-1.5 0-3 1-3 3v8c0 2.2 1.8 4 4 4h1a3 3 0 0 0 3-3V6c0-1.7-1.3-3-3-3H6zM18 3c1.5 0 3 1 3 3v8c0 2.2-1.8 4-4 4h-1a3 3 0 0 1-3-3V6c0-1.7 1.3-3 3-3h3z"/><path d="M10 6h4M12 6v14"/></svg>`
  }
}

const diseaseList = computed(() => {
  if (!mlPredictionResults.value?.risk_scores) return []
  return Object.entries(mlPredictionResults.value.risk_scores).map(([key, val]) => {
    const meta = diseaseMeta[key] || { name: key.replace('_', ' '), iconColor: '#64748b', bgColor: '#f1f5f9', barColor: '#64748b', iconSvg: `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><path d="M12 8v8M8 12h8"/></svg>` }
    return {
      key,
      val: Math.round(val * 100),
      name: meta.name,
      iconColor: meta.iconColor,
      bgColor: meta.bgColor,
      barColor: meta.barColor,
      iconSvg: meta.iconSvg
    }
  })
})

const lastUpdatedDate = computed(() => {
  const options = { year: 'numeric', month: 'short', day: 'numeric' }
  const today = new Date()
  return today.toLocaleDateString('en-US', options)
})

// Local State
const selectedId = ref('cuyahoga')
const activeTrendFilter = ref('all') // 'all', 'hosp', 'util', 'chronic', 'gap'
const activeGeoTab = ref('county') // 'county', 'zip', 'tract'
const activeCorrelationOutcome = ref('hosp') // 'hosp', 'util', 'chronic', 'gap'

const isTrendDropdownOpen = ref(false)
const isCorrelationDropdownOpen = ref(false)

const trendFilterLabel = computed(() => {
  switch (activeTrendFilter.value) {
    case 'all': return 'All Risks'
    case 'hosp': return 'Hospitalization'
    case 'util': return 'Preventable Utilization'
    case 'chronic': return 'Chronic Disease'
    case 'gap': return 'Care Gap'
    default: return 'All Risks'
  }
})

const correlationOutcomeLabel = computed(() => {
  switch (activeCorrelationOutcome.value) {
    case 'hosp': return 'Hospitalization Risk'
    case 'util': return 'Preventable Utilization'
    case 'chronic': return 'Chronic Disease Risk'
    case 'gap': return 'Care Gap Probability'
    default: return 'Hospitalization Risk'
  }
})

const closeDropdowns = (e) => {
  if (!e.target.closest('.filter-dropdown-wrapper')) {
    isTrendDropdownOpen.value = false
  }
  if (!e.target.closest('.correlation-dropdown-wrapper')) {
    isCorrelationDropdownOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', closeDropdowns)
})

onUnmounted(() => {
  document.removeEventListener('click', closeDropdowns)
})

// Form filters state
const filterPopulation = ref('All Members')
const filterAge = ref('All')
const filterGender = ref('All')
const filterSDOHRisk = ref('All')
const filterChronic = ref('All')

// Interactive Tooltip on Line Chart
const hoverX = ref(null)
const hoverData = ref(null)
const chartWidth = 480
const chartHeight = 160
const chartPadding = { top: 20, right: 20, bottom: 30, left: 30 }

// Shared metadata for all communities
const communitiesData = {
  cuyahoga: {
    name: 'Cuyahoga County, OH',
    state: 'Ohio',
    totalMembers: '2.48M',
    metrics: {
      hospRisk: { val: '24.8%', trend: '↑ 3.6% vs last 30 days', trendClass: 'green-text', sparkline: [18, 20, 19, 22, 21, 23, 24.8, 25, 26] },
      utilRisk: { val: '18.2%', trend: '↓ 1.8% vs last 30 days', trendClass: 'green-text', sparkline: [15, 16, 14, 17, 15, 16, 18.2, 17.5, 18] },
      chronicRisk: { val: '32.6%', trend: '↑ 4.2% vs last 30 days', trendClass: 'red-text', sparkline: [30, 28, 29, 31, 30, 32, 32.6, 33, 34] },
      gapProb: { val: '31.4%', trend: '↑ 2.9% vs last 30 days', trendClass: 'orange-text', sparkline: [25, 26, 24, 27, 26, 28, 31.4, 30, 29] },
      sdohImpact: { val: '0.68', trend: '↑ 0.07 vs last 30 days', trendClass: 'green-text', sparkline: [0.61, 0.63, 0.62, 0.65, 0.64, 0.66, 0.68, 0.67, 0.68] }
    },
    donut: {
      total: '2.48M',
      low: { val: '1.12M', pct: '45.2%' },
      mod: { val: '782K', pct: '31.5%' },
      high: { val: '412K', pct: '16.6%' },
      crit: { val: '164K', pct: '6.7%' },
      alertText: '16.6% of members are in High or Critical risk'
    },
    trends: [
      { date: 'Apr 1', hosp: 20, util: 15, chronic: 30, gap: 25 },
      { date: 'Apr 8', hosp: 22, util: 16, chronic: 28, gap: 26 },
      { date: 'Apr 15', hosp: 21, util: 14, chronic: 29, gap: 24 },
      { date: 'Apr 22', hosp: 23, util: 17, chronic: 31, gap: 27 },
      { date: 'Apr 29', hosp: 22, util: 15, chronic: 30, gap: 26 },
      { date: 'May 6', hosp: 24, util: 16, chronic: 32, gap: 28 },
      { date: 'May 13', hosp: 24.8, util: 18.2, chronic: 32.6, gap: 31.4 },
      { date: 'May 20', hosp: 25.0, util: 17.5, chronic: 33.0, gap: 30.0 },
      { date: 'May 27', hosp: 26.0, util: 18.0, chronic: 34.0, gap: 29.0 }
    ],
    geoCounty: [
      { name: 'Cuyahoga County, OH', val: 0.72, barClass: 'red-bar', members: '2.48M' },
      { name: 'Mahoning County, OH', val: 0.66, barClass: 'orange-bar', members: '312K' },
      { name: 'Summit County, OH', val: 0.63, barClass: 'orange-bar', members: '285K' },
      { name: 'Lorain County, OH', val: 0.61, barClass: 'orange-bar', members: '198K' },
      { name: 'Lake County, OH', val: 0.58, barClass: 'orange-bar', members: '184K' },
      { name: 'Stark County, OH', val: 0.56, barClass: 'orange-bar', members: '176K' },
      { name: 'Portage County, OH', val: 0.53, barClass: 'orange-bar', members: '146K' },
      { name: 'Medina County, OH', val: 0.52, barClass: 'orange-bar', members: '128K' },
      { name: 'Geauga County, OH', val: 0.50, barClass: 'green-bar', members: '96K' },
      { name: 'Trumbull County, OH', val: 0.48, barClass: 'green-bar', members: '92K' }
    ],
    geoZip: [
      { name: '44102 (Cleveland)', val: 0.88, barClass: 'red-bar', members: '48K' },
      { name: '44105 (Cleveland)', val: 0.84, barClass: 'red-bar', members: '42K' },
      { name: '44108 (East Cleveland)', val: 0.82, barClass: 'red-bar', members: '36K' },
      { name: '44104 (Cleveland)', val: 0.79, barClass: 'red-bar', members: '31K' },
      { name: '44113 (Cleveland)', val: 0.71, barClass: 'orange-bar', members: '28K' },
      { name: '44112 (East Cleveland)', val: 0.68, barClass: 'orange-bar', members: '25K' },
      { name: '44135 (Cleveland)', val: 0.63, barClass: 'orange-bar', members: '29K' },
      { name: '44109 (Cleveland)', val: 0.59, barClass: 'orange-bar', members: '34K' },
      { name: '44111 (Cleveland)', val: 0.49, barClass: 'green-bar', members: '41K' },
      { name: '44107 (Lakewood)', val: 0.42, barClass: 'green-bar', members: '52K' }
    ],
    geoTract: [
      { name: 'Tract 1011.01 (Cleveland)', val: 0.94, barClass: 'red-bar', members: '4.8K' },
      { name: 'Tract 1024.02 (Cleveland)', val: 0.91, barClass: 'red-bar', members: '3.9K' },
      { name: 'Tract 1109.00 (East Cleveland)', val: 0.88, barClass: 'red-bar', members: '5.2K' },
      { name: 'Tract 1056.00 (Cleveland)', val: 0.85, barClass: 'red-bar', members: '2.6K' },
      { name: 'Tract 1143.01 (Cleveland)', val: 0.78, barClass: 'red-bar', members: '4.1K' },
      { name: 'Tract 1072.00 (Cleveland)', val: 0.74, barClass: 'orange-bar', members: '3.5K' },
      { name: 'Tract 1098.02 (East Cleveland)', val: 0.69, barClass: 'orange-bar', members: '2.9K' },
      { name: 'Tract 1201.00 (Cleveland)', val: 0.65, barClass: 'orange-bar', members: '3.2K' },
      { name: 'Tract 1135.00 (Cleveland)', val: 0.55, barClass: 'orange-bar', members: '4.5K' },
      { name: 'Tract 1245.00 (Lakewood)', val: 0.41, barClass: 'green-bar', members: '5.1K' }
    ],
    radar: {
      social: 0.72,
      economic: 0.61,
      food: 0.67,
      healthcare: 0.55,
      environmentQuality: 0.59,
      neighborhoodBuilt: 0.64
    },
    explainability: [
      { name: 'Housing Instability', val: 0.82, barClass: 'indigo-bar' },
      { name: 'Food Insecurity', val: 0.74, barClass: 'indigo-bar' },
      { name: 'Transportation Barriers', val: 0.68, barClass: 'indigo-bar' },
      { name: 'Environmental Exposure', val: 0.52, barClass: 'indigo-bar' },
      { name: 'Healthcare Accessibility', val: 0.47, barClass: 'indigo-bar' }
    ],
    correlationDots: [
      { svi: 0.22, risk: 12, label: 'Tract 1342.02' },
      { svi: 0.35, risk: 18, label: 'Tract 1402.01' },
      { svi: 0.48, risk: 24, label: 'Tract 1083.00' },
      { svi: 0.55, risk: 21, label: 'Tract 1092.01' },
      { svi: 0.62, risk: 28, label: 'Tract 1114.02' },
      { svi: 0.68, risk: 32, label: 'Tract 1243.00' },
      { svi: 0.72, risk: 36, label: 'Tract 1056.00' },
      { svi: 0.78, risk: 34, label: 'Tract 1109.00' },
      { svi: 0.82, risk: 42, label: 'Tract 1024.02' },
      { svi: 0.88, risk: 45, label: 'Tract 1011.01' },
      { svi: 0.31, risk: 14, label: 'Tract 1255.00' },
      { svi: 0.42, risk: 19, label: 'Tract 1182.02' },
      { svi: 0.58, risk: 27, label: 'Tract 1098.02' },
      { svi: 0.65, risk: 29, label: 'Tract 1201.00' },
      { svi: 0.75, risk: 38, label: 'Tract 1143.01' },
      { svi: 0.85, risk: 41, label: 'Tract 1072.00' },
      { svi: 0.92, risk: 48, label: 'Tract 1135.00' }
    ]
  },
  wayne: {
    name: 'Wayne County, MI',
    state: 'Michigan',
    totalMembers: '1.79M',
    metrics: {
      hospRisk: { val: '29.4%', trend: '↑ 5.1% vs last 30 days', trendClass: 'red-text', sparkline: [22, 24, 23, 26, 25, 27, 29.4, 30, 31] },
      utilRisk: { val: '22.5%', trend: '↑ 2.4% vs last 30 days', trendClass: 'red-text', sparkline: [18, 19, 17, 20, 19, 21, 22.5, 22, 23] },
      chronicRisk: { val: '38.2%', trend: '↑ 3.8% vs last 30 days', trendClass: 'red-text', sparkline: [34, 32, 33, 36, 35, 37, 38.2, 39, 40] },
      gapProb: { val: '36.1%', trend: '↑ 1.2% vs last 30 days', trendClass: 'orange-text', sparkline: [30, 31, 29, 33, 32, 34, 36.1, 35, 34] },
      sdohImpact: { val: '0.78', trend: '↑ 0.09 vs last 30 days', trendClass: 'red-text', sparkline: [0.69, 0.71, 0.70, 0.74, 0.73, 0.75, 0.78, 0.77, 0.79] }
    },
    donut: {
      total: '1.79M',
      low: { val: '716K', pct: '40.0%' },
      mod: { val: '483K', pct: '27.0%' },
      high: { val: '394K', pct: '22.0%' },
      crit: { val: '197K', pct: '11.0%' },
      alertText: '33.0% of members are in High or Critical risk'
    },
    trends: [
      { date: 'Apr 1', hosp: 24, util: 18, chronic: 34, gap: 30 },
      { date: 'Apr 8', hosp: 25, util: 19, chronic: 35, gap: 31 },
      { date: 'Apr 15', hosp: 23, util: 17, chronic: 33, gap: 29 },
      { date: 'Apr 22', hosp: 26, util: 20, chronic: 36, gap: 33 },
      { date: 'Apr 29', hosp: 25, util: 19, chronic: 35, gap: 32 },
      { date: 'May 6', hosp: 27, util: 21, chronic: 37, gap: 34 },
      { date: 'May 13', hosp: 29.4, util: 22.5, chronic: 38.2, gap: 36.1 },
      { date: 'May 20', hosp: 30.0, util: 22.0, chronic: 39.0, gap: 35.0 },
      { date: 'May 27', hosp: 31.0, util: 23.0, chronic: 40.0, gap: 34.0 }
    ],
    geoCounty: [
      { name: 'Wayne County, MI', val: 0.81, barClass: 'red-bar', members: '1.79M' },
      { name: 'Genesee County, MI', val: 0.74, barClass: 'red-bar', members: '406K' },
      { name: 'Saginaw County, MI', val: 0.69, barClass: 'orange-bar', members: '190K' },
      { name: 'Muskegon County, MI', val: 0.65, barClass: 'orange-bar', members: '175K' },
      { name: 'Ingham County, MI', val: 0.61, barClass: 'orange-bar', members: '292K' },
      { name: 'Jackson County, MI', val: 0.59, barClass: 'orange-bar', members: '160K' },
      { name: 'Macomb County, MI', val: 0.54, barClass: 'orange-bar', members: '881K' },
      { name: 'Kent County, MI', val: 0.48, barClass: 'green-bar', members: '657K' },
      { name: 'Oakland County, MI', val: 0.41, barClass: 'green-bar', members: '1.27M' },
      { name: 'Washtenaw County, MI', val: 0.38, barClass: 'green-bar', members: '372K' }
    ],
    geoZip: [
      { name: '48201 (Detroit)', val: 0.95, barClass: 'red-bar', members: '15K' },
      { name: '48206 (Detroit)', val: 0.92, barClass: 'red-bar', members: '18K' },
      { name: '48208 (Detroit)', val: 0.89, barClass: 'red-bar', members: '12K' },
      { name: '48215 (Detroit)', val: 0.86, barClass: 'red-bar', members: '21K' },
      { name: '48226 (Detroit)', val: 0.78, barClass: 'red-bar', members: '8K' },
      { name: '48202 (Detroit)', val: 0.75, barClass: 'orange-bar', members: '24K' },
      { name: '48207 (Detroit)', val: 0.70, barClass: 'orange-bar', members: '22K' },
      { name: '48216 (Detroit)', val: 0.68, barClass: 'orange-bar', members: '11K' },
      { name: '48209 (Detroit)', val: 0.58, barClass: 'orange-bar', members: '33K' },
      { name: '48126 (Dearborn)', val: 0.46, barClass: 'green-bar', members: '48K' }
    ],
    geoTract: [
      { name: 'Tract 5122.00 (Detroit)', val: 0.98, barClass: 'red-bar', members: '2.5K' },
      { name: 'Tract 5136.00 (Detroit)', val: 0.95, barClass: 'red-bar', members: '3.1K' },
      { name: 'Tract 5208.00 (Detroit)', val: 0.91, barClass: 'red-bar', members: '1.8K' },
      { name: 'Tract 5155.02 (Detroit)', val: 0.89, barClass: 'red-bar', members: '4.2K' },
      { name: 'Tract 5243.00 (Detroit)', val: 0.84, barClass: 'red-bar', members: '2.9K' },
      { name: 'Tract 5312.00 (Detroit)', val: 0.79, barClass: 'red-bar', members: '3.6K' },
      { name: 'Tract 5082.01 (Detroit)', val: 0.74, barClass: 'orange-bar', members: '2.1K' },
      { name: 'Tract 5114.02 (Detroit)', val: 0.69, barClass: 'orange-bar', members: '4.8K' },
      { name: 'Tract 5422.00 (Dearborn)', val: 0.52, barClass: 'orange-bar', members: '3.3K' },
      { name: 'Tract 5445.00 (Dearborn)', val: 0.42, barClass: 'green-bar', members: '5.1K' }
    ],
    radar: {
      social: 0.84,
      economic: 0.55,
      food: 0.76,
      healthcare: 0.62,
      environmentQuality: 0.68,
      neighborhoodBuilt: 0.71
    },
    explainability: [
      { name: 'Food Insecurity', val: 0.88, barClass: 'indigo-bar' },
      { name: 'Housing Instability', val: 0.85, barClass: 'indigo-bar' },
      { name: 'Environmental Exposure', val: 0.76, barClass: 'indigo-bar' },
      { name: 'Economic Barriers', val: 0.74, barClass: 'indigo-bar' },
      { name: 'Healthcare Access Gaps', val: 0.62, barClass: 'indigo-bar' }
    ],
    correlationDots: [
      { svi: 0.42, risk: 20, label: 'Tract 5445.00' },
      { svi: 0.52, risk: 22, label: 'Tract 5422.00' },
      { svi: 0.69, risk: 31, label: 'Tract 5114.02' },
      { svi: 0.74, risk: 33, label: 'Tract 5082.01' },
      { svi: 0.79, risk: 38, label: 'Tract 5312.00' },
      { svi: 0.84, risk: 42, label: 'Tract 5243.00' },
      { svi: 0.89, risk: 46, label: 'Tract 5155.02' },
      { svi: 0.91, risk: 49, label: 'Tract 5208.00' },
      { svi: 0.95, risk: 51, label: 'Tract 5136.00' },
      { svi: 0.98, risk: 55, label: 'Tract 5122.00' },
      { svi: 0.65, risk: 28, label: 'Tract 5055.00' },
      { svi: 0.71, risk: 35, label: 'Tract 5012.01' },
      { svi: 0.76, risk: 37, label: 'Tract 5022.02' },
      { svi: 0.81, risk: 43, label: 'Tract 5099.00' },
      { svi: 0.88, risk: 47, label: 'Tract 5111.02' },
      { svi: 0.93, risk: 52, label: 'Tract 5164.00' }
    ]
  },
  marion: {
    name: 'Marion County, IN',
    state: 'Indiana',
    totalMembers: '967K',
    metrics: {
      hospRisk: { val: '21.2%', trend: '↓ 0.5% vs last 30 days', trendClass: 'green-text', sparkline: [22, 21, 23, 21, 22, 20, 21.2, 21.5, 21.2] },
      utilRisk: { val: '15.8%', trend: '↓ 1.2% vs last 30 days', trendClass: 'green-text', sparkline: [17, 16, 17, 15, 16, 14, 15.8, 15.5, 15.2] },
      chronicRisk: { val: '28.4%', trend: '↑ 1.1% vs last 30 days', trendClass: 'orange-text', sparkline: [27, 26, 28, 27, 29, 28, 28.4, 28.2, 28.5] },
      gapProb: { val: '25.9%', trend: '↑ 0.8% vs last 30 days', trendClass: 'orange-text', sparkline: [24, 25, 23, 26, 24, 25, 25.9, 25.4, 25.1] },
      sdohImpact: { val: '0.58', trend: '↓ 0.02 vs last 30 days', trendClass: 'green-text', sparkline: [0.60, 0.59, 0.61, 0.58, 0.59, 0.57, 0.58, 0.57, 0.56] }
    },
    donut: {
      total: '967K',
      low: { val: '493K', pct: '51.0%' },
      mod: { val: '271K', pct: '28.0%' },
      high: { val: '145K', pct: '15.0%' },
      crit: { val: '58K', pct: '6.0%' },
      alertText: '21.0% of members are in High or Critical risk'
    },
    trends: [
      { date: 'Apr 1', hosp: 22, util: 17, chronic: 27, gap: 24 },
      { date: 'Apr 8', hosp: 21, util: 16, chronic: 26, gap: 25 },
      { date: 'Apr 15', hosp: 23, util: 17, chronic: 28, gap: 23 },
      { date: 'Apr 22', hosp: 21, util: 15, chronic: 27, gap: 26 },
      { date: 'Apr 29', hosp: 22, util: 16, chronic: 29, gap: 24 },
      { date: 'May 6', hosp: 20, util: 14, chronic: 28, gap: 25 },
      { date: 'May 13', hosp: 21.2, util: 15.8, chronic: 28.4, gap: 25.9 },
      { date: 'May 20', hosp: 21.5, util: 15.5, chronic: 28.2, gap: 25.4 },
      { date: 'May 27', hosp: 21.2, util: 15.2, chronic: 28.5, gap: 25.1 }
    ],
    geoCounty: [
      { name: 'Marion County, IN', val: 0.64, barClass: 'orange-bar', members: '967K' },
      { name: 'Lake County, IN', val: 0.68, barClass: 'orange-bar', members: '485K' },
      { name: 'St. Joseph County, IN', val: 0.58, barClass: 'orange-bar', members: '272K' },
      { name: 'Allen County, IN', val: 0.54, barClass: 'orange-bar', members: '375K' },
      { name: 'Vanderburgh County, IN', val: 0.52, barClass: 'orange-bar', members: '180K' },
      { name: 'Madison County, IN', val: 0.49, barClass: 'green-bar', members: '129K' },
      { name: 'Vigo County, IN', val: 0.48, barClass: 'green-bar', members: '107K' },
      { name: 'Elkhart County, IN', val: 0.46, barClass: 'green-bar', members: '206K' },
      { name: 'Hamilton County, IN', val: 0.22, barClass: 'green-bar', members: '338K' },
      { name: 'Hendricks County, IN', val: 0.25, barClass: 'green-bar', members: '170K' }
    ],
    geoZip: [
      { name: '46201 (Indianapolis)', val: 0.79, barClass: 'red-bar', members: '18K' },
      { name: '46218 (Indianapolis)', val: 0.76, barClass: 'red-bar', members: '14K' },
      { name: '46203 (Indianapolis)', val: 0.69, barClass: 'orange-bar', members: '22K' },
      { name: '46222 (Indianapolis)', val: 0.68, barClass: 'orange-bar', members: '19K' },
      { name: '46205 (Indianapolis)', val: 0.61, barClass: 'orange-bar', members: '15K' },
      { name: '46208 (Indianapolis)', val: 0.58, barClass: 'orange-bar', members: '12K' },
      { name: '46224 (Indianapolis)', val: 0.54, barClass: 'orange-bar', members: '17K' },
      { name: '46202 (Indianapolis)', val: 0.48, barClass: 'green-bar', members: '11K' },
      { name: '46240 (Indianapolis)', val: 0.28, barClass: 'green-bar', members: '25K' },
      { name: '46250 (Indianapolis)', val: 0.24, barClass: 'green-bar', members: '20K' }
    ],
    geoTract: [
      { name: 'Tract 3542.00 (Indianapolis)', val: 0.82, barClass: 'red-bar', members: '2.1K' },
      { name: 'Tract 3556.00 (Indianapolis)', val: 0.78, barClass: 'red-bar', members: '1.9K' },
      { name: 'Tract 3512.00 (Indianapolis)', val: 0.72, barClass: 'orange-bar', members: '3.2K' },
      { name: 'Tract 3582.01 (Indianapolis)', val: 0.68, barClass: 'orange-bar', members: '2.5K' },
      { name: 'Tract 3505.00 (Indianapolis)', val: 0.64, barClass: 'orange-bar', members: '1.8K' },
      { name: 'Tract 3524.00 (Indianapolis)', val: 0.58, barClass: 'orange-bar', members: '2.7K' },
      { name: 'Tract 3599.00 (Indianapolis)', val: 0.54, barClass: 'orange-bar', members: '1.5K' },
      { name: 'Tract 3612.00 (Indianapolis)', val: 0.49, barClass: 'green-bar', members: '2.2K' },
      { name: 'Tract 3640.00 (Indianapolis)', val: 0.29, barClass: 'green-bar', members: '3.1K' },
      { name: 'Tract 3650.00 (Indianapolis)', val: 0.22, barClass: 'green-bar', members: '2.8K' }
    ],
    radar: {
      social: 0.64,
      economic: 0.52,
      food: 0.58,
      healthcare: 0.49,
      environmentQuality: 0.52,
      neighborhoodBuilt: 0.55
    },
    explainability: [
      { name: 'Food Insecurity', val: 0.72, barClass: 'indigo-bar' },
      { name: 'Transportation Gaps', val: 0.68, barClass: 'indigo-bar' },
      { name: 'Housing Instability', val: 0.64, barClass: 'indigo-bar' },
      { name: 'Healthcare Access Gaps', val: 0.52, barClass: 'indigo-bar' },
      { name: 'Air Quality Burden', val: 0.48, barClass: 'indigo-bar' }
    ],
    correlationDots: [
      { svi: 0.22, risk: 10, label: 'Tract 3650.00' },
      { svi: 0.29, risk: 13, label: 'Tract 3640.00' },
      { svi: 0.49, risk: 19, label: 'Tract 3612.00' },
      { svi: 0.54, risk: 20, label: 'Tract 3599.00' },
      { svi: 0.58, risk: 22, label: 'Tract 3524.00' },
      { svi: 0.64, risk: 25, label: 'Tract 3505.00' },
      { svi: 0.68, risk: 28, label: 'Tract 3582.01' },
      { svi: 0.72, risk: 31, label: 'Tract 3512.00' },
      { svi: 0.78, risk: 34, label: 'Tract 3556.00' },
      { svi: 0.82, risk: 37, label: 'Tract 3542.00' },
      { svi: 0.35, risk: 12, label: 'Tract 3012.02' },
      { svi: 0.48, risk: 18, label: 'Tract 3055.00' },
      { svi: 0.59, risk: 23, label: 'Tract 3088.01' },
      { svi: 0.69, risk: 29, label: 'Tract 3102.00' },
      { svi: 0.75, risk: 32, label: 'Tract 3122.02' }
    ]
  },
  franklin: {
    name: 'Franklin County, OH',
    state: 'Ohio',
    totalMembers: '1.32M',
    metrics: {
      hospRisk: { val: '19.4%', trend: '↓ 1.2% vs last 30 days', trendClass: 'green-text', sparkline: [21, 20, 22, 20, 21, 19, 19.4, 19.0, 18.5] },
      utilRisk: { val: '14.2%', trend: '↓ 2.1% vs last 30 days', trendClass: 'green-text', sparkline: [16, 15, 16, 14, 15, 13, 14.2, 13.8, 13.5] },
      chronicRisk: { val: '25.8%', trend: '↓ 0.9% vs last 30 days', trendClass: 'green-text', sparkline: [27, 26, 28, 26, 27, 25, 25.8, 25.2, 25.0] },
      gapProb: { val: '22.4%', trend: '↑ 0.5% vs last 30 days', trendClass: 'orange-text', sparkline: [21, 22, 21, 23, 22, 22, 22.4, 22.1, 22.0] },
      sdohImpact: { val: '0.52', trend: '↓ 0.04 vs last 30 days', trendClass: 'green-text', sparkline: [0.55, 0.54, 0.56, 0.53, 0.54, 0.52, 0.52, 0.51, 0.50] }
    },
    donut: {
      total: '1.32M',
      low: { val: '766K', pct: '58.0%' },
      mod: { val: '396K', pct: '30.0%' },
      high: { val: '119K', pct: '9.0%' },
      crit: { val: '39K', pct: '3.0%' },
      alertText: '12.0% of members are in High or Critical risk'
    },
    trends: [
      { date: 'Apr 1', hosp: 21, util: 16, chronic: 27, gap: 21 },
      { date: 'Apr 8', hosp: 20, util: 15, chronic: 26, gap: 22 },
      { date: 'Apr 15', hosp: 22, util: 16, chronic: 28, gap: 21 },
      { date: 'Apr 22', hosp: 20, util: 14, chronic: 26, gap: 23 },
      { date: 'Apr 29', hosp: 21, util: 15, chronic: 27, gap: 22 },
      { date: 'May 6', hosp: 19, util: 13, chronic: 25, gap: 22 },
      { date: 'May 13', hosp: 19.4, util: 14.2, chronic: 25.8, gap: 22.4 },
      { date: 'May 20', hosp: 19.0, util: 13.8, chronic: 25.2, gap: 22.1 },
      { date: 'May 27', hosp: 18.5, util: 13.5, chronic: 25.0, gap: 22.0 }
    ],
    geoCounty: [
      { name: 'Franklin County, OH', val: 0.52, barClass: 'orange-bar', members: '1.32M' },
      { name: 'Hamilton County, OH', val: 0.38, barClass: 'green-bar', members: '817K' },
      { name: 'Cuyahoga County, OH', val: 0.72, barClass: 'red-bar', members: '2.48M' },
      { name: 'Montgomery County, OH', val: 0.65, barClass: 'orange-bar', members: '531K' },
      { name: 'Lucas County, OH', val: 0.63, barClass: 'orange-bar', members: '428K' },
      { name: 'Summit County, OH', val: 0.60, barClass: 'orange-bar', members: '540K' },
      { name: 'Butler County, OH', val: 0.51, barClass: 'orange-bar', members: '383K' },
      { name: 'Lorain County, OH', val: 0.49, barClass: 'green-bar', members: '309K' },
      { name: 'Delaware County, OH', val: 0.21, barClass: 'green-bar', members: '209K' },
      { name: 'Warren County, OH', val: 0.24, barClass: 'green-bar', members: '242K' }
    ],
    geoZip: [
      { name: '43201 (Columbus)', val: 0.72, barClass: 'orange-bar', members: '18K' },
      { name: '43211 (Columbus)', val: 0.68, barClass: 'orange-bar', members: '12K' },
      { name: '43222 (Columbus)', val: 0.64, barClass: 'orange-bar', members: '14K' },
      { name: '43205 (Columbus)', val: 0.59, barClass: 'orange-bar', members: '10K' },
      { name: '43207 (Columbus)', val: 0.58, barClass: 'orange-bar', members: '16K' },
      { name: '43206 (Columbus)', val: 0.54, barClass: 'orange-bar', members: '13K' },
      { name: '43215 (Columbus)', val: 0.48, barClass: 'green-bar', members: '9K' },
      { name: '43202 (Columbus)', val: 0.38, barClass: 'green-bar', members: '15K' },
      { name: '43212 (Grandview Heights)', val: 0.25, barClass: 'green-bar', members: '11K' },
      { name: '43220 (Columbus)', val: 0.21, barClass: 'green-bar', members: '22K' }
    ],
    geoTract: [
      { name: 'Tract 0022.00 (Columbus)', val: 0.78, barClass: 'orange-bar', members: '2.1K' },
      { name: 'Tract 0015.01 (Columbus)', val: 0.74, barClass: 'orange-bar', members: '1.9K' },
      { name: 'Tract 0029.00 (Columbus)', val: 0.68, barClass: 'orange-bar', members: '1.4K' },
      { name: 'Tract 0038.00 (Columbus)', val: 0.64, barClass: 'orange-bar', members: '2.5K' },
      { name: 'Tract 0041.00 (Columbus)', val: 0.58, barClass: 'orange-bar', members: '1.8K' },
      { name: 'Tract 0005.00 (Columbus)', val: 0.52, barClass: 'orange-bar', members: '2.7K' },
      { name: 'Tract 0012.00 (Columbus)', val: 0.48, barClass: 'green-bar', members: '1.5K' },
      { name: 'Tract 0003.00 (Columbus)', val: 0.38, barClass: 'green-bar', members: '2.2K' },
      { name: 'Tract 0002.00 (Columbus)', val: 0.25, barClass: 'green-bar', members: '3.1K' },
      { name: 'Tract 0001.00 (Columbus)', val: 0.21, barClass: 'green-bar', members: '2.8K' }
    ],
    radar: {
      social: 0.52,
      economic: 0.48,
      food: 0.58,
      healthcare: 0.45,
      environmentQuality: 0.46,
      neighborhoodBuilt: 0.50
    },
    explainability: [
      { name: 'Housing Instability', val: 0.58, barClass: 'indigo-bar' },
      { name: 'Income Inequality', val: 0.52, barClass: 'indigo-bar' },
      { name: 'Food Desert Pockets', val: 0.48, barClass: 'indigo-bar' },
      { name: 'Air Quality Concerns', val: 0.42, barClass: 'indigo-bar' },
      { name: 'Transit Barriers', val: 0.35, barClass: 'indigo-bar' }
    ],
    correlationDots: [
      { svi: 0.21, risk: 8, label: 'Tract 0001.00' },
      { svi: 0.25, risk: 11, label: 'Tract 0002.00' },
      { svi: 0.38, risk: 14, label: 'Tract 0003.00' },
      { svi: 0.48, risk: 19, label: 'Tract 0012.00' },
      { svi: 0.52, risk: 20, label: 'Tract 0005.00' },
      { svi: 0.58, risk: 23, label: 'Tract 0001.00' },
      { svi: 0.64, risk: 26, label: 'Tract 0038.00' },
      { svi: 0.68, risk: 28, label: 'Tract 0029.00' },
      { svi: 0.74, risk: 32, label: 'Tract 0015.01' },
      { svi: 0.78, risk: 35, label: 'Tract 0022.00' },
      { svi: 0.32, risk: 10, label: 'Tract 0081.01' },
      { svi: 0.45, risk: 15, label: 'Tract 0092.00' },
      { svi: 0.55, risk: 21, label: 'Tract 0076.02' },
      { svi: 0.67, risk: 27, label: 'Tract 0084.00' },
      { svi: 0.71, risk: 30, label: 'Tract 0099.01' }
    ]
  }
}

const activeCommunity = computed(() => {
  if (isAnalyzed.value && predictionModelResults.value && mlPredictionResults.value) {
    const diabetesRisk = Math.round((mlPredictionResults.value.risk_scores?.diabetes || 0.5) * 100)
    const hypertensionRisk = Math.round((mlPredictionResults.value.risk_scores?.hypertension || 0.5) * 100)
    const heartDiseaseRisk = Math.round((mlPredictionResults.value.risk_scores?.heart_disease || 0.5) * 100)
    const asthmaRisk = Math.round((mlPredictionResults.value.risk_scores?.asthma || 0.5) * 100)
    const sviScoreVal = predictionModelResults.value.overall_risk_score

    const hospSpark = [heartDiseaseRisk - 4, heartDiseaseRisk - 2, heartDiseaseRisk - 3, heartDiseaseRisk - 1, heartDiseaseRisk]
    const utilSpark = [hypertensionRisk - 5, hypertensionRisk - 3, hypertensionRisk - 4, hypertensionRisk - 2, hypertensionRisk]
    const chronicSpark = [diabetesRisk - 3, diabetesRisk - 1, diabetesRisk - 2, diabetesRisk + 1, diabetesRisk]
    const gapSpark = [asthmaRisk - 2, asthmaRisk - 1, asthmaRisk - 3, asthmaRisk + 1, asthmaRisk]
    const sdohSpark = [sviScoreVal - 0.05, sviScoreVal - 0.03, sviScoreVal - 0.04, sviScoreVal - 0.01, sviScoreVal]

    const trends = [
      { date: 'Apr 1', hosp: heartDiseaseRisk - 5, util: hypertensionRisk - 4, chronic: diabetesRisk - 4, gap: asthmaRisk - 3 },
      { date: 'Apr 8', hosp: heartDiseaseRisk - 4, util: hypertensionRisk - 3, chronic: diabetesRisk - 2, gap: asthmaRisk - 1 },
      { date: 'Apr 15', hosp: heartDiseaseRisk - 3, util: hypertensionRisk - 4, chronic: diabetesRisk - 3, gap: asthmaRisk - 2 },
      { date: 'Apr 22', hosp: heartDiseaseRisk - 2, util: hypertensionRisk - 1, chronic: diabetesRisk - 1, gap: asthmaRisk },
      { date: 'Apr 29', hosp: heartDiseaseRisk - 2, util: hypertensionRisk - 2, chronic: diabetesRisk - 1, gap: asthmaRisk - 1 },
      { date: 'May 6', hosp: heartDiseaseRisk - 1, util: hypertensionRisk - 1, chronic: diabetesRisk, gap: asthmaRisk },
      { date: 'May 13', hosp: heartDiseaseRisk, util: hypertensionRisk, chronic: diabetesRisk, gap: asthmaRisk }
    ]

    const patientSDoH = predictionModelResults.value.scores
    const explainability = [
      { name: 'Healthcare Access Gap', val: patientSDoH.healthcare_access, barClass: 'indigo-bar' },
      { name: 'Food Insecurity', val: patientSDoH.food_security, barClass: 'indigo-bar' },
      { name: 'Social Context Barriers', val: patientSDoH.social_context, barClass: 'indigo-bar' },
      { name: 'Neighborhood & Built Env', val: patientSDoH.neighborhood_environment, barClass: 'indigo-bar' },
      { name: 'Economic Instability', val: patientSDoH.economic_stability || 0.45, barClass: 'indigo-bar' }
    ].sort((a, b) => b.val - a.val)

    return {
      name: patientData.value.name || 'Active Patient',
      state: `${predictionModelResults.value.city}, ${predictionModelResults.value.state}`,
      totalMembers: '1 (Individual)',
      metrics: {
        hospRisk: { val: `${heartDiseaseRisk}%`, trend: 'Patient Heart Disease risk', trendClass: heartDiseaseRisk > 50 ? 'red-text' : 'green-text', sparkline: hospSpark },
        utilRisk: { val: `${hypertensionRisk}%`, trend: 'Patient Hypertension risk', trendClass: hypertensionRisk > 50 ? 'red-text' : 'green-text', sparkline: utilSpark },
        chronicRisk: { val: `${diabetesRisk}%`, trend: 'Patient Diabetes risk', trendClass: diabetesRisk > 50 ? 'red-text' : 'green-text', sparkline: chronicSpark },
        gapProb: { val: `${asthmaRisk}%`, trend: 'Patient Asthma risk', trendClass: asthmaRisk > 50 ? 'red-text' : 'green-text', sparkline: gapSpark },
        sdohImpact: { val: sviScoreVal.toFixed(2), trend: 'Estimated location SVI index', trendClass: sviScoreVal > 0.5 ? 'red-text' : 'green-text', sparkline: sdohSpark }
      },
      donut: {
        total: '1',
        low: { val: heartDiseaseRisk <= 35 ? '1' : '0', pct: heartDiseaseRisk <= 35 ? '100%' : '0%' },
        mod: { val: (heartDiseaseRisk > 35 && heartDiseaseRisk <= 55) ? '1' : '0', pct: (heartDiseaseRisk > 35 && heartDiseaseRisk <= 55) ? '100%' : '0%' },
        high: { val: (heartDiseaseRisk > 55 && heartDiseaseRisk <= 75) ? '1' : '0', pct: (heartDiseaseRisk > 55 && heartDiseaseRisk <= 75) ? '100%' : '0%' },
        crit: { val: heartDiseaseRisk > 75 ? '1' : '0', pct: heartDiseaseRisk > 75 ? '100%' : '0%' },
        alertText: `Overall Patient Risk Level: ${sviScoreVal > 0.7 ? 'Critical' : (sviScoreVal > 0.5 ? 'High' : 'Moderate')}`
      },
      trends,
      geoCounty: [
        { name: 'County Healthcare Access Gap', val: patientSDoH.healthcare_access, barClass: patientSDoH.healthcare_access > 0.6 ? 'red-bar' : (patientSDoH.healthcare_access > 0.4 ? 'orange-bar' : 'green-bar'), members: patientSDoH.healthcare_access > 0.6 ? 'Severe Barrier' : 'Moderate' },
        { name: 'County Social Context Index', val: patientSDoH.social_context, barClass: patientSDoH.social_context > 0.6 ? 'red-bar' : (patientSDoH.social_context > 0.4 ? 'orange-bar' : 'green-bar'), members: patientSDoH.social_context > 0.6 ? 'High Vulnerability' : 'Moderate' },
        { name: 'County Food Insecurity Level', val: patientSDoH.food_security, barClass: patientSDoH.food_security > 0.6 ? 'red-bar' : (patientSDoH.food_security > 0.4 ? 'orange-bar' : 'green-bar'), members: patientSDoH.food_security > 0.6 ? 'Severe Insecurity' : 'Moderate' },
        { name: 'County Neighborhood & Air Quality', val: patientSDoH.neighborhood_environment, barClass: patientSDoH.neighborhood_environment > 0.6 ? 'red-bar' : (patientSDoH.neighborhood_environment > 0.4 ? 'orange-bar' : 'green-bar'), members: patientSDoH.neighborhood_environment > 0.6 ? 'High Burden' : 'Moderate' },
        { name: 'County Economic Instability Index', val: patientSDoH.economic_stability || 0.45, barClass: (patientSDoH.economic_stability || 0.45) > 0.6 ? 'red-bar' : ((patientSDoH.economic_stability || 0.45) > 0.4 ? 'orange-bar' : 'green-bar'), members: (patientSDoH.economic_stability || 0.45) > 0.6 ? 'Critical' : 'Moderate' }
      ],
      geoZip: [
        { name: 'ZIP Code Primary Care Access', val: patientSDoH.healthcare_access * 0.95, barClass: patientSDoH.healthcare_access > 0.6 ? 'red-bar' : 'orange-bar', members: 'Limited Access' },
        { name: 'ZIP Code Food Availability', val: patientSDoH.food_security * 1.05, barClass: patientSDoH.food_security * 1.05 > 0.6 ? 'red-bar' : 'orange-bar', members: 'Food Desert' },
        { name: 'ZIP Code Walkability Index', val: Math.max(0.1, 1 - patientSDoH.neighborhood_environment), barClass: patientSDoH.neighborhood_environment > 0.5 ? 'orange-bar' : 'green-bar', members: 'Moderate' }
      ],
      geoTract: [
        { name: 'Tract Housing Burden Factor', val: patientSDoH.social_context * 1.1, barClass: patientSDoH.social_context * 1.1 > 0.6 ? 'red-bar' : 'orange-bar', members: 'Severe Burden' },
        { name: 'Tract Median Income Indicator', val: patientSDoH.economic_stability || 0.45, barClass: (patientSDoH.economic_stability || 0.45) > 0.5 ? 'red-bar' : 'orange-bar', members: 'Low Income' }
      ],
      radar: {
        social: patientSDoH.social_context,
        economic: patientSDoH.economic_stability || 0.45,
        food: patientSDoH.food_security,
        healthcare: patientSDoH.healthcare_access,
        environmentQuality: patientSDoH.neighborhood_environment,
        neighborhoodBuilt: patientSDoH.neighborhood_environment
      },
      explainability,
      correlationDots: [
        { svi: sviScoreVal, risk: heartDiseaseRisk, label: `${patientData.value.name} (Active Patient)` },
        { svi: 0.22, risk: 12, label: 'Tract 1342.02' },
        { svi: 0.35, risk: 18, label: 'Tract 1402.01' },
        { svi: 0.48, risk: 24, label: 'Tract 1083.00' },
        { svi: 0.62, risk: 28, label: 'Tract 1114.02' },
        { svi: 0.72, risk: 36, label: 'Tract 1056.00' },
        { svi: 0.82, risk: 42, label: 'Tract 1024.02' }
      ]
    }
  }
  return communitiesData[selectedId.value]
})

// Sparkline helper
function getSparklinePoints(arr, width = 80, height = 30) {
  const min = Math.min(...arr)
  const max = Math.max(...arr)
  const range = max - min || 1
  return arr.map((val, idx) => {
    const x = (idx / (arr.length - 1)) * width
    const y = height - ((val - min) / range) * (height - 4) - 2
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
}

// Line Chart calculations (Trends Over Time)
const chartDataPoints = computed(() => activeCommunity.value.trends)
const chartXCoords = computed(() => {
  const gap = (chartWidth - chartPadding.left - chartPadding.right) / (chartDataPoints.value.length - 1)
  return chartDataPoints.value.map((_, i) => chartPadding.left + i * gap)
})

function getLinePath(key) {
  const coords = chartXCoords.value
  const points = chartDataPoints.value.map((dp, i) => {
    const x = coords[i]
    // Map value (0% to 50%) to chartHeight
    const yVal = dp[key]
    const y = chartHeight - chartPadding.bottom - (yVal / 50) * (chartHeight - chartPadding.top - chartPadding.bottom)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })
  return `M ${points.join(' L ')}`
}

function handleLineMouseMove(e) {
  const rect = e.currentTarget.getBoundingClientRect()
  const mouseX = e.clientX - rect.left
  const clientWidth = rect.width
  const scaleX = chartWidth / clientWidth
  const actualX = mouseX * scaleX

  const leftBound = chartPadding.left
  const rightBound = chartWidth - chartPadding.right
  if (actualX < leftBound || actualX > rightBound) {
    hoverX.value = null
    hoverData.value = null
    return
  }

  // Find nearest coordinate
  const coords = chartXCoords.value
  let nearestIdx = 0
  let minDist = Infinity
  coords.forEach((coord, i) => {
    const dist = Math.abs(coord - actualX)
    if (dist < minDist) {
      minDist = dist
      nearestIdx = i
    }
  })

  hoverX.value = coords[nearestIdx]
  hoverData.value = chartDataPoints.value[nearestIdx]
}

function handleLineMouseLeave() {
  hoverX.value = null
  hoverData.value = null
}

// Donut Chart calculations
const donutSlices = computed(() => {
  const d = activeCommunity.value.donut
  const vals = [
    { key: 'low', val: parseFloat(d.low.pct), color: '#10b981' },
    { key: 'mod', val: parseFloat(d.mod.pct), color: '#f59e0b' },
    { key: 'high', val: parseFloat(d.high.pct), color: '#f97316' },
    { key: 'crit', val: parseFloat(d.crit.pct), color: '#ef4444' }
  ]

  let accumulatedPct = 0
  return vals.map(item => {
    const dashArray = `${item.val} ${100 - item.val}`
    // Circle offset starts at -25 (12 o'clock)
    // Positive dashoffset rotates clockwise
    const offset = 100 - accumulatedPct + 25
    accumulatedPct += item.val
    return {
      ...item,
      dashArray,
      dashOffset: offset
    }
  })
})

// Geographic area list based on selected tab
const geoList = computed(() => {
  if (activeGeoTab.value === 'county') return activeCommunity.value.geoCounty
  if (activeGeoTab.value === 'zip') return activeCommunity.value.geoZip
  return activeCommunity.value.geoTract
})

// Radar/Spider web points calculations
const radarPoints = computed(() => {
  const r = activeCommunity.value.radar
  const center = 70
  const radius = 50
  // Order of axes: Social, Economic, Food, Healthcare, EnvQuality, NeighborhoodBuilt
  const keys = ['social', 'economic', 'food', 'healthcare', 'environmentQuality', 'neighborhoodBuilt']
  const angles = [0, 60, 120, 180, 240, 300] // 6-axis layout

  const points = keys.map((key, i) => {
    const val = r[key]
    const angleRad = (angles[i] - 90) * (Math.PI / 180)
    const x = center + radius * val * Math.cos(angleRad)
    const y = center + radius * val * Math.sin(angleRad)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })

  return points.join(' ')
})

function getRadarWebPoints(scale) {
  const center = 70
  const radius = 50 * scale
  const angles = [0, 60, 120, 180, 240, 300]
  const points = angles.map(angle => {
    const angleRad = (angle - 90) * (Math.PI / 180)
    const x = center + radius * Math.cos(angleRad)
    const y = center + radius * Math.sin(angleRad)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })
  return points.join(' ')
}

function getRadarLabelCoords(idx, label) {
  const center = 70
  const radius = 58
  const angles = [0, 60, 120, 180, 240, 300]
  const angleRad = (angles[idx] - 90) * (Math.PI / 180)
  const x = center + radius * Math.cos(angleRad)
  const y = center + radius * Math.sin(angleRad)

  // Align text based on location
  let textAnchor = 'middle'
  if (angles[idx] > 0 && angles[idx] < 180) textAnchor = 'start'
  if (angles[idx] > 180 && angles[idx] < 360) textAnchor = 'end'

  return { x, y, textAnchor }
}

// Scatter plot hover state
const hoverDot = ref(null)

// Sync filterLocation selection to selectedId
function handleLocationFilterChange(e) {
  const val = e.target.value
  if (val.includes('Cuyahoga')) selectedId.value = 'cuyahoga'
  else if (val.includes('Wayne')) selectedId.value = 'wayne'
  else if (val.includes('Marion')) selectedId.value = 'marion'
  else if (val.includes('Franklin')) selectedId.value = 'franklin'
}
</script>

<template>
  <div class="predictive-analytics-page">
    <!-- Top Main Scroll Container -->
    <div class="scroll-container">
      <div class="content-body">
        
        <!-- Page Header -->
        <header class="page-header">
          <div>
            <h1>Predictive Analytics</h1>
            <p class="description">AI-powered predictions that help anticipate risks and prioritize actions.</p>
          </div>
        </header>

        <!-- Active Patient Predictive Insights -->
        <!-- Active Patient Predictive Insights -->
        <section v-if="isAnalyzed" class="premium-patient-panel">
          
          <!-- Panel Header Row -->
          <div class="panel-header">
            <div class="panel-header-left">
              <div class="avatar-circle">
                <img :src="microscopeSrc" alt="AI Analysis" class="avatar-gif" />
              </div>
              <div class="header-texts">
                <h3>Patient Risk Profile: <span class="patient-name">{{ patientData.name }}</span></h3>
                <p>
                  Real-time clinical and geographic risk assessment powered by Random Forest and Gradient Boosted estimators.
                </p>
              </div>
            </div>
            
            <div class="panel-header-right">
              <span class="bmi-badge">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
                  <circle cx="12" cy="7" r="4" />
                </svg>
                BMI: {{ ((patientData.weight_kg) / ((patientData.height_cm / 100) * (patientData.height_cm / 100))).toFixed(1) }} ({{ patientData.height_cm }}cm / {{ patientData.weight_kg }}kg)
              </span>
            </div>
          </div>

          <!-- Main Layout Columns -->
          <div class="panel-cols-grid">
            
            <!-- Column 1: Patient Health Score -->
            <div class="panel-col col-health-score">
              <div class="col-header">
                <span class="col-badge purple">
                  <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
                </span>
                <span class="col-title">Patient Health Score</span>
              </div>
              
              <!-- Circular Progress Gauge -->
              <div class="radial-gauge-wrapper">
                <svg width="120" height="120" viewBox="0 0 36 36" class="premium-gauge">
                  <!-- Background Track -->
                  <path class="gauge-track" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#f1f5f9" stroke-width="2.5" />
                  <!-- Foreground Gradient Bar -->
                  <path class="gauge-bar" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="url(#healthScoreGrad)" stroke-width="2.5" :stroke-dasharray="patientSidebarData.equityScore + ', 100'" stroke-linecap="round" />
                  <defs>
                    <linearGradient id="healthScoreGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stop-color="#3b82f6" />
                      <stop offset="100%" stop-color="#a855f7" />
                    </linearGradient>
                  </defs>
                </svg>
                <div class="gauge-inner-text">
                  <span class="score-number">{{ patientSidebarData.equityScore }}</span>
                  <span class="score-total">/100</span>
                </div>
              </div>

              <!-- Risk Level Badge -->
              <div class="risk-badge-wrapper">
                <span v-if="patientSidebarData.equityLevel === 'Low Risk'" class="premium-risk-badge low-risk">
                  <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" class="badge-icon"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 11 2 2 4-4"/></svg>
                  Low Risk
                </span>
                <span v-else-if="patientSidebarData.equityLevel === 'Moderate'" class="premium-risk-badge moderate">
                  <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="badge-icon"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                  Moderate Risk
                </span>
                <span v-else class="premium-risk-badge high-risk">
                  <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="badge-icon"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                  {{ patientSidebarData.equityLevel }}
                </span>
              </div>

              <!-- Gap details -->
              <div class="score-gap-row">
                <span class="gap-title">Health Gap: <b>{{ 100 - patientSidebarData.equityScore }} pts</b></span>
                <span class="gap-sub">vs National Avg</span>
              </div>
              
              <!-- Bottom wave decoration -->
              <div class="col-wave-decor">
                <svg viewBox="0 0 120 28" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M0 15 C 30 28, 60 2, 120 15 L 120 28 L 0 28 Z" fill="#faf5ff" opacity="0.6"/>
                  <path d="M0 20 C 40 10, 80 25, 120 15 L 120 28 L 0 28 Z" fill="#f3e8ff" opacity="0.4"/>
                </svg>
              </div>
            </div>

            <!-- Column 2: Disease Risk Predictions -->
            <div class="panel-col col-disease-risks">
              <div class="col-header">
                <span class="col-badge green">
                  <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                </span>
                <span class="col-title">Clinical Disease Risk Probabilities</span>
              </div>

              <div class="disease-list" v-if="mlPredictionResults">
                <div v-for="item in diseaseList" :key="item.key" class="disease-item-row">
                  <div class="disease-icon-wrapper" :style="{ backgroundColor: item.bgColor }">
                    <span v-html="item.iconSvg"></span>
                  </div>
                  <div class="disease-info-block">
                    <div class="disease-name-row">
                      <span class="disease-name">{{ item.name }}</span>
                      <span class="disease-pct" :style="{ color: item.iconColor }">{{ item.val }}%</span>
                    </div>
                    <div class="disease-bar-track">
                      <div class="disease-bar-fill" :style="{ width: item.val + '%', backgroundColor: item.barColor }"></div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div class="col-footer-note">
                <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" style="color: #10b981; flex-shrink: 0;"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>
                <span>Probabilities indicate the estimated risk of developing the condition.</span>
              </div>
            </div>

            <!-- Column 3: Geocoded Location SDOH Risk -->
            <div class="panel-col col-location-barriers">
              <div class="col-header">
                <span class="col-badge blue">
                  <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                </span>
                <span class="col-title">Geocoded Location SDOH Barriers</span>
              </div>

              <div class="location-map-panel" v-if="predictionModelResults">
                <div class="location-text-details">
                  <span class="loc-label">Estimated Location</span>
                  <span class="loc-value">{{ predictionModelResults.city }}, {{ predictionModelResults.state }}</span>
                </div>
                <div class="map-bg-wrapper">
                  <img src="/assets/location-map.png" alt="Location Map" class="map-bg-img" />
                  <div class="map-bg-fade"></div>
                </div>
              </div>

              <div class="svi-score-row" v-if="predictionModelResults">
                <span class="svi-label">SVI Risk Score <span class="help-dot">?</span></span>
                <span class="svi-value" :class="predictionModelResults.overall_risk_category.toLowerCase()">
                  {{ predictionModelResults.overall_risk_score.toFixed(2) }} ({{ predictionModelResults.overall_risk_category }})
                </span>
              </div>

              <!-- 2x2 grid of SDOH scores -->
              <div class="sdoh-mini-grid" v-if="predictionModelResults">
                <!-- Healthcare Access -->
                <div class="sdoh-mini-card">
                  <div class="mini-card-icon blue">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></svg>
                  </div>
                  <div class="mini-card-text">
                    <span class="mini-lbl">Healthcare Access</span>
                    <span class="mini-val">{{ Math.round(predictionModelResults.scores.healthcare_access * 100) }}%</span>
                  </div>
                </div>

                <!-- Social Context -->
                <div class="sdoh-mini-card">
                  <div class="mini-card-icon purple">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                  </div>
                  <div class="mini-card-text">
                    <span class="mini-lbl">Social Context</span>
                    <span class="mini-val">{{ Math.round(predictionModelResults.scores.social_context * 100) }}%</span>
                  </div>
                </div>

                <!-- Food Security -->
                <div class="sdoh-mini-card">
                  <div class="mini-card-icon green">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2 M6 2v7 M9 2v7 M7 11v11"/></svg>
                  </div>
                  <div class="mini-card-text">
                    <span class="mini-lbl">Food Security</span>
                    <span class="mini-val">{{ Math.round(predictionModelResults.scores.food_security * 100) }}%</span>
                  </div>
                </div>

                <!-- Neighborhood Environment -->
                <div class="sdoh-mini-card">
                  <div class="mini-card-icon orange">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
                  </div>
                  <div class="mini-card-text">
                    <span class="mini-lbl">Neighborhood Env</span>
                    <span class="mini-val">{{ Math.round(predictionModelResults.scores.neighborhood_environment * 100) }}%</span>
                  </div>
                </div>
              </div>
            </div>
            
          </div>

          <!-- Bottom Footer Banner -->
          <div class="panel-footer-banner">
            <div class="footer-left">
              <span class="footer-icon-shield">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              </span>
              <span>AI-driven insights for proactive care and better outcomes.</span>
            </div>
            <div class="footer-right">
              <span class="footer-icon-cal">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
              </span>
              <span>Last updated: {{ lastUpdatedDate }} • 10:30 AM</span>
            </div>
          </div>

        </section>

        <!-- Predictive Cards Top Row -->
        <section class="predictive-cards-grid">
          <!-- Card 1: Hospitalization Risk -->
          <div class="card metric-risk-card">
            <div class="card-header-row">
              <span class="icon-circle blue"><IconBase name="pulse" :size="14" /></span>
              <p class="card-title">Predicted Hospitalization Risk</p>
            </div>
            <div class="card-value-row">
              <h2>{{ activeCommunity.metrics.hospRisk.val }}</h2>
              <span class="trend-lbl" :class="activeCommunity.metrics.hospRisk.trendClass">
                {{ activeCommunity.metrics.hospRisk.trend }}
              </span>
            </div>

          </div>

          <!-- Card 2: Preventable Utilization -->
          <div class="card metric-risk-card">
            <div class="card-header-row">
              <span class="icon-circle teal"><IconBase name="shield" :size="14" /></span>
              <p class="card-title">Preventable Utilization Risk</p>
            </div>
            <div class="card-value-row">
              <h2>{{ activeCommunity.metrics.utilRisk.val }}</h2>
              <span class="trend-lbl" :class="activeCommunity.metrics.utilRisk.trendClass">
                {{ activeCommunity.metrics.utilRisk.trend }}
              </span>
            </div>

          </div>

          <!-- Card 3: Chronic Disease Risk -->
          <div class="card metric-risk-card">
            <div class="card-header-row">
              <span class="icon-circle purple"><IconBase name="heart" :size="14" /></span>
              <p class="card-title">Chronic Disease Risk</p>
            </div>
            <div class="card-value-row">
              <h2>{{ activeCommunity.metrics.chronicRisk.val }}</h2>
              <span class="trend-lbl" :class="activeCommunity.metrics.chronicRisk.trendClass">
                {{ activeCommunity.metrics.chronicRisk.trend }}
              </span>
            </div>

          </div>

          <!-- Card 4: Core Gap Probability -->
          <div class="card metric-risk-card">
            <div class="card-header-row">
              <span class="icon-circle orange"><IconBase name="puzzle" :size="14" /></span>
              <p class="card-title">Core Gap Probability</p>
            </div>
            <div class="card-value-row">
              <h2>{{ activeCommunity.metrics.gapProb.val }}</h2>
              <span class="trend-lbl" :class="activeCommunity.metrics.gapProb.trendClass">
                {{ activeCommunity.metrics.gapProb.trend }}
              </span>
            </div>

          </div>

          <!-- Card 5: SDOH Impact Score -->
          <div class="card metric-risk-card">
            <div class="card-header-row">
              <span class="icon-circle green"><IconBase name="sparkle" :size="14" /></span>
              <p class="card-title">SDOH Impact Score</p>
            </div>
            <div class="card-value-row">
              <h2>{{ activeCommunity.metrics.sdohImpact.val }}</h2>
              <span class="trend-lbl font-semibold" :class="activeCommunity.metrics.sdohImpact.trendClass">
                {{ activeCommunity.metrics.sdohImpact.trend }}
              </span>
            </div>

          </div>
        </section>



        <!-- Main Responsive Layout Grid -->
        <div class="layout-grid-main">
          
          <!-- Central Column: Detailed Graphs & Geographies -->
          <div class="main-left-column">
            
            <!-- Row 1: Line Chart & Donut Chart -->
            <div class="trends-distribution-row">
              
              <!-- 1. Risk Trends Over Time -->
              <div class="card trends-time-card">
                <div class="card-head-actions">
                  <div>
                    <h4>Risk Trends Over Time <span class="info-tooltip-btn"><IconBase name="help" :size="11" /></span></h4>
                  </div>
                  
                  <div class="filter-dropdown-wrapper">
                    <button class="filter-dropdown-btn" @click.stop="isTrendDropdownOpen = !isTrendDropdownOpen">
                      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="filter-icon"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
                      <span>{{ trendFilterLabel }}</span>
                      <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="chevron-icon"><polyline points="6 9 12 15 18 9"/></svg>
                    </button>
                    
                    <transition name="dropdown-fade">
                      <div class="filter-dropdown-menu" v-if="isTrendDropdownOpen">
                        <button class="dropdown-item" :class="{ active: activeTrendFilter === 'all' }" @click="activeTrendFilter = 'all'; isTrendDropdownOpen = false">All Risks</button>
                        <button class="dropdown-item" :class="{ active: activeTrendFilter === 'hosp' }" @click="activeTrendFilter = 'hosp'; isTrendDropdownOpen = false">Hospitalization</button>
                        <button class="dropdown-item" :class="{ active: activeTrendFilter === 'util' }" @click="activeTrendFilter = 'util'; isTrendDropdownOpen = false">Preventable Utilization</button>
                        <button class="dropdown-item" :class="{ active: activeTrendFilter === 'chronic' }" @click="activeTrendFilter = 'chronic'; isTrendDropdownOpen = false">Chronic Disease</button>
                        <button class="dropdown-item" :class="{ active: activeTrendFilter === 'gap' }" @click="activeTrendFilter = 'gap'; isTrendDropdownOpen = false">Care Gap</button>
                      </div>
                    </transition>
                  </div>
                </div>

                <!-- Custom Interactive SVG Graph -->
                <div class="svg-graph-container" @mousemove="handleLineMouseMove" @mouseleave="handleLineMouseLeave">
                  <svg viewBox="0 0 480 160" width="100%" height="100%">
                    <!-- Grid Lines -->
                    <line x1="30" y1="20" x2="460" y2="20" stroke="#f1f5f9" stroke-dasharray="2 2" />
                    <line x1="30" y1="50" x2="460" y2="50" stroke="#f1f5f9" stroke-dasharray="2 2" />
                    <line x1="30" y1="80" x2="460" y2="80" stroke="#f1f5f9" stroke-dasharray="2 2" />
                    <line x1="30" y1="110" x2="460" y2="110" stroke="#f1f5f9" stroke-dasharray="2 2" />
                    <line x1="30" y1="130" x2="460" y2="130" stroke="#e2e8f0" stroke-width="1.2" />

                    <!-- Axis Labels -->
                    <text x="8" y="24" class="axis-text">40%</text>
                    <text x="8" y="54" class="axis-text">30%</text>
                    <text x="8" y="84" class="axis-text">20%</text>
                    <text x="8" y="114" class="axis-text">10%</text>
                    <text x="12" y="134" class="axis-text">0%</text>

                    <!-- Trend lines -->
                    <g v-if="activeTrendFilter === 'all' || activeTrendFilter === 'hosp'">
                      <path :d="getLinePath('hosp')" fill="none" stroke="#3b82f6" stroke-width="2.2" stroke-linecap="round" />
                    </g>
                    <g v-if="activeTrendFilter === 'all' || activeTrendFilter === 'util'">
                      <path :d="getLinePath('util')" fill="none" stroke="#10b981" stroke-width="2.2" stroke-linecap="round" />
                    </g>
                    <g v-if="activeTrendFilter === 'all' || activeTrendFilter === 'chronic'">
                      <path :d="getLinePath('chronic')" fill="none" stroke="#8b5cf6" stroke-width="2.2" stroke-linecap="round" />
                    </g>
                    <g v-if="activeTrendFilter === 'all' || activeTrendFilter === 'gap'">
                      <path :d="getLinePath('gap')" fill="none" stroke="#f59e0b" stroke-width="2.2" stroke-linecap="round" />
                    </g>

                    <!-- Vertical hover line tracking cursor -->
                    <line 
                      v-if="hoverX" 
                      :x1="hoverX" 
                      y1="10" 
                      :x2="hoverX" 
                      y2="130" 
                      stroke="#94a3b8" 
                      stroke-width="1.5" 
                      stroke-dasharray="3 3" 
                    />

                    <!-- Draw intersection dots on hover -->
                    <g v-if="hoverX && hoverData">
                      <circle v-if="activeTrendFilter === 'all' || activeTrendFilter === 'hosp'" :cx="hoverX" :cy="chartHeight - chartPadding.bottom - (hoverData.hosp / 50) * (chartHeight - chartPadding.top - chartPadding.bottom)" r="4" fill="#3b82f6" stroke="#ffffff" stroke-width="1.5" />
                      <circle v-if="activeTrendFilter === 'all' || activeTrendFilter === 'util'" :cx="hoverX" :cy="chartHeight - chartPadding.bottom - (hoverData.util / 50) * (chartHeight - chartPadding.top - chartPadding.bottom)" r="4" fill="#10b981" stroke="#ffffff" stroke-width="1.5" />
                      <circle v-if="activeTrendFilter === 'all' || activeTrendFilter === 'chronic'" :cx="hoverX" :cy="chartHeight - chartPadding.bottom - (hoverData.chronic / 50) * (chartHeight - chartPadding.top - chartPadding.bottom)" r="4" fill="#8b5cf6" stroke="#ffffff" stroke-width="1.5" />
                      <circle v-if="activeTrendFilter === 'all' || activeTrendFilter === 'gap'" :cx="hoverX" :cy="chartHeight - chartPadding.bottom - (hoverData.gap / 50) * (chartHeight - chartPadding.top - chartPadding.bottom)" r="4" fill="#f59e0b" stroke="#ffffff" stroke-width="1.5" />
                    </g>
                  </svg>

                  <!-- Custom Interactive Tooltip card floating overlay -->
                  <div 
                    v-if="hoverX && hoverData" 
                    class="line-hover-tooltip"
                    :style="{ left: (hoverX / 480 * 100) + '%' }"
                  >
                    <p class="tooltip-date font-bold">{{ hoverData.date }}, 2025</p>
                    <ul class="tooltip-values-list">
                      <li v-if="activeTrendFilter === 'all' || activeTrendFilter === 'hosp'">
                        <span class="dot blue"></span> Hosp. Risk: <span class="val font-bold">{{ hoverData.hosp }}%</span>
                      </li>
                      <li v-if="activeTrendFilter === 'all' || activeTrendFilter === 'util'">
                        <span class="dot green"></span> Util. Risk: <span class="val font-bold">{{ hoverData.util }}%</span>
                      </li>
                      <li v-if="activeTrendFilter === 'all' || activeTrendFilter === 'chronic'">
                        <span class="dot purple"></span> Chronic Risk: <span class="val font-bold">{{ hoverData.chronic }}%</span>
                      </li>
                      <li v-if="activeTrendFilter === 'all' || activeTrendFilter === 'gap'">
                        <span class="dot orange"></span> Care Gap: <span class="val font-bold">{{ hoverData.gap }}%</span>
                      </li>
                    </ul>
                  </div>
                </div>

                <!-- X Axis Months labels row -->
                <div class="xaxis-labels-row">
                  <span>Apr 1</span>
                  <span>Apr 8</span>
                  <span>Apr 15</span>
                  <span>Apr 22</span>
                  <span>Apr 29</span>
                  <span>May 6</span>
                  <span>May 13</span>
                  <span>May 20</span>
                  <span>May 27</span>
                </div>

                <!-- Legend Row -->
                <div class="legend-labels-row">
                  <span><span class="dot blue"></span> Hospitalization Risk</span>
                  <span><span class="dot green"></span> Preventable Utilization</span>
                  <span><span class="dot purple"></span> Chronic Disease Risk</span>
                  <span><span class="dot orange"></span> Care Gap Probability</span>
                </div>
              </div>

              <!-- 2. Population Distribution by Risk Level -->
              

            </div>

            <!-- Row 2: Geographic Risk list, Radar chart, Model Performance -->
            <div class="geographic-radar-row">
              
              <!-- 1. Risk by Geographic Area -->
              <div class="card geo-risk-card">
                <div class="card-head-actions border-b">
                  <h4>{{ isAnalyzed ? 'Local Location SDOH Breakdown' : 'Risk by Geographic Area' }} <span v-if="!isAnalyzed" class="light">(Top 10)</span> <span class="info-tooltip-btn"><IconBase name="help" :size="11" /></span></h4>
                  
                  <div class="geo-capsule-tabs">
                    <button :class="{ active: activeGeoTab === 'county' }" @click="activeGeoTab = 'county'">County</button>
                    <button :class="{ active: activeGeoTab === 'zip' }" @click="activeGeoTab = 'zip'">ZIP Code</button>
                    <button :class="{ active: activeGeoTab === 'tract' }" @click="activeGeoTab = 'tract'">Census Tract</button>
                  </div>
                </div>

                <div class="geo-table-container">
                  <table class="geo-custom-table">
                    <thead>
                      <tr>
                        <th class="text-left">{{ isAnalyzed ? 'SDOH Barrier Domain' : 'Name' }}</th>
                        <th class="text-center" style="width: 100px;">{{ isAnalyzed ? 'Vulnerability Score' : 'Predicted Risk' }}</th>
                        <th class="text-right" style="width: 100px;">{{ isAnalyzed ? 'Barrier Impact' : 'Members' }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(geo, i) in geoList" :key="i">
                        <td class="geo-name font-semibold">{{ geo.name }}</td>
                        <td class="geo-gauge-cell">
                          <span class="risk-val font-semibold">{{ geo.val.toFixed(2) }}</span>
                          <div class="bar-track">
                            <div class="bar-fill" :class="geo.barClass" :style="{ width: (geo.val * 100) + '%' }"></div>
                          </div>
                        </td>
                        <td class="geo-members text-right">{{ geo.members }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <!-- 2. Risk Drivers Breakdown Radar Chart -->
              <div class="card radar-drivers-card">
                <h4>Risk Drivers Breakdown</h4>
                <p class="subtitle">Contribution of SDOH domains to predicted risk</p>

                <!-- Custom SVG Hexagon Radar Chart -->
                <div class="radar-chart-container">
                  <svg viewBox="0 0 140 140" width="100%" height="100%">
                    <!-- Nested background grid hexagons -->
                    <polygon :points="getRadarWebPoints(1.0)" fill="none" stroke="#e2e8f0" stroke-width="0.8" />
                    <polygon :points="getRadarWebPoints(0.8)" fill="none" stroke="#e2e8f0" stroke-width="0.8" />
                    <polygon :points="getRadarWebPoints(0.6)" fill="none" stroke="#e2e8f0" stroke-width="0.8" stroke-dasharray="1 1" />
                    <polygon :points="getRadarWebPoints(0.4)" fill="none" stroke="#e2e8f0" stroke-width="0.8" />
                    <polygon :points="getRadarWebPoints(0.2)" fill="none" stroke="#e2e8f0" stroke-width="0.8" />

                    <!-- Axis lines -->
                    <!-- Order: Social, Economic, Food, Healthcare, EnvQuality, NeighborhoodBuilt -->
                    <line x1="70" y1="70" x2="70" y2="20" stroke="#cbd5e1" stroke-width="0.8" />
                    <line x1="70" y1="70" x2="113.3" y2="45" stroke="#cbd5e1" stroke-width="0.8" />
                    <line x1="70" y1="70" x2="113.3" y2="95" stroke="#cbd5e1" stroke-width="0.8" />
                    <line x1="70" y1="70" x2="70" y2="120" stroke="#cbd5e1" stroke-width="0.8" />
                    <line x1="70" y1="70" x2="26.7" y2="95" stroke="#cbd5e1" stroke-width="0.8" />
                    <line x1="70" y1="70" x2="26.7" y2="45" stroke="#cbd5e1" stroke-width="0.8" />

                    <!-- Plotted Data Polygon -->
                    <polygon 
                      :points="radarPoints" 
                      fill="rgba(59, 130, 246, 0.15)" 
                      stroke="#3b82f6" 
                      stroke-width="1.8" 
                    />

                    <!-- Web dots -->
                    <!-- We can loop and draw dots if needed, but keeping it clean like mockup -->

                    <!-- Labels positioning -->
                    <text :x="getRadarLabelCoords(0).x" :y="getRadarLabelCoords(0).y" :text-anchor="getRadarLabelCoords(0).textAnchor" class="radar-axis-text">Social Conditions ({{ activeCommunity.radar.social }})</text>
                    <text :x="getRadarLabelCoords(1).x" :y="getRadarLabelCoords(1).y" :text-anchor="getRadarLabelCoords(1).textAnchor" class="radar-axis-text">Economic Stability ({{ activeCommunity.radar.economic }})</text>
                    <text :x="getRadarLabelCoords(2).x" :y="getRadarLabelCoords(2).y" :text-anchor="getRadarLabelCoords(2).textAnchor" class="radar-axis-text">Food Access ({{ activeCommunity.radar.food }})</text>
                    <text :x="getRadarLabelCoords(3).x" :y="getRadarLabelCoords(3).y" :text-anchor="getRadarLabelCoords(3).textAnchor" class="radar-axis-text">Healthcare Access ({{ activeCommunity.radar.healthcare }})</text>
                    <text :x="getRadarLabelCoords(4).x" :y="getRadarLabelCoords(4).y" :text-anchor="getRadarLabelCoords(4).textAnchor" class="radar-axis-text">Env. Quality ({{ activeCommunity.radar.environmentQuality }})</text>
                    <text :x="getRadarLabelCoords(5).x" :y="getRadarLabelCoords(5).y" :text-anchor="getRadarLabelCoords(5).textAnchor" class="radar-axis-text">Neighborhood & Built ({{ activeCommunity.radar.neighborhoodBuilt }})</text>
                  </svg>
                </div>
              </div>

              <!-- 3. Model Performance metrics -->
              <div class="card model-performance-card">
                <div class="card-head-actions">
                  <h4>Model Performance <span class="info-tooltip-btn"><IconBase name="help" :size="11" /></span></h4>
                </div>
                <p class="subtitle">Time Period: Last 90 Days</p>

                <div class="performance-metrics-list">
                  <div class="perf-row">
                    <div class="row-left">
                      <span class="icon-indicator"><IconBase name="pulse" :size="13" /></span>
                      <span class="lbl">AUC (ROC)</span>
                    </div>
                    <div class="row-right">
                      <span class="val font-semibold">0.84</span>
                      <span class="badge excel">Excellent</span>
                    </div>
                  </div>
                  <div class="perf-row">
                    <div class="row-left">
                      <span class="icon-indicator"><IconBase name="target" :size="13" /></span>
                      <span class="lbl">Precision</span>
                    </div>
                    <div class="row-right">
                      <span class="val font-semibold">0.78</span>
                      <span class="badge good">Good</span>
                    </div>
                  </div>
                  <div class="perf-row">
                    <div class="row-left">
                      <span class="icon-indicator"><IconBase name="shield" :size="13" /></span>
                      <span class="lbl">Recall (Sensitivity)</span>
                    </div>
                    <div class="row-right">
                      <span class="val font-semibold">0.76</span>
                      <span class="badge good">Good</span>
                    </div>
                  </div>
                  <div class="perf-row">
                    <div class="row-left">
                      <span class="icon-indicator"><IconBase name="puzzle" :size="13" /></span>
                      <span class="lbl">F1 Score</span>
                    </div>
                    <div class="row-right">
                      <span class="val font-semibold">0.77</span>
                      <span class="badge good">Good</span>
                    </div>
                  </div>
                </div>
              </div>

            </div>

          </div>

          <!-- Right Column: AI Explainability, Scatter Plot Correlation & Actions -->
          <aside class="right-explain-rail">
            
            <!-- Card 1: Explainability Factors -->
            <div class="card explain-factors-card">
              <h4>Explainability</h4>
              <p class="subtitle">Top Factors Influencing Predicted Risk</p>

              <ul class="explain-bars-list">
                <li v-for="(item, i) in activeCommunity.explainability" :key="i">
                  <div class="factor-header-row">
                    <span class="index-num font-bold">{{ i + 1 }}</span>
                    <span class="lbl font-semibold">{{ item.name }}</span>
                    <span class="val font-bold">{{ item.val.toFixed(2) }}</span>
                    <span class="info-icon"><IconBase name="help" :size="11" /></span>
                  </div>
                  <div class="factor-bar-track">
                    <div class="bar-fill" :class="item.barClass" :style="{ width: (item.val * 100) + '%' }"></div>
                  </div>
                </li>
              </ul>
              
              <p class="impact-indicator-text">Impact score indicates the strength of influence</p>
            </div>

            <!-- Card 2: SDOH vs Health Outcome Correlation Scatter Plot -->
            <div class="card correlation-scatter-card">
              <div class="scatter-head-row">
                <h4>SDOH vs Health Outcome Correlation <span class="info-tooltip-btn"><IconBase name="help" :size="11" /></span></h4>
              </div>

              <div class="select-outcome-wrapper">
                <span class="axis-lbl">Y-Axis</span>
                <div class="correlation-dropdown-wrapper">
                  <button class="filter-dropdown-btn" @click.stop="isCorrelationDropdownOpen = !isCorrelationDropdownOpen">
                    <span>{{ correlationOutcomeLabel }}</span>
                    <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="chevron-icon"><polyline points="6 9 12 15 18 9"/></svg>
                  </button>
                  
                  <transition name="dropdown-fade">
                    <div class="filter-dropdown-menu left-align" v-if="isCorrelationDropdownOpen">
                      <button class="dropdown-item" :class="{ active: activeCorrelationOutcome === 'hosp' }" @click="activeCorrelationOutcome = 'hosp'; isCorrelationDropdownOpen = false">Hospitalization Risk</button>
                      <button class="dropdown-item" :class="{ active: activeCorrelationOutcome === 'util' }" @click="activeCorrelationOutcome = 'util'; isCorrelationDropdownOpen = false">Preventable Utilization</button>
                      <button class="dropdown-item" :class="{ active: activeCorrelationOutcome === 'chronic' }" @click="activeCorrelationOutcome = 'chronic'; isCorrelationDropdownOpen = false">Chronic Disease Risk</button>
                      <button class="dropdown-item" :class="{ active: activeCorrelationOutcome === 'gap' }" @click="activeCorrelationOutcome = 'gap'; isCorrelationDropdownOpen = false">Care Gap Probability</button>
                    </div>
                  </transition>
                </div>
              </div>

              <!-- Scatter Plot SVG Area -->
              <div class="scatter-plot-container">
                <span class="y-label">Hospitalization Risk (%)</span>
                
                <div class="scatter-svg-wrapper">
                  <svg viewBox="0 0 200 120" width="100%" height="100%">
                    <!-- Grid dashed lines -->
                    <line x1="20" y1="20" x2="190" y2="20" stroke="#f1f5f9" stroke-width="0.8" />
                    <line x1="20" y1="50" x2="190" y2="50" stroke="#f1f5f9" stroke-width="0.8" />
                    <line x1="20" y1="80" x2="190" y2="80" stroke="#f1f5f9" stroke-width="0.8" />
                    <line x1="20" y1="100" x2="190" y2="100" stroke="#cbd5e1" stroke-width="0.8" />
                    <line x1="20" y1="10" x2="20" y2="100" stroke="#cbd5e1" stroke-width="0.8" />

                    <!-- Scatter plot regression trend line -->
                    <line x1="20" y1="90" x2="190" y2="30" stroke="#3b82f6" stroke-width="1.5" stroke-dasharray="3 2" />

                    <!-- Scatter Dots -->
                    <circle 
                      v-for="(dot, idx) in activeCommunity.correlationDots" 
                      :key="idx"
                      :cx="20 + dot.svi * 170" 
                      :cy="100 - (dot.risk / 60) * 80" 
                      r="2.8" 
                      fill="#3b82f6" 
                      opacity="0.6" 
                      class="scatter-dot"
                      @mouseover="hoverDot = dot"
                      @mouseleave="hoverDot = null"
                    />

                    <!-- X-Axis Labels -->
                    <text x="20" y="112" class="scatter-axis-text" text-anchor="middle">0.00</text>
                    <text x="62.5" y="112" class="scatter-axis-text" text-anchor="middle">0.25</text>
                    <text x="105" y="112" class="scatter-axis-text" text-anchor="middle">0.50</text>
                    <text x="147.5" y="112" class="scatter-axis-text" text-anchor="middle">0.75</text>
                    <text x="190" y="112" class="scatter-axis-text" text-anchor="middle">1.00</text>

                    <!-- Y-Axis Labels -->
                    <text x="15" y="103" class="scatter-axis-text" text-anchor="end">0%</text>
                    <text x="15" y="83" class="scatter-axis-text" text-anchor="end">10%</text>
                    <text x="15" y="63" class="scatter-axis-text" text-anchor="end">20%</text>
                    <text x="15" y="43" class="scatter-axis-text" text-anchor="end">30%</text>
                    <text x="15" y="23" class="scatter-axis-text" text-anchor="end">40%</text>
                  </svg>

                  <!-- Floating Dot Tooltip -->
                  <div v-if="hoverDot" class="scatter-hover-tooltip">
                    <p class="font-bold">{{ hoverDot.label }}</p>
                    <p>SVI Index: <span class="font-semibold">{{ hoverDot.svi.toFixed(2) }}</span></p>
                    <p>Predicted Risk: <span class="font-semibold">{{ hoverDot.risk }}%</span></p>
                  </div>
                </div>

                <div class="x-label">Social Vulnerability Index (SVI)</div>
              </div>

              <!-- Scatter Statistics -->
              <div class="scatter-stats-row">
                <span class="r-val font-semibold">Correlation (r) = 0.63</span>
                <span class="relation font-semibold blue-text">Positive correlation</span>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>

    <!-- Sticky Bottom Footer Bar -->
    <footer class="predictive-footer">
      <div class="footer-left">
        <span class="icon-globe"><IconBase name="shield" :size="13" /></span>
        <p class="transparency-text">
          <strong>Model Transparency</strong>: Our models are trained on de-identified data and follow explainable AI principles. 
        </p>
      </div>
      
      <div class="footer-right">
        <span class="refreshed-text">Data refreshed: May 31, 2025</span>
        <span class="divider">|</span>
        <span class="privacy-lock"><IconBase name="shield" :size="12" /> Data privacy protected</span>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.predictive-analytics-page {
  background: #f8fafc;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.scroll-container {
  flex: 1;
  overflow-y: auto;
  min-width: 0;
}

.content-body {
  padding: 24px 32px 32px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Page Header */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-header h1 {
  margin: 0 0 4px;
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--text-primary);
}

.page-header .description {
  margin: 0;
  font-size: 0.86rem;
  color: var(--text-secondary);
}

.header-actions {
  display: flex;
  gap: 12px;
}

.btn {
  border-radius: var(--radius-md);
  font-size: 0.78rem;
  font-weight: 600;
  padding: 8px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.15s ease;
}

.btn.outlined {
  background: #ffffff;
  border: 1px solid var(--border);
  color: var(--text-primary);
}

.btn.outlined:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
}

.btn.primary {
  background: var(--brand);
  color: #ffffff;
}

.btn.primary:hover {
  background: var(--brand-dark);
}

/* General Card */
.card {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  padding: 16px;
}

/* Predictive Cards Row */
.predictive-cards-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}

.metric-risk-card {
  display: flex;
  flex-direction: column;
  padding: 14px;
  position: relative;
  overflow: hidden;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.metric-risk-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.card-header-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.icon-circle {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.icon-circle.blue { background: #eff6ff; color: #2563eb; }
.icon-circle.teal { background: #ecfdf5; color: #059669; }
.icon-circle.purple { background: #f5f3ff; color: #7c3aed; }
.icon-circle.orange { background: #fffbeb; color: #d97706; }
.icon-circle.green { background: #ecfdf5; color: #059669; }

.card-title {
  margin: 0;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--text-secondary);
  line-height: 1.25;
}

.card-value-row {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-bottom: 8px;
}

.card-value-row h2 {
  margin: 0;
  font-size: 1.45rem;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1.1;
}

.trend-lbl {
  font-size: 0.62rem;
  font-weight: 700;
}

.green-text { color: #059669; }
.red-text { color: #dc2626; }
.orange-text { color: #d97706; }

.sparkline-container {
  height: 30px;
  margin-top: auto;
}

.spark-svg {
  width: 100%;
  height: 100%;
}

/* Filters Row Bar */
.filters-row-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 10px 18px;
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
  flex: 1;
  min-width: 110px;
}

.filter-lbl {
  font-size: 0.62rem;
  font-weight: 700;
  color: var(--text-secondary);
  text-transform: uppercase;
}

.filter-select {
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 5px 8px;
  font-size: 0.76rem;
  font-weight: 600;
  color: var(--text-primary);
  background: #ffffff;
  outline: none;
  cursor: pointer;
}

.filters-more-btn {
  background: #ffffff;
  border: 1px solid var(--border);
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 0.74rem;
  font-weight: 700;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 6px;
  align-self: flex-end;
}

.filters-more-btn:hover {
  background: #f8fafc;
  color: var(--text-primary);
}

/* Layout Grid Main */
.layout-grid-main {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 20px;
}

.main-left-column {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 0;
}

.trends-distribution-row {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
}

.trends-time-card {
  padding: 18px;
  display: flex;
  flex-direction: column;
  position: relative;
}

.card-head-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.card-head-actions h4 {
  margin: 0;
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--text-primary);
  text-transform: uppercase;
  display: flex;
  align-items: center;
  gap: 6px;
}

.info-tooltip-btn {
  color: #94a3b8;
  cursor: pointer;
}

.filter-dropdown-wrapper {
  position: relative;
  display: inline-block;
}

.correlation-dropdown-wrapper {
  position: relative;
  display: inline-block;
}

.filter-dropdown-menu.left-align {
  left: 0;
  right: auto;
}

.filter-dropdown-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 0.72rem;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  white-space: nowrap;
}

.filter-dropdown-btn:hover {
  border-color: #94a3b8;
  background: #f8fafc;
}

.filter-icon,
.chevron-icon {
  color: #64748b;
  flex-shrink: 0;
}

.filter-dropdown-menu {
  position: absolute;
  right: 0;
  top: calc(100% + 6px);
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  z-index: 50;
  min-width: 180px;
  padding: 4px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.dropdown-item {
  border: none;
  background: transparent;
  text-align: left;
  padding: 8px 12px;
  font-size: 0.74rem;
  font-weight: 500;
  color: #475569;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.dropdown-item:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.dropdown-item.active {
  background: #eff6ff;
  color: #2563eb;
  font-weight: 600;
}

/* Dropdown Animation */
.dropdown-fade-enter-active,
.dropdown-fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.dropdown-fade-enter-from,
.dropdown-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.svg-graph-container {
  height: 160px;
  position: relative;
  cursor: crosshair;
}

.axis-text {
  font-size: 8px;
  fill: #94a3b8;
  font-weight: 600;
}

.xaxis-labels-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 16px 0 30px;
  border-top: 1px solid #f1f5f9;
  font-size: 8px;
  font-weight: 700;
  color: #94a3b8;
  margin-top: 4px;
}

.legend-labels-row {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 12px;
  padding-top: 8px;
  border-top: 1px solid #f1f5f9;
}

.legend-labels-row span {
  font-size: 0.68rem;
  font-weight: 600;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 4px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  display: inline-block;
}

.dot.blue { background: #3b82f6; }
.dot.green { background: #10b981; }
.dot.purple { background: #8b5cf6; }
.dot.orange { background: #f59e0b; }
.dot.yellow { background: #fbbf24; }
.dot.orange-red { background: #f97316; }
.dot.red { background: #ef4444; }

/* Tooltip Line Chart */
.line-hover-tooltip {
  position: absolute;
  top: 10px;
  transform: translateX(-50%);
  background: #1e293b;
  color: #ffffff;
  padding: 8px 10px;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  pointer-events: none;
  z-index: 10;
  min-width: 110px;
}

.tooltip-date {
  font-size: 0.64rem;
  margin: 0 0 4px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  padding-bottom: 2px;
}

.tooltip-values-list {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.tooltip-values-list li {
  font-size: 0.62rem;
  display: flex;
  align-items: center;
  gap: 4px;
}

.tooltip-values-list .val {
  margin-left: auto;
}

/* Donut Chart Distribution */
.distribution-donut-card {
  padding: 18px;
  display: flex;
  flex-direction: column;
}

.view-table-link {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--brand);
}

.donut-chart-wrapper {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-top: 10px;
  flex: 1;
}

.donut-svg-container {
  width: 90px;
  height: 90px;
  position: relative;
  flex-shrink: 0;
}

.donut-svg {
  transform: rotate(-90deg);
  width: 100%;
  height: 100%;
}

.donut-segment {
  transition: stroke-dasharray 0.3s ease, stroke-dashoffset 0.3s ease;
}

.donut-center-info {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.donut-center-info .total-val {
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--text-primary);
}

.donut-center-info .lbl {
  font-size: 0.58rem;
  color: var(--text-secondary);
  font-weight: 600;
}

.donut-details-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}

.details-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.68rem;
}

.item-left {
  display: flex;
  align-items: center;
  gap: 6px;
}

.details-item .val {
  color: var(--text-primary);
}

.details-item .pct {
  color: var(--text-secondary);
}

.donut-alert-bubble {
  background: #fff5f5;
  border: 1px solid #fee2e2;
  border-radius: 10px;
  padding: 8px 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 14px;
}

.donut-alert-bubble .alert-icon {
  color: #ef4444;
  display: flex;
}

.donut-alert-bubble .alert-msg {
  margin: 0;
  font-size: 0.68rem;
  font-weight: 700;
  color: #b91c1c;
}

/* Row 2: Geo Risk, Radar, Model Performance */
.geographic-radar-row {
  display: grid;
  grid-template-columns: 1.15fr 0.9fr 0.95fr;
  gap: 20px;
}

.geo-risk-card {
  padding: 16px;
  display: flex;
  flex-direction: column;
}

.card-head-actions.border-b {
  border-bottom: 1px solid var(--border);
  padding-bottom: 10px;
  margin-bottom: 10px;
}

.geo-capsule-tabs {
  display: flex;
  background: #f1f5f9;
  border-radius: 6px;
  padding: 2px;
}

.geo-capsule-tabs button {
  border: none;
  background: transparent;
  padding: 3.5px 8px;
  font-size: 0.64rem;
  font-weight: 700;
  color: var(--text-secondary);
  border-radius: 4px;
  cursor: pointer;
}

.geo-capsule-tabs button.active {
  background: #ffffff;
  color: var(--brand);
}

.geo-table-container {
  height: 200px;
  overflow-y: auto;
  flex: 1;
}

.geo-custom-table {
  width: 100%;
  border-collapse: collapse;
}

.geo-custom-table th {
  font-size: 0.64rem;
  font-weight: 700;
  color: var(--text-tertiary);
  text-transform: uppercase;
  padding-bottom: 6px;
}

.geo-custom-table td {
  padding: 6.5px 0;
  font-size: 0.7rem;
  border-bottom: 1px solid #f8fafc;
}

.geo-name {
  color: var(--text-primary);
  max-width: 14ch;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.geo-gauge-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.risk-val {
  width: 25px;
  font-size: 0.72rem;
  color: var(--text-primary);
}

.bar-track {
  flex: 1;
  height: 5px;
  background: #e2e8f0;
  border-radius: 99px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 99px;
}

.bar-fill.red-bar { background: #ef4444; }
.bar-fill.orange-bar { background: #f59e0b; }
.bar-fill.green-bar { background: #10b981; }

.geo-members {
  color: var(--text-secondary);
}

.view-map-link {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--brand);
  margin-top: 10px;
  border-top: 1px solid var(--border);
  padding-top: 8px;
}

/* Radar drivers breakdown */
.radar-drivers-card {
  padding: 16px;
  display: flex;
  flex-direction: column;
}

.radar-drivers-card .subtitle {
  margin: 0 0 10px;
  font-size: 0.68rem;
  color: var(--text-secondary);
}

.radar-chart-container {
  height: 180px;
  margin-bottom: auto;
  display: flex;
  align-items: center;
  justify-content: center;
}

.radar-axis-text {
  font-size: 4px;
  fill: #64748b;
  font-weight: 700;
}

.view-details-link {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--brand);
  margin-top: auto;
  border-top: 1px solid var(--border);
  padding-top: 8px;
}

/* Model Performance Card */
.model-performance-card {
  padding: 16px;
  display: flex;
  flex-direction: column;
}

.model-performance-card .subtitle {
  margin: 0 0 12px;
  font-size: 0.68rem;
  color: var(--text-secondary);
}

.performance-metrics-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
}

.perf-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #f8fafc;
  padding-bottom: 6px;
}

.row-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon-indicator {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #f1f5f9;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.perf-row .lbl {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.row-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.perf-row .val {
  font-size: 0.78rem;
  color: var(--text-primary);
}

.badge {
  font-size: 0.58rem;
  font-weight: 700;
  padding: 1.5px 6px;
  border-radius: 4px;
}

.badge.excel {
  background: #e7fbf3;
  color: #047857;
}

.badge.good {
  background: #eff6ff;
  color: #1d4ed8;
}

.view-performance-link {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--brand);
  margin-top: auto;
  border-top: 1px solid var(--border);
  padding-top: 8px;
}

/* Right Column Explain Rail */
.right-explain-rail {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.right-explain-rail h4 {
  margin: 0 0 4px;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-primary);
  text-transform: uppercase;
}

.right-explain-rail .subtitle {
  margin: 0 0 12px;
  font-size: 0.68rem;
  color: var(--text-secondary);
}

/* Explain factors */
.explain-factors-card {
  padding: 16px;
}

.explain-bars-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 12px;
}

.factor-header-row {
  display: flex;
  align-items: center;
  font-size: 0.7rem;
  margin-bottom: 4px;
}

.index-num {
  color: var(--text-tertiary);
  width: 14px;
}

.factor-header-row .lbl {
  color: var(--text-primary);
}

.factor-header-row .val {
  color: var(--brand);
  margin-left: auto;
  margin-right: 6px;
}

.factor-header-row .info-icon {
  color: #cbd5e1;
  cursor: pointer;
}

.factor-bar-track {
  height: 5px;
  background: #e2e8f0;
  border-radius: 99px;
  overflow: hidden;
}

.factor-bar-track .bar-fill.indigo-bar {
  background: #6366f1;
}

.impact-indicator-text {
  font-size: 0.64rem;
  color: var(--text-tertiary);
  margin: 0 0 8px;
}

.how-works-link {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--brand);
}

/* Correlation Scatter Plot */
.correlation-scatter-card {
  padding: 16px;
  position: relative;
}

.select-outcome-wrapper {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
}

.select-outcome-wrapper .axis-lbl {
  font-size: 0.64rem;
  font-weight: 700;
  color: var(--text-secondary);
  text-transform: uppercase;
}

.select-outcome {
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 4px 6px;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--text-primary);
  background: #ffffff;
  outline: none;
  cursor: pointer;
}

.scatter-plot-container {
  display: flex;
  flex-direction: column;
  position: relative;
}

.scatter-plot-container .y-label {
  font-size: 6px;
  font-weight: 700;
  color: #94a3b8;
  position: absolute;
  left: 24px;
  top: 4px;
}

.scatter-svg-wrapper {
  position: relative;
}

.scatter-axis-text {
  font-size: 6px;
  fill: #94a3b8;
  font-weight: 600;
}

.scatter-dot {
  cursor: pointer;
  transition: r 0.15s ease, fill 0.15s ease;
}

.scatter-dot:hover {
  r: 4.5;
  fill: #2563eb;
  opacity: 1;
}

.scatter-plot-container .x-label {
  font-size: 6px;
  font-weight: 700;
  color: #94a3b8;
  text-align: center;
  margin-top: 4px;
}

.scatter-hover-tooltip {
  position: absolute;
  background: #1e293b;
  color: #ffffff;
  padding: 6px 8px;
  border-radius: 4px;
  font-size: 0.6rem;
  pointer-events: none;
  bottom: 30px;
  right: 10px;
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
  line-height: 1.35;
}

.scatter-hover-tooltip p {
  margin: 0;
}

.scatter-stats-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.68rem;
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid #f1f5f9;
}

.blue-text {
  color: var(--brand);
}

/* What This Means */
.what-means-card {
  padding: 16px;
}

.means-desc {
  margin: 0 0 12px;
  font-size: 0.68rem;
  color: var(--text-secondary);
  line-height: 1.4;
}

.focus-callout-card {
  background: #faf5ff;
  border: 1px solid #f3e8ff;
  border-radius: 10px;
  padding: 10px 12px;
  margin-bottom: 12px;
}

.header-callout {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.focus-callout-card .icon-bulb {
  color: #9333ea;
  display: flex;
}

.focus-callout-card .title {
  font-size: 0.72rem;
  color: #6b21a8;
}

.focus-callout-card .desc {
  margin: 0;
  font-size: 0.66rem;
  color: #701a75;
  line-height: 1.35;
}

.view-interventions-link {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--brand);
}

/* Footer Section */
.predictive-footer {
  height: 48px;
  background: #ffffff;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  flex-shrink: 0;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon-globe {
  color: var(--text-secondary);
  display: flex;
}

.transparency-text {
  margin: 0;
  font-size: 0.7rem;
  color: var(--text-secondary);
}

.responsible-link {
  color: var(--brand);
  font-weight: 600;
}

.responsible-link:hover {
  text-decoration: underline;
}

.footer-right {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 0.7rem;
  color: var(--text-secondary);
}

.divider {
  color: var(--border);
}

.privacy-lock {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #059669;
  font-weight: 600;
}

/* ── PREMIUM ACTIVE PATIENT PROFILE ── */
.premium-patient-panel {
  background: linear-gradient(135deg, #f0f7ff 0%, #e0f2fe 100%);
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.02);
  margin-bottom: 24px;
  overflow: hidden;
  position: relative;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #f1f5f9;
}

.panel-header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.avatar-circle {
  background: #ffffff;
  border: 1px solid #c7d2fe;
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.12);
  flex-shrink: 0;
}

.avatar-gif {
  width: 32px;
  height: 32px;
  object-fit: contain;
}

.header-texts h3 {
  margin: 0;
  color: var(--text-primary);
  font-size: 1.2rem;
  font-weight: 800;
}

.patient-name {
  color: var(--brand);
}

.header-texts p {
  margin: 4px 0 0;
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.35;
}

.bmi-badge {
  background: #eff6ff;
  border: 1px solid rgba(59, 130, 246, 0.15);
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 0.78rem;
  font-weight: 700;
  color: #2563eb;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.panel-cols-grid {
  display: grid;
  grid-template-columns: 240px 1fr 1fr;
  gap: 20px;
  padding: 24px;
}

.panel-col {
  background: #ffffff;
  border: 1px solid #f1f5f9;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.005);
}

.col-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 18px;
}

.col-badge {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.col-badge.purple {
  background: #f3e8ff;
  color: #7c3aed;
}

.col-badge.green {
  background: #dcfce7;
  color: #10b981;
}

.col-badge.blue {
  background: #dbeafe;
  color: #2563eb;
}

.col-title {
  font-size: 0.72rem;
  font-weight: 700;
  color: #1e293b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.col-health-score {
  align-items: center;
  justify-content: space-between;
  min-height: 290px;
}

.radial-gauge-wrapper {
  position: relative;
  width: 120px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 6px 0;
}

.premium-gauge {
  transform: rotate(-90deg);
}

.gauge-track {
  stroke: #f1f5f9;
}

.gauge-bar {
  transition: stroke-dasharray 0.5s ease;
}

.gauge-inner-text {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.score-number {
  font-size: 32px;
  font-weight: 850;
  color: #0f172a;
  line-height: 1;
}

.score-total {
  font-size: 11px;
  color: #64748b;
  font-weight: 500;
}

.risk-badge-wrapper {
  margin: 8px 0;
}

.premium-risk-badge {
  padding: 5px 12px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 750;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.premium-risk-badge.low-risk {
  background: #dcfce7;
  color: #15803d;
}

.premium-risk-badge.moderate {
  background: #ffedd5;
  color: #c2410c;
}

.premium-risk-badge.high-risk,
.premium-risk-badge.critical {
  background: #fee2e2;
  color: #b91c1c;
}

.badge-icon {
  flex-shrink: 0;
}

.score-gap-row {
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-bottom: 8px;
}

.gap-title {
  font-size: 0.76rem;
  color: #475569;
}

.gap-sub {
  font-size: 0.68rem;
  color: #94a3b8;
}

.col-wave-decor {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 28px;
  pointer-events: none;
}

.disease-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
}

.disease-item-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.disease-icon-wrapper {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.disease-info-block {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.disease-name-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.disease-name {
  font-size: 0.78rem;
  font-weight: 700;
  color: #334155;
}

.disease-pct {
  font-size: 0.78rem;
  font-weight: 800;
}

.disease-bar-track {
  height: 6px;
  background: #f1f5f9;
  border-radius: 3px;
  overflow: hidden;
}

.disease-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.col-footer-note {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 14px;
  font-size: 0.68rem;
  color: #64748b;
  line-height: 1.25;
}

.location-map-panel {
  display: flex;
  align-items: center;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px 24px;
  position: relative;
  overflow: hidden;
  min-height: 84px;
  box-sizing: border-box;
  margin-bottom: 14px;
}

.location-text-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
  position: relative;
  z-index: 2;
}

.loc-label {
  font-size: 0.68rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 700;
}

.loc-value {
  font-size: 1.15rem;
  font-weight: 850;
  color: #0f172a;
}

.map-bg-wrapper {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  pointer-events: none;
  overflow: hidden;
}

.map-bg-img {
  width: 60%;
  height: 100%;
  object-fit: cover;
  object-position: right 15%;
  position: absolute;
  right: 0;
}

.map-bg-fade {
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  right: 0;
  background: linear-gradient(to right, #ffffff 40%, rgba(255, 255, 255, 0.8) 55%, rgba(255, 255, 255, 0) 100%);
}

.svi-score-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #f1f5f9;
  padding-bottom: 8px;
  margin-bottom: 12px;
}

.svi-label {
  font-size: 0.72rem;
  color: #475569;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.help-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #e2e8f0;
  color: #64748b;
  font-size: 9px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  cursor: help;
}

.svi-value {
  font-size: 0.75rem;
  font-weight: 800;
}

.svi-value.low {
  color: #10b981;
}

.svi-value.medium,
.svi-value.moderate {
  color: #f59e0b;
}

.svi-value.high,
.svi-value.very-high,
.svi-value.critical {
  color: #ef4444;
}

.sdoh-mini-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.sdoh-mini-card {
  background: #f8fafc;
  border: 1px solid #f1f5f9;
  border-radius: 8px;
  padding: 8px 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.mini-card-icon {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.mini-card-icon.blue {
  background: #eff6ff;
  color: #2563eb;
}

.mini-card-icon.purple {
  background: #f5f3ff;
  color: #7c3aed;
}

.mini-card-icon.green {
  background: #ecfdf5;
  color: #10b981;
}

.mini-card-icon.orange {
  background: #fffbeb;
  color: #d97706;
}

.mini-card-text {
  display: flex;
  flex-direction: column;
}

.mini-lbl {
  font-size: 0.62rem;
  color: #64748b;
  font-weight: 500;
  white-space: nowrap;
}

.mini-val {
  font-size: 0.75rem;
  font-weight: 800;
  color: #1e293b;
}

.panel-footer-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(248, 250, 252, 0.65);
  border-top: 1px solid #f1f5f9;
  padding: 12px 24px;
  font-size: 0.7rem;
  color: #64748b;
  font-weight: 500;
}

.footer-left,
.footer-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.footer-icon-shield {
  color: #4f46e5;
  display: flex;
  align-items: center;
}

.footer-icon-cal {
  color: #64748b;
  display: flex;
  align-items: center;
}

/* ── RESPONSIVE OVERRIDES ── */
@media (max-width: 1280px) {
  .geographic-radar-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 1100px) {
  .layout-grid-main {
    grid-template-columns: 1fr;
  }

  .predictive-cards-grid {
    grid-template-columns: repeat(3, 1fr);
  }

  .panel-cols-grid {
    grid-template-columns: 1fr 1fr;
  }
  .col-health-score {
    grid-column: span 2;
    flex-direction: row;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-around;
    min-height: auto;
    padding: 24px;
    gap: 16px;
  }
  .col-wave-decor {
    display: none;
  }
}

@media (max-width: 900px) {
  .predictive-cards-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .content-body {
    padding: 16px 20px;
  }
}

@media (max-width: 768px) {
  .geographic-radar-row {
    grid-template-columns: 1fr;
  }

  .panel-cols-grid {
    grid-template-columns: 1fr;
    padding: 16px;
  }
  .col-health-score {
    grid-column: span 1;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
  }
  .col-wave-decor {
    display: block;
  }
  .col-disease-risks, .col-location-barriers {
    grid-column: span 1;
  }
  .panel-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    padding: 16px;
  }
  .panel-footer-banner {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
    padding: 12px 16px;
  }
}

@media (max-width: 600px) {
  .predictive-cards-grid {
    grid-template-columns: 1fr;
  }
  
  .predictive-footer {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
    height: auto;
    padding: 16px;
  }
}

@media (max-width: 480px) {
  .sdoh-mini-grid {
    grid-template-columns: 1fr;
  }
}
</style>
