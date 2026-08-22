<script setup>
import { ref, computed, watch } from 'vue'
import IconBase from '../components/dashboard/IconBase.vue'
import { patientData, locationRecords, mlPredictionResults, predictionModelResults, isAnalyzed } from '../store/appState'

// US State Abbreviation Map
const US_STATE_ABBR = {
  'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA',
  'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA',
  'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA',
  'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
  'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO',
  'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ',
  'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH',
  'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
  'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT',
  'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY',
  'District of Columbia': 'DC'
}

function getStateAbbr(stateName) {
  if (!stateName) return ''
  const trimmed = String(stateName).trim()
  if (trimmed.length === 2) return trimmed.toUpperCase()
  return US_STATE_ABBR[trimmed] || trimmed
}

function cleanCountyName(countyName) {
  if (!countyName) return ''
  return String(countyName).replace(/\s+County$/i, '').replace(/\s+Parish$/i, '').replace(/\s+Borough$/i, '').trim()
}

const activeStateAbbr = computed(() => {
  const st = patientData.value?.state || locationRecords.value?.[0]?.state || predictionModelResults.value?.state || ''
  return getStateAbbr(st)
})

const activeCounty = computed(() => {
  const ct = patientData.value?.county || locationRecords.value?.[0]?.county || predictionModelResults.value?.county || ''
  return String(ct).trim()
})

const activeLocationLabel = computed(() => {
  const st = activeStateAbbr.value
  const ct = activeCounty.value
  if (ct && st) return `${ct.replace(/\s+County$/i, '')}, ${st}`
  if (st) return st
  if (ct) return ct
  return ''
})

// Tableau State
const tableauKey = ref(0)
const isFullscreen = ref(false)
const isVizLoading = ref(true)

const tableauEmbedUrl = computed(() => {
  const baseUrl = 'https://public.tableau.com/views/CareEquity_Map/Sheet2?:showVizHome=no&:embed=true&:toolbar=no&:tabs=no&:animate_transition=yes&:display_static_image=no'
  const params = []
  
  if (activeStateAbbr.value) {
    params.push(`State Abbr=${encodeURIComponent(activeStateAbbr.value)}`)
  }
  if (activeCounty.value) {
    params.push(`county clean=${encodeURIComponent(activeCounty.value)}`)
  }
  
  return params.length > 0 ? `${baseUrl}&${params.join('&')}` : baseUrl
})

const tableauPublicUrl = 'https://public.tableau.com/app/profile/harish.r2464/viz/CareEquity_Map/Sheet2?publish=yes'

function reloadTableau() {
  isVizLoading.value = true
  tableauKey.value++
  setTimeout(() => {
    isVizLoading.value = false
  }, 1000)
}

function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
}

function onIframeLoad() {
  isVizLoading.value = false
}

// List of map layers
const mapLayers = [
  { id: 'health', name: 'Health Risk' },
  { id: 'svi', name: 'Social Vulnerability' },
  { id: 'food', name: 'Food Access' },
  { id: 'env', name: 'Environmental Risk' },
  { id: 'care', name: 'Healthcare Access' }
]
const activeLayer = ref('health')
const layerCapsuleRef = ref(null)

function scrollCapsuleLeft() {
  if (layerCapsuleRef.value) {
    layerCapsuleRef.value.scrollBy({ left: -140, behavior: 'smooth' })
  }
}

function scrollCapsuleRight() {
  if (layerCapsuleRef.value) {
    layerCapsuleRef.value.scrollBy({ left: 140, behavior: 'smooth' })
  }
}

