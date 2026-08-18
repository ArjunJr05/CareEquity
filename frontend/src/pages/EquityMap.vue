<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import IconBase from '../components/dashboard/IconBase.vue'
import { patientData, mlPredictionResults, predictionModelResults, isAnalyzed } from '../store/appState'
import L from 'leaflet'

import 'leaflet/dist/leaflet.css'

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


// Leaflet Map Reference
let map = null
const polygonLayers = {}

// Helper to determine polygon color based on score and active layer
function getPolygonColor(communityId, layer) {
  const comm = communities[communityId]
  let val = 0
  if (layer === 'health') val = parseFloat(comm.healthRisk) * 100
  else if (layer === 'svi') val = parseFloat(comm.sviScore) * 100
  else if (layer === 'food') val = parseFloat(comm.foodAccess) * 100
  else if (layer === 'env') val = parseFloat(comm.environmental) * 100
  else if (layer === 'care') val = parseFloat(comm.healthcareAccess) * 100

  if (val <= 20) return '#93c5fd'
  if (val <= 40) return '#86efac'
  if (val <= 60) return '#fde047'
  if (val <= 80) return '#fed7aa'
  return '#fca5a5'
}

function updateMapColors() {
  Object.keys(polygonLayers).forEach(id => {
    const poly = polygonLayers[id]
    if (poly) {
      poly.setStyle({
        fillColor: getPolygonColor(id, activeLayer.value),
        color: selectedId.value === id ? '#4f46e5' : '#ffffff',
        weight: selectedId.value === id ? 3 : 1.5
      })
    }
  })
}

// Leaflet Map Initialization
onMounted(() => {
  // Centered roughly in the Midwest region containing OH, MI, IN
  map = L.map('leaflet-map', {
    zoomControl: false,
    attributionControl: false
  }).setView([41.1, -83.5], 6)

  // Use crisp Voyager tiles from CartoDB which match the dashboard theme
  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    maxZoom: 19
  }).addTo(map)

  // Add County Polygons
  Object.keys(communities).forEach(id => {
    const comm = communities[id]
    const polygon = L.polygon(comm.bounds, {
      fillColor: getPolygonColor(id, activeLayer.value),
      fillOpacity: 0.65,
      color: selectedId.value === id ? '#4f46e5' : '#ffffff',
      weight: selectedId.value === id ? 3 : 1.5
    }).addTo(map)

    // Event handlers
    polygon.on('click', () => {
      selectedId.value = id
      polygon.openPopup()
    })

    polygon.on('mouseover', () => {
      polygon.setStyle({ fillOpacity: 0.85, weight: 2.5 })
    })

    polygon.on('mouseout', () => {
      polygon.setStyle({
        fillOpacity: 0.65,
        weight: selectedId.value === id ? 3 : 1.5
      })
    })

    // Bind popup tooltip
    const popupContent = `
      <div style="font-family: sans-serif; font-size: 11px; min-width: 150px;">
        <b style="font-size:12px; color:#1e293b;">${comm.name}</b><br/>
        <span style="color:#64748b;">Population: ${comm.population}</span><br/>
        <span style="color:#ef4444;">Health Risk: ${comm.healthRisk}</span>
      </div>
    `
    polygon.bindPopup(popupContent)

    polygonLayers[id] = polygon
  })

  // Add Patient Pin Marker (using dynamic geolocated coordinates)
  if (patientData.value && patientData.value.name) {
    const patientIcon = L.divIcon({
      className: 'custom-patient-icon',
      html: `
        <div style="position:relative; width: 14px; height: 14px;">
          <div class="pulse-ring-leaflet"></div>
          <div style="width: 8px; height: 8px; background: #4f46e5; border: 2px solid white; border-radius: 50%;"></div>
        </div>
      `,
      iconSize: [14, 14]
    })
    const lat = parseFloat(patientData.value.lat) || 41.48
    const long = parseFloat(patientData.value.long) || -81.65
    
    const hasPred = !!predictionModelResults.value
    const pred = predictionModelResults.value
    let popupText = `<b>${patientData.value.name} (Patient Location)</b>`
    if (hasPred) {
      popupText += `<br/><b>Location:</b> ${pred.city}, ${pred.state}`
      popupText += `<br/><b>Risk Score:</b> ${pred.overall_risk_category} (${pred.overall_risk_score.toFixed(2)})`
    }
    
    const marker = L.marker([lat, long], { icon: patientIcon })
      .addTo(map)
      .bindPopup(popupText)
      
    marker.on('click', () => {
      map.panTo([lat, long])
      marker.openPopup()
    })
  }

  if (isAnalyzed.value && patientData.value && patientData.value.lat) {
    map.setView([parseFloat(patientData.value.lat), parseFloat(patientData.value.long)], 8)
  } else {
    // Adjust view to fit all bounding areas
    const allBounds = Object.values(communities).map(c => c.bounds)
    const mergedBounds = L.latLngBounds(allBounds.flat())
    map.fitBounds(mergedBounds, { padding: [20, 20] })
  }
})