// Communities metadata
const communities = {
  cuyahoga: {
    id: 'cuyahoga',
    name: 'Cuyahoga County, OH',
    state: 'Ohio',
    population: '1,245,678',
    sviScore: '0.78',
    sviLevel: 'High',
    healthRisk: '0.72',
    healthRiskLevel: 'High',
    foodAccess: '0.43',
    foodAccessLevel: 'Moderate',
    environmental: '0.61',
    environmentalLevel: 'High',
    healthcareAccess: '0.58',
    healthcareAccessLevel: 'Moderate',
    equityScore: 64,
    equityLevel: 'Moderate',
    center: [41.4339, -81.6758],
    bounds: [
      [41.65, -81.97],
      [41.65, -81.42],
      [41.28, -81.42],
      [41.28, -81.97]
    ],
    radar: {
      healthcare: 58,
      social: 72,
      economic: 60,
      food: 43,
      environmental: 70,
      outcomes: 68
    },
    factors: [
      'High poverty rate in urban core',
      'Limited food access in east Cleveland',
      'Transportation barriers / transit deserts',
      'Environmental burden / industrial emissions'
    ],
    resources: [
      { name: 'Cleveland Food Bank', type: 'Food Assistance', dist: '2.3 miles' },
      { name: 'MetroHealth Community Clinic', type: 'Healthcare', dist: '3.1 miles' },
      { name: 'Neighborhood Family Services', type: 'Social Services', dist: '1.8 miles' }
    ]
  },
  wayne: {
    id: 'wayne',
    name: 'Wayne County, MI',
    state: 'Michigan',
    population: '1,793,561',
    sviScore: '0.88',
    sviLevel: 'Very High',
    healthRisk: '0.81',
    healthRiskLevel: 'Very High',
    foodAccess: '0.31',
    foodAccessLevel: 'High Risk',
    environmental: '0.76',
    environmentalLevel: 'Very High',
    healthcareAccess: '0.48',
    healthcareAccessLevel: 'High Risk',
    equityScore: 48,
    equityLevel: 'High Risk',
    center: [42.2808, -83.2721],
    bounds: [
      [42.45, -83.55],
      [42.45, -82.92],
      [42.05, -82.92],
      [42.05, -83.55]
    ],
    radar: {
      healthcare: 48,
      social: 54,
      economic: 42,
      food: 31,
      environmental: 76,
      outcomes: 52
    },
    factors: [
      'Poverty rate exceeding state average',
      'Severe food desert coverage in Detroit',
      'Aging water infrastructure / lead concerns',
      'Air particulate matter from heavy transit'
    ],
    resources: [
      { name: 'Gleaners Community Food Bank', type: 'Food Assistance', dist: '1.4 miles' },
      { name: 'Detroit Health Department Clinic', type: 'Healthcare', dist: '2.8 miles' },
      { name: 'Focus: HOPE Social Center', type: 'Social Services', dist: '3.5 miles' }
    ]
  },
  marion: {
    id: 'marion',
    name: 'Marion County, IN',
    state: 'Indiana',
    population: '967,201',
    sviScore: '0.64',
    sviLevel: 'Mod-High',
    healthRisk: '0.68',
    healthRiskLevel: 'High',
    foodAccess: '0.38',
    foodAccessLevel: 'High Risk',
    environmental: '0.54',
    environmentalLevel: 'Moderate',
    healthcareAccess: '0.62',
    healthcareAccessLevel: 'Moderate',
    equityScore: 58,
    equityLevel: 'Moderate',
    center: [39.7817, -86.1581],
    bounds: [
      [39.93, -86.28],
      [39.93, -85.96],
      [39.63, -85.96],
      [39.63, -86.28]
    ],
    radar: {
      healthcare: 62,
      social: 64,
      economic: 55,
      food: 38,
      environmental: 54,
      outcomes: 60
    },
    factors: [
      'Localized poverty pockets',
      'Limited grocery stores in center township',
      'Moderate public transit access limits',
      'Industrial landfill proximity risks'
    ],
    resources: [
      { name: 'Midwest Food Connection', type: 'Food Assistance', dist: '3.6 miles' },
      { name: 'Eskenazi Health Center', type: 'Healthcare', dist: '2.2 miles' },
      { name: 'Marion County Family Center', type: 'Social Services', dist: '4.1 miles' }
    ]
  },
  franklin: {
    id: 'franklin',
    name: 'Franklin County, OH',
    state: 'Ohio',
    population: '1,323,807',
    sviScore: '0.52',
    sviLevel: 'Moderate',
    healthRisk: '0.55',
    healthRiskLevel: 'Moderate',
    foodAccess: '0.58',
    foodAccessLevel: 'Moderate',
    environmental: '0.48',
    environmentalLevel: 'Moderate',
    healthcareAccess: '0.71',
    healthcareAccessLevel: 'Good',
    equityScore: 71,
    equityLevel: 'Moderate',
    center: [39.9699, -82.9988],
    bounds: [
      [40.15, -83.25],
      [40.15, -82.78],
      [39.82, -82.78],
      [39.82, -83.25]
    ],
    radar: {
      healthcare: 71,
      social: 75,
      economic: 68,
      food: 58,
      environmental: 48,
      outcomes: 70
    },
    factors: [
      'Rapid suburbanization disparities',
      'Local income inequalities near universities',
      'Adequate medical services in core metro',
      'Localized ozone pollution warnings'
    ],
    resources: [
      { name: 'Mid-Ohio Food Collective', type: 'Food Assistance', dist: '4.8 miles' },
      { name: 'Columbus Free Medical Clinic', type: 'Healthcare', dist: '1.9 miles' },
      { name: 'Franklin Co. Job & Family Services', type: 'Social Services', dist: '2.5 miles' }
    ]
  }
}

// Selected community
const selectedId = ref('cuyahoga')
const selectedCommunity = computed(() => {
  return communities[selectedId.value]
})

const patientCommunity = computed(() => {
  const avgRisk = mlPredictionResults.value?.risk_scores ? (Object.values(mlPredictionResults.value.risk_scores).reduce((a, b) => a + b, 0) / 4) : 0.5
  const hasPred = !!predictionModelResults.value
  const pred = predictionModelResults.value
  
  return {
    id: 'patient',
    name: patientData.value.name || 'Active Patient',
    state: hasPred ? `${pred.city}, ${pred.state}` : 'Individual Assessment',
    population: '1 (Individual)',
    sviScore: hasPred ? pred.overall_risk_score.toFixed(2) : '0.65',
    sviLevel: hasPred ? pred.overall_risk_category : 'High Risk',
    healthRisk: avgRisk.toFixed(2),
    healthRiskLevel: avgRisk > 0.7 ? 'Critical' : (avgRisk > 0.5 ? 'High' : 'Moderate'),
    foodAccess: hasPred ? pred.scores.food_security.toFixed(2) : '0.35',
    environmental: hasPred ? pred.scores.neighborhood_environment.toFixed(2) : '0.55',
    healthcareAccess: hasPred ? pred.scores.healthcare_access.toFixed(2) : '0.40',
    equityScore: hasPred ? Math.round((1 - pred.overall_risk_score) * 100) : Math.round((1 - avgRisk) * 100),
    equityLevel: hasPred ? pred.overall_risk_category : 'High Risk',
    radar: {
      healthcare: hasPred ? Math.round(pred.scores.healthcare_access * 100) : 40,
      social: hasPred ? Math.round(pred.scores.social_context * 100) : 60,
      economic: hasPred ? Math.round(pred.scores.economic_stability * 100) : 58,
      food: hasPred ? Math.round(pred.scores.food_security * 100) : 35,
      environmental: hasPred ? Math.round(pred.scores.neighborhood_environment * 100) : 55,
      outcomes: Math.round(avgRisk * 100)
    },
    factors: (mlPredictionResults.value?.sdoh_barriers && mlPredictionResults.value.sdoh_barriers.length > 0)
      ? mlPredictionResults.value.sdoh_barriers
      : [
          'High economic stability concerns',
          'Limited access to primary care providers',
          'Transportation accessibility limits'
        ],
    resources: [
      { name: 'Local Food Pantry', type: 'Food Assistance', dist: '1.2 miles' },
      { name: 'Community Health Clinic', type: 'Healthcare', dist: '2.5 miles' },
      { name: 'Outreach Social Services', type: 'Social Services', dist: '1.9 miles' }
    ]
  }
})