onUnmounted(() => {
  if (map) {
    map.remove()
  }
})

// Watchers to update styles dynamically
watch(isAnalyzed, (analyzed) => {
  if (analyzed && map && patientData.value.lat) {
    map.panTo([parseFloat(patientData.value.lat), parseFloat(patientData.value.long)])
  }
}, { immediate: true })

watch(activeLayer, () => {
  updateMapColors()
})

watch(selectedId, (newId) => {
  updateMapColors()
  if (newId && map) {
    const comm = communities[newId]
    if (comm) {
      map.panTo(comm.center)
      const poly = polygonLayers[newId]
      if (poly) poly.openPopup()
    }
  }
})

// Custom zoom controls
const zoomIn = () => {
  if (map) map.zoomIn()
}
const zoomOut = () => {
  if (map) map.zoomOut()
}
const resetMap = () => {
  if (map) {
    const allBounds = Object.values(communities).map(c => c.bounds)
    map.fitBounds(L.latLngBounds(allBounds.flat()), { padding: [20, 20] })
  }
}

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

        <!-- Map Layer Toolbar -->
        <section class="toolbar-section">
          <div class="layer-selector">
            <span class="lbl">Map Layer</span>
            <div class="layer-capsule-wrapper">
              <button class="scroll-arrow-btn left" @click="scrollCapsuleLeft" title="Scroll Left">
                <IconBase name="chevron-left" :size="12" />
              </button>
              <div ref="layerCapsuleRef" class="layer-capsule">
                <button 
                  v-for="layer in mapLayers" 
                  :key="layer.id"
                  class="layer-btn"
                  :class="{ active: activeLayer === layer.id }"
                  @click="activeLayer = layer.id"
                >
                  {{ layer.name }}
                </button>
              </div>
              <button class="scroll-arrow-btn right" @click="scrollCapsuleRight" title="Scroll Right">
                <IconBase name="chevron-right" :size="12" />
              </button>
            </div>
          </div>

          
        </section>

        <!-- Leaflet Map Container -->
        <div class="map-wrapper">
          <!-- Floating Controls on the left -->
          <div class="map-controls">
            <button @click="zoomIn" title="Zoom In"><IconBase name="plus" :size="14" /></button>
            <button @click="zoomOut" title="Zoom Out"><IconBase name="minus" :size="14" /></button>
            <button @click="resetMap" title="Reset View"><IconBase name="home" :size="14" /></button>
            <button title="Layers"><IconBase name="filter" :size="14" /></button>
          </div>

          <!-- Color scale legend overlay bottom-left -->
          <div class="map-legend">
            <p class="legend-title">Health Risk Score <span class="light">(Population Weighted)</span></p>
            <div class="legend-colors">
              <div class="legend-item"><span class="color blue"></span> 0 - 20 <span>Low</span></div>
              <div class="legend-item"><span class="color green"></span> 21 - 40 <span>Low-Mod</span></div>
              <div class="legend-item"><span class="color yellow"></span> 41 - 60 <span>Mod</span></div>
              <div class="legend-item"><span class="color orange"></span> 61 - 80 <span>High</span></div>
              <div class="legend-item"><span class="color red"></span> 81 - 100 <span>Very High</span></div>
            </div>
          </div>

          <!-- Real Map Element -->
          <div id="leaflet-map" style="width: 100%; height: 100%;"></div>
        </div>

        <!-- Equity Trends Footer Row -->
        <section class="trends-footer">
          <p class="section-title"><IconBase name="trend" :size="13" /> Equity Trends <span class="light">(vs last 30 days)</span></p>
          <div class="trends-grid">
            <div class="trend-item">
              <span class="icon-indicator red-dot"></span>
              <span class="lbl">Health Risk</span>
              <span class="val font-semibold red-text">&uarr; 8.6%</span>
            </div>
            <div class="trend-item">
              <span class="icon-indicator red-dot"></span>
              <span class="lbl">Social Vulnerability</span>
              <span class="val font-semibold red-text">&uarr; 6.3%</span>
            </div>
            <div class="trend-item">
              <span class="icon-indicator green-dot"></span>
              <span class="lbl">Food Access</span>
              <span class="val font-semibold green-text">&uarr; 7.2%</span>
            </div>
            <div class="trend-item">
              <span class="icon-indicator red-dot"></span>
              <span class="lbl">Environmental Risk</span>
              <span class="val font-semibold red-text">&uarr; 9.1%</span>
            </div>
            <div class="trend-item">
              <span class="icon-indicator green-dot"></span>
              <span class="lbl">Healthcare Access</span>
              <span class="val font-semibold green-text">&uarr; 5.4%</span>
            </div>
          </div>
        </section>

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
  background: #f1f5f9;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  height: 600px;
  position: relative;
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