const kpiStats = computed(() => {
  const hasPatient = isAnalyzed.value && predictionModelResults.value
  
  // 1. Communities Mapped
  const baseCommunities = 3152
  const layerShift = activeLayer.value === 'health' ? 12 : (activeLayer.value === 'svi' ? 5 : (activeLayer.value === 'food' ? -8 : 17))
  const patientShift = hasPatient ? Math.round(predictionModelResults.value.overall_risk_score * 30) : 0
  const communitiesVal = baseCommunities + layerShift + patientShift
  const communitiesTrendVal = (6.1 + (layerShift + patientShift) / 10).toFixed(1)
  const communitiesTrendDir = communitiesTrendVal >= 0 ? '↑' : '↓'

  // 2. High Vulnerability Areas
  const baseVulnerability = 412
  const selectedCommunitySVI = parseFloat(selectedCommunity.value?.sviScore || 0.5)
  const sviShift = Math.round((selectedCommunitySVI - 0.5) * 100)
  const vulnerabilityVal = baseVulnerability + sviShift + (hasPatient ? Math.round(predictionModelResults.value.scores.social_context * 25) : 0)
  const vulnerabilityTrendVal = (12.3 + (sviShift / 5)).toFixed(1)
  const vulnerabilityTrendDir = vulnerabilityTrendVal >= 0 ? '↑' : '↓'

  // 3. Health Risk Hotspots
  const baseHotspots = 268
  const selectedCommunityRisk = parseFloat(selectedCommunity.value?.healthRisk || 0.5)
  const riskShift = Math.round((selectedCommunityRisk - 0.5) * 80)
  const hotspotsVal = baseHotspots + riskShift + (hasPatient ? Math.round(predictionModelResults.value.overall_risk_score * 20) : 0)
  const hotspotsTrendVal = (8.6 + (riskShift / 4)).toFixed(1)
  const hotspotsTrendDir = hotspotsTrendVal >= 0 ? '↑' : '↓'

  // 4. Resources Identified
  const baseResources = 1247
  const foodShift = activeLayer.value === 'food' ? 45 : -15
  const resourceVal = baseResources + foodShift + (hasPatient ? Math.round((1 - predictionModelResults.value.scores.healthcare_access) * 60) : 0)
  const resourceTrendVal = (15.4 + (foodShift / 10)).toFixed(1)
  const resourceTrendDir = resourceTrendVal >= 0 ? '↑' : '↓'

  return {
    communities: {
      val: communitiesVal.toLocaleString(),
      trend: `${communitiesTrendDir} ${Math.abs(communitiesTrendVal)}%`
    },
    vulnerability: {
      val: vulnerabilityVal.toLocaleString(),
      trend: `${vulnerabilityTrendDir} ${Math.abs(vulnerabilityTrendVal)}%`
    },
    hotspots: {
      val: hotspotsVal.toLocaleString(),
      trend: `${hotspotsTrendDir} ${Math.abs(hotspotsTrendVal)}%`
    },
    resources: {
      val: resourceVal.toLocaleString(),
      trend: `${resourceTrendDir} ${Math.abs(resourceTrendVal)}%`
    }
  }
})


// Radar Chart Helper Methods
const cx = 120
const cy = 90
const r = 60

const getAngleX = (index, value) => {
  const theta = (index * 2 * Math.PI / 6) - Math.PI / 2
  return cx + r * (value / 100) * Math.cos(theta)
}

const getAngleY = (index, value) => {
  const theta = (index * 2 * Math.PI / 6) - Math.PI / 2
  return cy + r * (value / 100) * Math.sin(theta)
}

const getHexPoints = (val) => {
  return Array.from({ length: 6 }, (_, i) => `${getAngleX(i, val).toFixed(1)},${getAngleY(i, val).toFixed(1)}`).join(' ')
}

const getScorePoints = () => {
  const keys = ['healthcare', 'social', 'economic', 'food', 'environmental', 'outcomes']
  return keys.map((key, i) => {
    const val = selectedCommunity.value.radar[key]
    return `${getAngleX(i, val).toFixed(1)},${getAngleY(i, val).toFixed(1)}`
  }).join(' ')
}

const getLabelX = (index) => {
  const theta = (index * 2 * Math.PI / 6) - Math.PI / 2
  const offsetMultiplier = 16
  return cx + (r + offsetMultiplier) * Math.cos(theta)
}

const getLabelY = (index) => {
  const theta = (index * 2 * Math.PI / 6) - Math.PI / 2
  const offsetMultiplier = 12
  return cy + (r + offsetMultiplier) * Math.sin(theta) + 3
}

const axes = [
  { label: 'Healthcare', key: 'healthcare' },
  { label: 'Social', key: 'social' },
  { label: 'Economic', key: 'economic' },
  { label: 'Food Access', key: 'food' },
  { label: 'Env Safety', key: 'environmental' },
  { label: 'Outcomes', key: 'outcomes' }
]
</script>

<template>
  <div class="equity-map-page">
    <div class="main-layout">
      
      <!-- 1. Central Content Column -->
      <div class="content-body">
        
        <!-- Header -->
        <header class="page-header">
          <div>
            <h1>Equity Map</h1>
            <p class="subtitle">Visualize health equity and social determinants across communities.</p>
          </div>
          <router-link to="/reports" class="btn outlined report-btn">
            <IconBase name="report" :size="15" /> Create Report
          </router-link>
        </header>

        <!-- Patient Specific Context Banner -->
        <!-- <section v-if="patientData && patientData.name" class="card active-patient-banner" style="background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%); color: white; border: none; display: flex; justify-content: space-between; align-items: center; padding: 14px 20px; box-shadow: 0 10px 25px rgba(59, 130, 246, 0.15); border-radius: 12px; margin-bottom: 16px;">
          <div style="display: flex; align-items: center; gap: 12px;">
            <div style="background: rgba(255,255,255,0.2); width: 34px; height: 34px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 16px;">🔬</div>
            <div>
              <h3 style="margin: 0; color: white; font-size: 0.95rem; font-weight: 700;">Active Patient: {{ patientData.name }} (Age {{ patientData.age }})</h3>
              <p style="margin: 2px 0 0; font-size: 0.78rem; opacity: 0.9; color: rgba(255,255,255,0.9);">
                Dynamically geo-matching coordinates to SDOH risk indicators.
              </p>
            </div>
          </div>
        </section> -->

        <!-- KPI Cards Row -->
        <section class="kpi-grid">
          <div class="card kpi-card blue">
            <div class="kpi-header">
              <span class="lbl">Communities Mapped</span>
              <span class="trend-badge">{{ kpiStats.communities.trend }}</span>
            </div>
            <div class="kpi-value">{{ kpiStats.communities.val }}</div>
          </div>

          <div class="card kpi-card red">
            <div class="kpi-header">
              <span class="lbl">High Vulnerability Areas</span>
              <span class="trend-badge">{{ kpiStats.vulnerability.trend }}</span>
            </div>
            <div class="kpi-value">{{ kpiStats.vulnerability.val }}</div>
          </div>

          <div class="card kpi-card purple">
            <div class="kpi-header">
              <span class="lbl">Health Risk Hotspots</span>
              <span class="trend-badge">{{ kpiStats.hotspots.trend }}</span>
            </div>
            <div class="kpi-value">{{ kpiStats.hotspots.val }}</div>
          </div>

          <div class="card kpi-card green">
            <div class="kpi-header">
              <span class="lbl">Resources Identified</span>
              <span class="trend-badge">{{ kpiStats.resources.trend }}</span>
            </div>
            <div class="kpi-value">{{ kpiStats.resources.val }}</div>
          </div>
        </section>

        <!-- Tableau Interactive Map Container -->
        <div class="map-wrapper" :class="{ 'is-fullscreen': isFullscreen }">
          <!-- Top Control Header Bar -->
          <div class="tableau-topbar">
            <div class="tableau-info">
              <span class="live-indicator">
                <span class="dot-pulse"></span>
                LIVE VIZ
              </span>
              <span class="viz-title">CareEquity Health Disparities & Risk Map</span>
            </div>

            <div class="tableau-actions">
              <button class="tb-btn" @click="reloadTableau" title="Reload Map View">
                <IconBase name="refresh" :size="13" />
                <span>Reload</span>
              </button>
              <button class="tb-btn" @click="toggleFullscreen" title="Toggle Fullscreen View">
                <IconBase name="maximize" :size="13" />
                <span>{{ isFullscreen ? 'Exit Fullscreen' : 'Fullscreen' }}</span>
              </button>
            </div>
          </div>

          <!-- Loading indicator -->
          <div v-if="isVizLoading" class="tableau-loader">
            <div class="spinner"></div>
            <p>Loading Map View...</p>
          </div>

          <!-- Tableau Iframe Container -->
          <div class="tableau-frame-container">
            <iframe
              :key="`${tableauEmbedUrl}-${tableauKey}`"
              :src="tableauEmbedUrl"
              class="tableau-iframe"
              title="CareEquity Map Tableau Interactive View"
              @load="onIframeLoad"
              allow="fullscreen; accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowfullscreen
              loading="eager"
            ></iframe>
          </div>
        </div>

      </div>

      <!-- 2. Right Side details rail -->
      <aside v-if="selectedCommunity" class="details-rail">
        <div class="rail-header">
          <h3>Community Details</h3>
          <button @click="selectedId = null" class="close-btn">&times;</button>
        </div>

        <!-- Patient Real-time Location SDoH Card -->
        <div v-if="isAnalyzed" class="patient-realtime-card" style="border: 1px solid rgba(79, 70, 229, 0.2); background: #fdfdfd; border-radius: var(--radius-md); padding: 16px; margin-bottom: 8px; flex-shrink: 0;">
          <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px; border-bottom: 1px solid var(--border); padding-bottom: 8px;">
            <span style="background: #ffffff; width: 32px; height: 32px; border-radius: 6px; display: flex; align-items: center; justify-content: center; border: 1px solid var(--border);">
              <img src="/assets/meeting-point.png" style="width: 22px; height: 22px; object-fit: contain;" />
            </span>
            <div>
              <h4 style="margin: 0; font-size: 0.9rem; font-weight: bold; color: var(--text-primary);">Entered Location SDOH</h4>
            </div>
          </div>
          
          <div style="display: flex; gap: 12px; align-items: center; margin-bottom: 12px;">
            <!-- Radial Score Gauge for Patient -->
            <div class="circle-gauge" style="width: 60px; height: 60px; position: relative;">
              <svg width="60" height="60" viewBox="0 0 36 36" class="circular-chart">
                <path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                <path class="circle" :stroke-dasharray="patientCommunity.equityScore + ', 100'" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
              </svg>
              <div class="gauge-center" style="font-size: 8px; display: flex; flex-direction: column; align-items: center; justify-content: center; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);">
                <span class="score-num" style="font-size: 13px; font-weight: bold; color: var(--text-primary);">{{ patientCommunity.equityScore }}</span>
                <span class="score-den" style="color: var(--text-secondary);">/100</span>
              </div>
            </div>
            
            <div style="flex: 1;">
              <p style="margin: 0; font-size: 0.8rem; font-weight: bold; color: var(--text-primary);">{{ patientData.name }}'s Location</p>
              <p style="margin: 2px 0; font-size: 0.75rem; color: var(--text-secondary);">{{ patientCommunity.state }}</p>
              <span class="gauge-level-badge font-bold" :class="patientCommunity.equityLevel.toLowerCase().replace(' ', '-')" style="font-size: 0.65rem; padding: 2px 6px; border-radius: 4px; display: inline-block;">
                {{ patientCommunity.equityLevel }}
              </span>
            </div>
          </div>
          
          <!-- Table values -->
          <div class="gauge-table" style="font-size: 0.75rem; border-top: 1px dashed var(--border); padding-top: 8px; display: flex; flex-direction: column; gap: 4px;">
            <div class="table-row" style="display: flex; justify-content: space-between; margin-bottom: 2px;">
              <span class="lbl" style="color: var(--text-secondary);">SVI Score</span>
              <span class="val red-text" style="font-weight: bold;">{{ patientCommunity.sviScore }} ({{ patientCommunity.sviLevel }})</span>
            </div>
            <div class="table-row" style="display: flex; justify-content: space-between; margin-bottom: 2px;">
              <span class="lbl" style="color: var(--text-secondary);">Health Risk</span>
              <span class="val red-text" style="font-weight: bold;">{{ patientCommunity.healthRisk }} ({{ patientCommunity.healthRiskLevel }})</span>
            </div>
            <div class="table-row" style="display: flex; justify-content: space-between; margin-bottom: 2px;">
              <span class="lbl" style="color: var(--text-secondary);">Food Access</span>
              <span class="val yellow-text" style="font-weight: bold;">{{ patientCommunity.foodAccess }}</span>
            </div>
            <div class="table-row" style="display: flex; justify-content: space-between; margin-bottom: 2px;">
              <span class="lbl" style="color: var(--text-secondary);">Env Risk</span>
              <span class="val red-text" style="font-weight: bold;">{{ patientCommunity.environmental }}</span>
            </div>
            <div class="table-row" style="display: flex; justify-content: space-between; margin-bottom: 2px;">
              <span class="lbl" style="color: var(--text-secondary);">Healthcare</span>
              <span class="val yellow-text" style="font-weight: bold;">{{ patientCommunity.healthcareAccess }}</span>
            </div>
          </div>
        </div>

        <!-- Selected Community Title -->
        <div class="selected-header-card">
          <span class="card-icon-box">
            <img src="/assets/location.png" style="width: 22px; height: 22px; object-fit: contain;" />
          </span>
          <div class="text-info">
            <h4>{{ selectedCommunity.name }}</h4>
            <p>{{ selectedCommunity.state }}</p>
          </div>
        </div>

        <!-- Health Equity Score radial gauge -->
        <div class="card radial-score-card">
          <div class="gauge-left">
            <div class="circle-gauge">
              <svg width="84" height="84" viewBox="0 0 36 36" class="circular-chart">
                <path class="circle-bg"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
                <path class="circle"
                  :stroke-dasharray="selectedCommunity.equityScore + ', 100'"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
              </svg>
              <div class="gauge-center">
                <span class="score-num">{{ selectedCommunity.equityScore }}</span>
                <span class="score-den">/100</span>
              </div>
            </div>
            <span class="gauge-level-badge font-bold" :class="selectedCommunity.equityLevel.toLowerCase().replace(' ', '-')">
              {{ selectedCommunity.equityLevel }}
            </span>
          </div>

          <div class="gauge-table">
            <div class="table-row">
              <span class="lbl">Population</span>
              <span class="val">{{ selectedCommunity.population }}</span>
            </div>
            <div class="table-row">
              <span class="lbl">SVI Score</span>
              <span class="val red-text">{{ selectedCommunity.sviScore }} {{ selectedCommunity.sviLevel }}</span>
            </div>
            <div class="table-row">
              <span class="lbl">Health Risk</span>
              <span class="val red-text">{{ selectedCommunity.healthRisk }} {{ selectedCommunity.healthRiskLevel }}</span>
            </div>
            <div class="table-row">
              <span class="lbl">Food Access</span>
              <span class="val yellow-text">{{ selectedCommunity.foodAccess }}</span>
            </div>
            <div class="table-row">
              <span class="lbl">Env Risk</span>
              <span class="val red-text">{{ selectedCommunity.environmental }}</span>
            </div>
            <div class="table-row">
              <span class="lbl">Healthcare</span>
              <span class="val yellow-text">{{ selectedCommunity.healthcareAccess }}</span>
            </div>
          </div>
        </div>

        <!-- Radar spider chart card -->
        <div class="card radar-chart-card">
          <h5 class="font-bold">Equity Score Breakdown</h5>
          
          <div class="radar-svg-wrapper">
            <svg width="240" height="200" viewBox="0 0 240 200">
              <polygon :points="getHexPoints(20)" class="radar-grid" />
              <polygon :points="getHexPoints(40)" class="radar-grid" />
              <polygon :points="getHexPoints(60)" class="radar-grid" />
              <polygon :points="getHexPoints(80)" class="radar-grid" />
              <polygon :points="getHexPoints(100)" class="radar-grid" />

              <line 
                v-for="(axis, i) in axes" 
                :key="'axis-' + i" 
                :x1="cx" 
                :y1="cy" 
                :x2="getAngleX(i, 100)" 
                :y2="getAngleY(i, 100)" 
                class="radar-axis-line" 
              />

              <polygon :points="getScorePoints()" class="radar-filled-shape" />

              <circle 
                v-for="(axis, i) in axes" 
                :key="'dot-' + i"
                :cx="getAngleX(i, selectedCommunity.radar[axis.key])"
                :cy="getAngleY(i, selectedCommunity.radar[axis.key])"
                r="3.5"
                class="radar-dot"
              />

              <text 
                v-for="(axis, i) in axes" 
                :key="'lbl-' + i" 
                :x="getLabelX(i)" 
                :y="getLabelY(i)" 
                class="radar-lbl-text" 
                text-anchor="middle"
              >
                {{ axis.label }} ({{ selectedCommunity.radar[axis.key] }})
              </text>
            </svg>
          </div>
        </div>

        <!-- Driving risk info card -->
        <div class="card driver-card">
          <h5 class="font-bold">What's driving risk here?</h5>
          <p class="font-semibold">Elevated risk is driven by high social vulnerability, limited food access, transportation barriers, and environmental exposure.</p>
          <router-link to="/sdoh-insights" class="driver-link font-bold">View SDOH Insights &rarr;</router-link>
        </div>

        <!-- Nearby Resources card -->
        <div class="card resources-card">
          <div class="sec-header">
            <h5 class="font-bold">Nearby Resources</h5>
            <router-link to="/community-resources" class="see-all font-bold">See all (23)</router-link>
          </div>

          <ul class="resources-list">
            <li v-for="(res, i) in selectedCommunity.resources" :key="i">
              <span class="res-dot" :class="res.type.toLowerCase().replace(' ', '-')"></span>
              <div class="res-details">
                <b>{{ res.name }}</b>
                <p>{{ res.type }}</p>
              </div>
              <span class="res-distance">{{ res.dist }}</span>
            </li>
          </ul>
        </div>

        <!-- Bottom buttons -->
        <div class="action-footer">
          <router-link to="/community-resources" class="btn primary full-width" style="text-align: center; justify-content: center;">
            View Community Resources
          </router-link>
        </div>
      </aside>

    </div>
  </div>