/* Patient Pin Marker */
:deep(.pulse-ring-leaflet) {
  position: absolute;
  top: -3px;
  left: -3px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: rgba(79, 70, 229, 0.4);
  animation: pulse-ring-anim 2s infinite ease-in-out;
}

@keyframes pulse-ring-anim {
  0% { transform: scale(0.6); opacity: 1; }
  100% { transform: scale(1.8); opacity: 0; }
}

/* Float Map Controls */
.map-controls {
  position: absolute;
  top: 16px;
  left: 16px;
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-sm);
  z-index: 1000;
}

.map-controls button {
  width: 30px;
  height: 30px;
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  cursor: pointer;
  border-bottom: 1px solid var(--border);
}

.map-controls button:last-child {
  border-bottom: none;
}

.map-controls button:hover {
  background: #f1f5f9;
  color: var(--text-primary);
}

/* Map legend */
.map-legend {
  position: absolute;
  bottom: 16px;
  left: 16px;
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 12px;
  box-shadow: var(--shadow-sm);
  z-index: 1000;
}

.legend-title {
  margin: 0 0 6px;
  font-size: 0.68rem;
  font-weight: 700;
  color: var(--text-primary);
  text-transform: uppercase;
}

.legend-title .light {
  color: var(--text-tertiary);
  font-weight: 500;
}

.legend-colors {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.legend-item {
  font-size: 0.65rem;
  font-weight: 600;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-item .color {
  width: 14px;
  height: 8px;
  border-radius: 2px;
  display: inline-block;
}

.legend-item .color.blue { background: #93c5fd; }
.legend-item .color.green { background: #86efac; }
.legend-item .color.yellow { background: #fde047; }
.legend-item .color.orange { background: #fed7aa; }
.legend-item .color.red { background: #fca5a5; }

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