</template>

<style scoped>
.equity-map-page {
  background: #f8fafc;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.main-layout {
  display: flex;
  height: 100%;
  width: 100%;
  overflow: hidden;
}

/* Central map column */
.content-body {
  flex: 1;
  padding: 24px 32px 32px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow-y: auto;
  min-width: 0;
}

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

.page-header .subtitle {
  margin: 0;
  font-size: 0.86rem;
  color: var(--text-secondary);
}

.report-btn {
  background: #ffffff;
  padding: 8px 16px;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-primary);
  border: 1px solid var(--border);
  text-decoration: none;
}

/* KPI Cards Row */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.kpi-card {
  padding: 16px;
  background: #ffffff;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.kpi-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.kpi-header .lbl {
  font-size: 0.76rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.trend-badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
}

.kpi-card.blue .trend-badge { background: #eff6ff; color: #3b82f6; }
.kpi-card.red .trend-badge { background: #fee2e2; color: #ef4444; }
.kpi-card.purple .trend-badge { background: #f5f3ff; color: #8b5cf6; }
.kpi-card.green .trend-badge { background: #ecfdf5; color: #10b981; }

.kpi-value {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1.1;
  margin-bottom: 8px;
}

.sparkline {
  width: 100%;
  height: 20px;
  opacity: 0.85;
}

/* Map layer toolbar */
.toolbar-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border);
  padding-bottom: 14px;
}

.layer-selector {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  max-width: 100%;
}

.layer-selector .lbl {
  font-size: 0.76rem;
  font-weight: 700;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.layer-capsule-wrapper {
  display: flex;
  align-items: center;
  gap: 4px;
  max-width: 100%;
  position: relative;
  min-width: 0;
}

.scroll-arrow-btn {
  display: none;
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: 6px;
  width: 24px;
  height: 24px;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.15s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.scroll-arrow-btn:hover {
  background: #f1f5f9;
  color: var(--text-primary);
  border-color: #cbd5e1;
}

.scroll-arrow-btn:active {
  transform: scale(0.94);
}

.layer-capsule {
  display: inline-flex;
  background: #e2e8f0;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 3px;
  max-width: 100%;
  overflow-x: auto;
  scroll-behavior: smooth;
  white-space: nowrap;
  scrollbar-width: none;
  box-sizing: border-box;
}

.layer-capsule::-webkit-scrollbar {
  display: none;
}

.layer-btn {
  border: none;
  background: transparent;
  padding: 6px 14px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #475569;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.layer-btn.active {
  background: #2563eb;
  color: #ffffff;
  box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
}

.toolbar-actions {
  display: flex;
  gap: 10px;
}

.btn {
  border-radius: var(--radius-md);
  font-size: 0.76rem;
  font-weight: 700;
  padding: 8px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.15s ease;
  cursor: pointer;
}

.btn.primary {
  background: var(--brand);
  border: none;
  color: #ffffff;
}
.btn.primary:hover {
  background: var(--brand-dark);
}

.action-btn {
  background: #ffffff;
  border: 1px solid var(--border);
  padding: 6px 12px;
  font-size: 0.76rem;
  font-weight: 600;
  color: var(--text-secondary);
}

/* Map wrapper */
.map-wrapper {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  height: 650px;
  position: relative;
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  transition: all 0.25s ease;
}

.map-wrapper.is-fullscreen {
  position: fixed;
  inset: 16px;
  height: auto;
  z-index: 99999;
  border-radius: var(--radius-lg);
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.35);
  background: #ffffff;
}

/* Tableau Topbar */
.tableau-topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  background: #f8fafc;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
  gap: 12px;
}

.tableau-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-primary);
  min-width: 0;
}

.live-indicator {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 0.62rem;
  font-weight: 800;
  color: #16a34a;
  background: #dcfce7;
  padding: 2px 7px;
  border-radius: 999px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.dot-pulse {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #16a34a;
  box-shadow: 0 0 0 2px rgba(22, 163, 74, 0.3);
  animation: pulse-dot 1.8s infinite ease-in-out;
}

@keyframes pulse-dot {
  0% { transform: scale(0.9); opacity: 0.8; }
  50% { transform: scale(1.3); opacity: 1; box-shadow: 0 0 0 4px rgba(22, 163, 74, 0.15); }
  100% { transform: scale(0.9); opacity: 0.8; }
}

.viz-title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--text-primary);
}

.viz-sub {
  color: var(--text-secondary);
  font-weight: 400;
  font-size: 0.72rem;
}

.tableau-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.tb-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: #ffffff;
  border: 1px solid var(--border);
  padding: 5px 10px;
  border-radius: 6px;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  text-decoration: none;
  transition: all 0.15s ease;
}

.tb-btn:hover {
  background: #f1f5f9;
  color: var(--text-primary);
  border-color: #cbd5e1;
}

.tb-btn.highlight {
  background: #eff6ff;
  color: #2563eb;
  border-color: #bfdbfe;
}

.tb-btn.highlight:hover {
  background: #2563eb;
  color: #ffffff;
  border-color: #2563eb;
}

/* Tableau Frame Container */
.tableau-frame-container {
  flex: 1;
  width: 100%;
  height: 100%;
  min-height: 0;
  position: relative;
  background: #ffffff;
  overflow: hidden;
}

.tableau-iframe {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: calc(100% + 30px);
  border: none;
  display: block;
}

/* Loader */
.tableau-loader {
  position: absolute;
  inset: 42px 0 0 0;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(4px);
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
  font-size: 0.82rem;
  font-weight: 600;
}

.spinner {
  width: 28px;
  height: 28px;
  border: 3px solid #e2e8f0;
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Trends Footer block */
.trends-footer {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 14px 18px;
  box-shadow: var(--shadow-sm);
}

.trends-footer .section-title {
  margin: 0 0 10px;
  font-size: 0.76rem;
  font-weight: 700;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 6px;
  text-transform: uppercase;
}

.trends-footer .section-title .light {
  color: var(--text-tertiary);
  font-weight: 500;
  text-transform: none;
}

.trends-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 24px;
}

.trend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.72rem;
  white-space: nowrap;
  flex-shrink: 0;
}

.icon-indicator {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.icon-indicator.red-dot { background: #ef4444; }
.icon-indicator.green-dot { background: #10b981; }

.trend-item .lbl {
  color: var(--text-secondary);
  margin-right: auto;
}

.trend-item .val {
  font-size: 0.74rem;
}

.red-text { color: #ef4444; }
.green-text { color: #10b981; }

/* 2. Right Side details rail */
.details-rail {
  width: 340px;
  background: #ffffff;
  border-left: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 24px 20px;
  overflow-y: auto;
  flex-shrink: 0;
  height: 100%;
}

.rail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.rail-header h3 {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--text-primary);
}

.rail-header .close-btn {
  border: none;
  background: transparent;
  font-size: 1.4rem;
  cursor: pointer;
  line-height: 1;
  color: var(--text-tertiary);
}

.selected-header-card {
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  background: #fafafa;
}

.card-icon-box {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  background: #ffffff;
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.selected-header-card .text-info {
  display: flex;
  flex-direction: column;
  margin-right: auto;
}

.selected-header-card h4 {
  margin: 0;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-primary);
}

.selected-header-card p {
  margin: 1px 0 0;
  font-size: 0.68rem;
  color: var(--text-secondary);
}

.follow-btn {
  background: #ffffff;
  border: 1px solid var(--border);
  padding: 4px 10px;
  font-size: 0.68rem;
  font-weight: 600;
  border-radius: 6px;
}

/* Radial Score Card */
.radial-score-card {
  padding: 14px;
  display: flex;
  gap: 14px;
  align-items: center;
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
}

.gauge-left {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.circle-gauge {
  position: relative;
  width: 74px;
  height: 74px;
}

.circular-chart {
  display: block;
  max-width: 100%;
}

.circle-bg {
  fill: none;
  stroke: #f1f5f9;
  stroke-width: 2.8;
}

.circle {
  fill: none;
  stroke: var(--brand);
  stroke-width: 2.8;
  stroke-linecap: round;
  transition: stroke-dasharray 0.35s ease;
}

.gauge-center {
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

.score-num {
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--text-primary);
}

.score-den {
  font-size: 0.58rem;
  color: var(--text-secondary);
  font-weight: 600;
}

.gauge-level-badge {
  font-size: 0.62rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 12px;
}

.gauge-level-badge.moderate { background: #fffbeb; color: #d97706; }
.gauge-level-badge.high-risk { background: #fee2e2; color: #b91c1c; }

.gauge-table {
  display: flex;
  flex-direction: column;
  gap: 3px;
  flex: 1;
  border-left: 1px solid var(--border);
  padding-left: 12px;
}

.gauge-table .table-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.68rem;
}

.gauge-table .lbl {
  color: var(--text-secondary);
}

.gauge-table .val {
  font-weight: 700;
  color: var(--text-primary);
}

/* Radar chart style */
.radar-chart-card {
  padding: 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
}

.radar-chart-card h5 {
  margin: 0 0 10px;
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--text-primary);
  text-transform: uppercase;
}

.radar-svg-wrapper {
  display: flex;
  justify-content: center;
}

.radar-grid {
  fill: none;
  stroke: #e2e8f0;
  stroke-width: 1;
}

.radar-axis-line {
  stroke: #cbd5e1;
  stroke-width: 1;
}

.radar-filled-shape {
  fill: rgba(37, 99, 235, 0.15);
  stroke: #2563eb;
  stroke-width: 1.8;
  transition: points 0.35s ease;
}

.radar-dot {
  fill: #2563eb;
  stroke: #ffffff;
  stroke-width: 1.2;
  transition: cx 0.35s ease, cy 0.35s ease;
}

.radar-lbl-text {
  font-size: 7.5px;
  font-weight: 700;
  fill: #64748b;
}

/* Driver card */
.driver-card {
  padding: 14px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: var(--radius-lg);
}

.driver-card h5 {
  margin: 0 0 4px;
  font-size: 0.76rem;
  font-weight: 700;
  color: var(--text-primary);
}

.driver-card p {
  margin: 0 0 8px;
  font-size: 0.68rem;
  color: var(--text-secondary);
  line-height: 1.4;
}

.driver-link {
  font-size: 0.68rem;
  font-weight: 700;
  color: var(--brand);
  text-decoration: none;
}

.driver-link:hover {
  text-decoration: underline;
}

/* Resources list card */
.resources-card {
  padding: 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
}

.resources-card .sec-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.resources-card h5 {
  margin: 0;
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--text-primary);
}

.see-all {
  font-size: 0.68rem;
  font-weight: 700;
  color: var(--brand);
  text-decoration: none;
}

.resources-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.resources-list li {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.72rem;
}

.res-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.res-dot.food-assistance { background: #f59e0b; }
.res-dot.healthcare { background: #3b82f6; }
.res-dot.social-services { background: #8b5cf6; }

.res-details {
  display: flex;
  flex-direction: column;
  margin-right: auto;
}

.res-details b {
  color: var(--text-primary);
}

.res-details p {
  margin: 1px 0 0;
  font-size: 0.64rem;
  color: var(--text-tertiary);
}

.res-distance {
  color: var(--text-secondary);
  font-size: 0.66rem;
  font-weight: 600;
}

/* Action footer buttons */
.action-footer {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: auto;
  padding-top: 14px;
  border-top: 1px solid var(--border);
}

.action-footer .btn {
  padding: 10px 16px;
  font-size: 0.78rem;
  font-weight: 700;
  text-decoration: none;
}

.btn.outlined {
  background: #ffffff;
  border: 1px solid var(--border);
  color: var(--text-primary);
}

/* ── RESPONSIVE OVERRIDES ── */
@media (max-width: 1100px) {
  .scroll-arrow-btn {
    display: flex;
  }

  .main-layout {
    flex-direction: column;
    height: 100%;
    overflow-y: auto;
  }

  .content-body {
    height: auto;
    overflow: visible;
    padding: 16px 20px;
    flex-shrink: 0;
  }

  .details-rail {
    width: 100%;
    height: auto;
    border-left: none;
    border-top: 1px solid var(--border);
    overflow: visible;
    padding: 20px;
    flex-shrink: 0;
  }
}

@media (max-width: 900px) {
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .page-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .report-btn {
    align-self: flex-start;
  }
}

@media (max-width: 600px) {
  .kpi-grid {
    grid-template-columns: 1fr;
  }
  
  .layer-selector {
    flex-direction: column;
    align-items: flex-start;
    width: 100%;
    gap: 8px;
  }

  .layer-capsule {
    width: 100%;
    display: flex;
    overflow-x: auto;
    white-space: nowrap;
    scrollbar-width: none;
    box-sizing: border-box;
  }

  .layer-capsule::-webkit-scrollbar {
    display: none;
  }

  .layer-btn {
    flex-shrink: 0;
    flex: 1;
    text-align: center;
    padding: 6px 10px;
  }
}
</style>
