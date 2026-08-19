<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import IconBase from '../components/dashboard/IconBase.vue'
import FloatingChatbot from '../components/dashboard/FloatingChatbot.vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { isLoggedIn, setShowLoginScreen, isAnalyzed, patientData, mlPredictionResults, predictionModelResults } from '../store/appState'
import { SYSTEM_BACKEND_URL } from '../config'

const mapLayers = ['Health Risk', 'Social Vulnerability', 'Food Access', 'Environmental Risk', 'Healthcare Access']
const activeLayer = ref('Health Risk')
const microscopeSrc = ref(`/assets/microscope.gif?t=${Date.now()}`)

const showFiltersDropdown = ref(false)
const toggleFiltersDropdown = () => {
  showFiltersDropdown.value = !showFiltersDropdown.value
}
const selectLayer = (layer) => {
  activeLayer.value = layer
  showFiltersDropdown.value = false
}

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
    factors: [
      'High poverty rate in urban core',
      'Limited food access in east Cleveland',
      'Transportation barriers / transit deserts',
      'Environmental burden / industrial emissions'
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
    factors: [
      'Poverty rate exceeding state average',
      'Severe food desert coverage in Detroit',
      'Aging water infrastructure / lead concerns',
      'Air particulate matter from heavy transit'
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
    factors: [
      'Localized poverty pockets',
      'Limited grocery stores in center township',
      'Moderate public transit access limits',
      'Industrial landfill proximity risks'
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
    factors: [
      'Rapid suburbanization disparities',
      'Local income inequalities near universities',
      'Adequate medical services in core metro',
      'Localized ozone pollution warnings'
    ]
  }
}

const selectedId = ref('cuyahoga')
const selectedCommunity = computed(() => {
  return communities[selectedId.value]
})

const patientCommunity = computed(() => {
  const risk = mlPredictionResults.value?.risk_scores || { diabetes: 0.5, hypertension: 0.5, heart_disease: 0.5, asthma: 0.5 }
  const avgRisk = Object.values(risk).reduce((a, b) => a + b, 0) / Object.values(risk).length
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
    foodAccessLevel: hasPred ? (pred.scores.food_security > 0.6 ? 'High Risk' : 'Moderate') : 'High Risk',
    environmental: hasPred ? pred.scores.neighborhood_environment.toFixed(2) : '0.55',
    environmentalLevel: hasPred ? (pred.scores.neighborhood_environment > 0.6 ? 'High' : 'Moderate') : 'High',
    healthcareAccess: hasPred ? pred.scores.healthcare_access.toFixed(2) : '0.40',
    healthcareAccessLevel: hasPred ? (pred.scores.healthcare_access > 0.6 ? 'Moderate' : 'Low') : 'Moderate',
    equityScore: Math.round((1 - avgRisk) * 100),
    equityLevel: avgRisk > 0.7 ? 'Critical' : (avgRisk > 0.5 ? 'High Risk' : (avgRisk > 0.3 ? 'Moderate' : 'Low Risk')),
    center: [parseFloat(patientData.value.lat) || 41.4993, parseFloat(patientData.value.long) || -81.6944],
    bounds: [],
    factors: (mlPredictionResults.value?.sdoh_barriers && mlPredictionResults.value.sdoh_barriers.length > 0)
      ? mlPredictionResults.value.sdoh_barriers
      : [
          'Economic instability concerns',
          'Healthcare access limitations',
          'Transportation options shortage'
        ]
  }
})

// Compare metrics helper list
const sidebarCompareMetrics = computed(() => {
  const commA = isAnalyzed.value ? patientCommunity.value : selectedCommunity.value
  const commB = isAnalyzed.value ? selectedCommunity.value : (selectedId.value === 'marion' ? communities['cuyahoga'] : communities['marion'])
  
  const getMetrics = (comm) => {
    if (!comm) return { healthcare: 50, social: 50, economic: 50, food: 50, environmental: 50, healthOutcomes: 50 }
    if (comm.id === 'patient') {
      const pred = predictionModelResults.value
      const pScores = pred?.scores || {}
      const risk = mlPredictionResults.value?.risk_scores || { diabetes: 0.5, hypertension: 0.5, heart_disease: 0.5, asthma: 0.5 }
      const avgRisk = Object.values(risk).reduce((a, b) => a + b, 0) / Object.values(risk).length
      return {
        healthcare: pred ? Math.round((pScores.healthcare_access || 0.5) * 100) : 40,
        social: pred ? Math.round((pScores.social_context || 0.5) * 100) : 65,
        economic: pred ? Math.round((pScores.economic_stability || 0.5) * 100) : 55,
        food: pred ? Math.round((pScores.food_security || 0.5) * 100) : 35,
        environmental: pred ? Math.round((pScores.neighborhood_environment || 0.5) * 100) : 55,
        healthOutcomes: Math.round((1 - avgRisk) * 100)
      }
    }
    return {
      healthcare: Math.round(parseFloat(comm.healthcareAccess || 0.5) * 100),
      social: Math.round(parseFloat(comm.sviScore || 0.5) * 100),
      economic: Math.round((1 - parseFloat(comm.healthRisk || 0.5)) * 100),
      food: Math.round(parseFloat(comm.foodAccess || 0.5) * 100),
      environmental: Math.round(parseFloat(comm.environmental || 0.5) * 100),
      healthOutcomes: Math.round(parseFloat(comm.equityScore || 50))
    }
  }

  const metricsA = getMetrics(commA)
  const metricsB = getMetrics(commB)

  return [
    { label: 'Healthcare Access', a: metricsA.healthcare, b: metricsB.healthcare },
    { label: 'Social Stability', a: metricsA.social, b: metricsB.social },
    { label: 'Economic Stability', a: metricsA.economic, b: metricsB.economic },
    { label: 'Food Access', a: metricsA.food, b: metricsB.food },
    { label: 'Environmental Safety', a: metricsA.environmental, b: metricsB.environmental },
    { label: 'Health Outcomes', a: metricsA.healthOutcomes, b: metricsB.healthOutcomes }
  ]
})


const scoreDash = 2 * Math.PI * 34

// Leaflet Map State
let map = null
const polygonLayers = {}

// Helper to determine polygon color based on score and active layer
function getPolygonColor(communityId, layerName) {
  const comm = communities[communityId]
  let val = 0
  if (layerName === 'Health Risk') val = parseFloat(comm.healthRisk) * 100
  else if (layerName === 'Social Vulnerability') val = parseFloat(comm.sviScore) * 100
  else if (layerName === 'Food Access') val = parseFloat(comm.foodAccess) * 100
  else if (layerName === 'Environmental Risk') val = parseFloat(comm.environmental) * 100
  else if (layerName === 'Healthcare Access') val = parseFloat(comm.healthcareAccess) * 100

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

onMounted(() => {
  map = L.map('leaflet-overview-map', {
    zoomControl: false,
    attributionControl: false
  }).setView([41.1, -83.5], 6)

  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    maxZoom: 19
  }).addTo(map)

  // Draw boundaries
  Object.keys(communities).forEach(id => {
    const comm = communities[id]
    const polygon = L.polygon(comm.bounds, {
      fillColor: getPolygonColor(id, activeLayer.value),
      fillOpacity: 0.65,
      color: selectedId.value === id ? '#4f46e5' : '#ffffff',
      weight: selectedId.value === id ? 3 : 1.5
    }).addTo(map)

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

    const popupContent = `
      <div style="font-family: sans-serif; font-size: 11px; min-width: 140px;">
        <b style="font-size:12px; color:#1e293b;">${comm.name}</b><br/>
        <span style="color:#64748b;">Population: ${comm.population}</span><br/>
        <span style="color:#ef4444;">Health Risk: ${comm.healthRisk}</span>
      </div>
    `
    polygon.bindPopup(popupContent)
    polygonLayers[id] = polygon
  })

  // Fit boundaries nicely
  const allBounds = Object.values(communities).map(c => c.bounds)
  map.fitBounds(L.latLngBounds(allBounds.flat()), { padding: [15, 15] })

  drawPatientMarker()
})

onUnmounted(() => {
  if (map) {
    map.remove()
  }
})

let patientMarker = null

const drawPatientMarker = () => {
  if (!map || !isAnalyzed.value) return
  
  const coords = [parseFloat(patientData.value.lat) || 41.4993, parseFloat(patientData.value.long) || -81.6944]
  if (patientMarker) {
    map.removeLayer(patientMarker)
  }
  
  const hasPred = !!predictionModelResults.value
  const pred = predictionModelResults.value
  let popupText = `<b>${patientData.value.name}</b><br/>Individual Patient Residence`
  if (hasPred) {
    popupText += `<br/><b>Location:</b> ${pred.city}, ${pred.state}`
    popupText += `<br/><b>Overall Risk Score:</b> ${pred.overall_risk_category} (${pred.overall_risk_score.toFixed(2)})`
  }
  
  patientMarker = L.marker(coords).addTo(map)
    .bindPopup(popupText)
  
  map.panTo(coords)
  patientMarker.openPopup()
}

watch(isAnalyzed, (analyzed) => {
  if (analyzed) {
    drawPatientMarker()
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
    nextTick(() => {
      map.invalidateSize()
    })
  }
})

// Custom zoom/pan triggers
const zoomIn = () => {
  if (map) map.zoomIn()
}
const zoomOut = () => {
  if (map) map.zoomOut()
}
const resetMap = () => {
  if (map) {
    const allBounds = Object.values(communities).map(c => c.bounds)
    map.fitBounds(L.latLngBounds(allBounds.flat()), { padding: [15, 15] })
  }
}

// Consult AI Chat Assistant Panel State
const showConsultAI = ref(false)
const handleConsultClick = () => {
  if (!isLoggedIn.value) {
    setShowLoginScreen(true)
  } else {
    showConsultAI.value = true
  }
}
const chatInput = ref('')
const activeMode = ref('vibe')
const isAutopilot = ref(true)
const messages = ref([])
const isThinking = ref(false)

const quickSuggestions = [
  'Show Cuyahoga County risk factors',
  'Food access ideas for Wayne County',
  'What is SVI score of Marion County?'
]

const clickSuggestion = (suggest) => {
  chatInput.value = suggest
  handleSendMessage()
}

const formatMessageText = (text) => {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br/>')
}

const handleSendMessage = () => {
  const text = chatInput.value.trim()
  if (!text) return

  messages.value.push({ role: 'user', text })
  chatInput.value = ''
  isThinking.value = true

  // Auto scroll
  setTimeout(() => {
    const el = document.querySelector('.ai-chat-content')
    if (el) el.scrollTop = el.scrollHeight
  }, 50)

  // Try live FastAPI chat server first, fallback to mock simulation
  const chatUrl = `${SYSTEM_BACKEND_URL}/api/v1/chat?member_id=DEMO001`
  fetch(chatUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      role: 'user',
      content: text
    })
  })
  .then(r => {
    if (!r.ok) throw new Error('Live Chat API HTTP error: ' + r.status)
    return r.json()
  })
  .then(data => {
    isThinking.value = false
    const reply = data.response || 'No response received from agent.'
    messages.value.push({ role: 'assistant', text: reply })
    
    // Auto scroll
    setTimeout(() => {
      const el = document.querySelector('.ai-chat-content')
      if (el) el.scrollTop = el.scrollHeight
    }, 50)
  })
  .catch(err => {
    console.warn('Falling back to local simulated response:', err)
    
    isThinking.value = false
    let reply = ''
    const lower = text.toLowerCase()

    if (lower.includes('wayne')) {
      reply = 'In **Wayne County, MI**, the Health Equity Score is **48/100 (High Risk)**. Key driving factors: severe food deserts in Detroit, aging water infrastructure, and air quality concerns from heavy transit. Recommended intervention: Deploy mobile fresh food markets or outreach campaigns.'
    } else if (lower.includes('cuyahoga')) {
      reply = 'In **Cuyahoga County, OH**, the Health Equity Score is **64/100 (Moderate)**. Vulnerability drivers include poverty in the Cleveland urban core and east Cleveland transit deserts. Recommended resource expansion: Connect members with Cleveland Food Bank and regional health clinics.'
    } else if (lower.includes('marion')) {
      reply = 'In **Marion County, IN**, the Health Equity Score is **58/100 (Moderate)**. Factors include localized poverty pockets and Center Township food access limits. Recommended intervention: Target mobile screening clinics and food pantries.'
    } else if (lower.includes('franklin')) {
      reply = 'In **Franklin County, OH**, the Health Equity Score is **71/100**. Disparities are concentrated near student regions and the outer beltway. Environmental ozone warnings are active.'
    } else if (lower.includes('hello') || lower.includes('hi') || lower.includes('hey')) {
      reply = 'Hello! I am your **CareEquity AI Assistant**. I can help you analyze census-level social vulnerability indicators (SVI), plan clinical interventions, or write strategic county reports. How can I help you today?'
    } else {
      reply = `Thank you for consulting me! Regarding "${text}", I am currently analyzing the SVI dataset across Cuyahoga, Wayne, Marion, and Franklin counties. Please specify which county or risk factor you would like me to drill down into.`
    }

    messages.value.push({ role: 'assistant', text: reply })

    // Auto scroll
    setTimeout(() => {
      const el = document.querySelector('.ai-chat-content')
      if (el) el.scrollTop = el.scrollHeight
    }, 50)
  })
}
</script>

<template>
  <div class="overview-layout">
    <!-- Left Scrollable Area -->
    <div class="overview-main-content">
      <!-- Hero -->
      <section class="hero">
        <div class="hero-copy">
          <h1>Understanding the<br />conditions that shape health.</h1>
          <p>
            Connect member health data with social, environmental, and
            community factors to identify health risks and close health-equity gaps.
          </p>
          <div class="hero-actions">
            <button class="btn primary btn-consult-ai" @click="handleConsultClick" style="text-decoration: none; cursor: pointer;">
              <IconBase name="sparkle" :size="16" /> Consult AI
            </button>
            <router-link to="/equity-map" class="btn ghost" style="text-decoration: none;">
              <IconBase name="map" :size="16" /> View Equity Map
            </router-link>
          </div>
        </div>

        <div class="hero-art">
          <img src="/src/assets/hero-illustration.png" alt="Understanding conditions that shape health" class="hero-img" />
        </div>
      </section>
      
      <!-- Patient Specific Context Banner -->
      <section v-if="isAnalyzed" class="card active-patient-banner" style="background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%); color: white; border: none; display: flex; justify-content: space-between; align-items: center; padding: 18px 24px; box-shadow: 0 10px 25px rgba(59, 130, 246, 0.25); border-radius: 16px; margin-bottom: 24px;">
        <div style="display: flex; align-items: center; gap: 16px;">
          <div style="background: #ffffff; width: 42px; height: 42px; border-radius: 12px; display: flex; align-items: center; justify-content: center; padding: 4px; flex-shrink: 0; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <img :src="microscopeSrc" alt="AI Analysis" style="width: 34px; height: 34px; object-fit: contain;" />
          </div>
          <div>
            <h3 style="margin: 0; color: white; font-size: 1.1rem; font-weight: 700;">Active Patient: {{ patientData.name }} (Age {{ patientData.age }})</h3>
            <p style="margin: 4px 0 0; font-size: 0.85rem; opacity: 0.9; color: rgba(255,255,255,0.9);">
              Individual Risk Prediction & social determinants generated via CareEquity Predictive System.
            </p>
          </div>
        </div>
      </section>

      <!-- Map & Community details container -->
      <div class="map-section-wrapper">
        <div class="map-row">
          <article class="card map-card">
            <!-- Dropdown click-outside overlay -->
            <div v-if="showFiltersDropdown" class="dropdown-overlay" @click="showFiltersDropdown = false"></div>

            <div class="map-head">
              <div>
                <h3 class="font-bold">Health Equity Map</h3>
                <p>Explore social determinants and health risks by community</p>
              </div>
              <div class="filter-dropdown-container" style="position: relative; display: inline-block;">
                <button class="btn outline sm filter-trigger" @click="toggleFiltersDropdown" :class="{ 'btn-active': showFiltersDropdown }">
                  <IconBase name="filter" :size="14" /> Filters
                </button>
                
                <Transition name="fade">
                  <div v-if="showFiltersDropdown" class="filter-dropdown-menu">
                    <div class="dropdown-header">Select Map Layer</div>
                    <button
                      v-for="layer in mapLayers"
                      :key="layer"
                      class="dropdown-item"
                      :class="{ active: layer === activeLayer }"
                      @click="selectLayer(layer)"
                    >
                      <span class="status-indicator" :class="{ active: layer === activeLayer }"></span>
                      {{ layer }}
                    </button>
                  </div>
                </Transition>
              </div>
            </div>

            <div class="map-canvas">
              <!-- Custom zoom controls -->
              <div class="zoom-controls" style="z-index: 1000;">
                <button @click="zoomIn"><IconBase name="plus" :size="15" /></button>
                <button @click="zoomOut"><IconBase name="minus" :size="15" /></button>
                <button @click="resetMap"><IconBase name="locate" :size="15" /></button>
              </div>

              <!-- Leaflet Real Map Container -->
              <div id="leaflet-overview-map" style="width: 100%; height: 100%;"></div>
            </div>
          </article>

          <!-- Community details card -->
          <article class="card community-card" v-if="selectedCommunity">
            <div class="community-head">
              <div>
                <h4 class="font-bold" style="margin: 0;">{{ selectedCommunity.name }}</h4>
                <p v-if="selectedCommunity.state" style="margin: 2px 0 0; font-size: 0.7rem; color: var(--text-secondary); font-weight: bold;">{{ selectedCommunity.state }}</p>
              </div>
            </div>
            <p class="community-sub">Health Equity Score</p>

            <div class="score-row">
              <svg viewBox="0 0 80 80" class="gauge">
                <circle cx="40" cy="40" r="34" fill="none" stroke="#eef1f6" stroke-width="8" />
                <circle
                  cx="40"
                  cy="40"
                  r="34"
                  fill="none"
                  stroke="var(--brand)"
                  stroke-width="8"
                  stroke-linecap="round"
                  :stroke-dasharray="scoreDash"
                  :stroke-dashoffset="scoreDash * (1 - selectedCommunity.equityScore / 100)"
                  transform="rotate(-90 40 40)"
                />
                <text x="40" y="37" text-anchor="middle" font-size="18" font-weight="700" fill="var(--text-primary)">
                  {{ selectedCommunity.equityScore }}
                </text>
                <text x="40" y="50" text-anchor="middle" font-size="8" fill="var(--text-tertiary)">/100</text>
              </svg>
              <span class="pill block font-bold" :class="selectedCommunity.equityLevel.toLowerCase().replace(' ', '-')">
                {{ selectedCommunity.equityLevel }}
              </span>

              <div class="mini-stats">
                <div><span>Population</span><b>{{ selectedCommunity.population }}</b></div>
                <div><span>SVI Score</span><b>{{ selectedCommunity.sviScore }}</b> <em class="pill sm font-bold" :class="selectedCommunity.sviLevel.toLowerCase().replace(' ', '-')">{{ selectedCommunity.sviLevel }}</em></div>
                <div><span>Health Risk</span><b>{{ selectedCommunity.healthRisk }}</b> <em class="pill sm font-bold" :class="selectedCommunity.healthRiskLevel.toLowerCase().replace(' ', '-')">{{ selectedCommunity.healthRiskLevel }}</em></div>
              </div>
            </div>

            <div class="quick-insights">
              <p class="popup-label">Quick Insights</p>
              <p class="insight-text font-semibold">
                Elevated risk is driven by: {{ selectedCommunity.factors.join(', ') }}.
              </p>
              <router-link to="/equity-map" class="link-arrow font-bold">View Full Insights <IconBase name="chevron-right" :size="13" /></router-link>
            </div>

            <router-link to="/equity-map" class="btn primary block font-bold" style="text-decoration: none; text-align: center; justify-content: center;">
              View Community Details
            </router-link>
          </article>
        </div>

        <!-- AI insight strip -->
        <section class="card insight-strip">
          <div class="insight-main">
            <p class="insight-title"><IconBase name="sparkle" :size="16" /> AI-Powered Insight</p>
            <p class="insight-desc">
              Communities with high social vulnerability and limited food access have 2.3x higher
              risk of preventable hospitalizations.
            </p>
            <router-link to="/sdoh-insights" class="link-arrow font-bold">View Details <IconBase name="chevron-right" :size="13" /></router-link>
          </div>

          <div class="insight-metric">
            <p class="metric-label">Highest Risk Factor</p>
            <p class="metric-value">Housing Instability</p>
            <div class="metric-bar"><span style="width: 82%"></span></div>
            <p class="metric-caption">Impact Score <b>0.82</b></p>
          </div>

          <div class="insight-metric">
            <p class="metric-label">Rising Concern</p>
            <p class="metric-value">Food Insecurity</p>
            <p class="metric-trend up"><IconBase name="arrow-up" :size="12" /> Trend 18%</p>
          </div>

          <div class="insight-metric">
            <p class="metric-label">Opportunity Area</p>
            <p class="metric-value">Preventive Care Access</p>
            <p class="metric-caption">Potential Impact <b class="high-text">High</b></p>
          </div>
        </section>
      </div>
    </div>

    <!-- Right Column (Right Sidebar) -->
    <aside class="overview-right-sidebar">
      <div v-if="!showConsultAI" class="right-sidebar-scroll-container">
        <article class="card score-card" v-if="selectedCommunity">
          <p class="popup-label">{{ isAnalyzed ? 'Patient Health Score' : 'Health Equity Score' }}</p>
          <div class="score-big">
            <span class="num">{{ isAnalyzed ? patientCommunity.equityScore : selectedCommunity.equityScore }}</span><span class="denom">/100</span>
            <span class="pill font-bold" :class="(isAnalyzed ? patientCommunity.equityLevel : selectedCommunity.equityLevel).toLowerCase().replace(' ', '-')">
              {{ isAnalyzed ? patientCommunity.equityLevel : selectedCommunity.equityLevel }}
            </span>
          </div>
          <div class="gap-row">
            <span>{{ isAnalyzed ? 'Health Gap' : 'Equity Gap' }}</span>
            <b>{{ 100 - (isAnalyzed ? patientCommunity.equityScore : selectedCommunity.equityScore) }} pts</b>
          </div>
          <p class="gap-caption">vs. National Average</p>

          <!-- Personal Disease Risk Predictions (from ml/system) -->
          <div v-if="isAnalyzed && mlPredictionResults" class="personal-risk-section" style="margin-top: 16px; border-top: 1px solid var(--border); padding-top: 16px;">
            <p class="popup-label" style="margin-bottom: 12px; font-weight: bold; color: var(--text-primary);">Personal Health Predictions</p>
            <div style="display: flex; flex-direction: column; gap: 10px;">
              <div v-for="(val, disease) in mlPredictionResults.risk_scores" :key="disease" class="disease-risk-row">
                <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 4px;">
                  <span style="text-transform: capitalize; font-weight: 600; color: var(--text-secondary);">{{ disease.replace('_', ' ') }}</span>
                  <span style="font-weight: bold; color: var(--text-primary);">{{ Math.round(val * 100) }}%</span>
                </div>
                <div style="height: 6px; background-color: var(--border); border-radius: 3px; overflow: hidden; display: flex;">
                  <div :style="{ width: (val * 100) + '%', backgroundColor: val > 0.7 ? '#ef4444' : (val > 0.4 ? '#f59e0b' : '#10b981') }" style="height: 100%; border-radius: 3px;"></div>
                </div>
              </div>
            </div>
          </div>
        </article>

        <!-- Compare Communities Card -->
        <article class="card compare-card" v-if="selectedCommunity">
          <h4 class="font-bold">{{ isAnalyzed ? `Compare Patient vs. ${selectedCommunity.name}` : 'Compare Communities' }}</h4>
          <div class="compare-heads">
            <span class="compare-chip">{{ isAnalyzed ? (patientData.name || 'Patient') : selectedCommunity.name }}</span>
            <span class="vs">vs</span>
            <span class="compare-chip alt">{{ isAnalyzed ? selectedCommunity.name : (selectedId === 'marion' ? 'Cuyahoga County, OH' : 'Marion County, IN') }}</span>
          </div>

          <div class="compare-list">
            <div v-for="m in sidebarCompareMetrics" :key="m.label" class="compare-row">
              <p class="compare-row-title">{{ m.label }}</p>
              <div class="compare-row-flex">
                <span class="compare-val val-a">{{ m.a }}</span>
                <div class="compare-bar-container">
                  <div class="compare-bar-fill bar-a" :style="{ width: m.a + '%' }"></div>
                </div>
                <div class="compare-bar-container">
                  <div class="compare-bar-fill bar-b" :style="{ width: m.b + '%' }"></div>
                </div>
                <span class="compare-val val-b">{{ m.b }}</span>
              </div>
            </div>
          </div>
        </article>
      </div>

      <!-- Consult AI Chat Panel inside Right Sidebar -->
      <div v-else class="ai-sidebar-full">
        <!-- Header -->
        <div class="ai-header">
          <h3 style="margin: 0; font-size: 0.95rem; font-weight: 700; color: var(--text-primary);">Consult AI Assistant</h3>
          <button class="close-btn" @click="showConsultAI = false">
            <IconBase name="close" :size="16" />
          </button>
        </div>

        <!-- Chat Feed / Main Content -->
        <div class="ai-chat-content">
          <!-- Welcome Screen (Only shown when no messages) -->
          <div v-if="messages.length === 0" class="ai-welcome-container">
            <div class="ai-big-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
              </svg>
            </div>
            <h2>Consult AI</h2>
            <p>SDOH, SVI & Intervention Assistant</p>

            <div class="ai-mode-cards">
              <div class="mode-card" :class="{ active: activeMode === 'vibe' }" @click="activeMode = 'vibe'">
                <h4>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display:inline-block; vertical-align:middle;">
                    <circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line>
                  </svg>
                  Analyze SDOH
                </h4>
                <p>Explore social vulnerability and barriers.</p>
              </div>
              <div class="mode-card" :class="{ active: activeMode === 'spec' }" @click="activeMode = 'spec'">
                <h4>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display:inline-block; vertical-align:middle;">
                    <path d="M9 21h6M9 18h6M10 22h4M12 2a7 7 0 0 0-7 7c0 2.38 1.19 4.47 3 5.74V17c0 .55.45 1 1 1h6c.55 0 1-.45 1-1v-2.26c1.81-1.27 3-3.36 3-5.74a7 7 0 0 0-7-7z"></path>
                  </svg>
                  Suggest Actions
                </h4>
                <p>Generate clinical pathways & outreach plans.</p>
              </div>
            </div>

            <div class="great-for-box">
              <b>Great for:</b>
              <ul>
                <li>• Identifying community disparities</li>
                <li>• Targeting preventative care outreach</li>
                <li>• Recommending local support programs</li>
              </ul>
            </div>

            <!-- Quick Suggestion Pills -->
            <div class="ai-quick-suggestions">
              <button 
                v-for="suggest in quickSuggestions" 
                :key="suggest" 
                class="suggest-pill"
                @click="clickSuggestion(suggest)"
              >
                {{ suggest }}
              </button>
            </div>
          </div>

          <!-- Real Messages List -->
          <div v-else style="display: flex; flex-direction: column; gap: 14px; width: 100%;">
            <div 
              v-for="(msg, i) in messages" 
              :key="i" 
              class="chat-message" 
              :class="msg.role"
            >
              <div v-html="formatMessageText(msg.text)"></div>
            </div>
            <!-- Thinking loading indicator -->
            <div v-if="isThinking" class="chat-message assistant">
              <span>Thinking...</span>
            </div>
          </div>
        </div>

        <!-- Bottom Chat Input matches Gemini/Let's build interface -->
        <div class="ai-input-area">
          <div class="ai-input-container">
            <textarea 
              v-model="chatInput" 
              placeholder="Ask a question or describe a task..." 
              rows="2"
              @keydown.enter.prevent="handleSendMessage"
            ></textarea>
            <div class="ai-input-controls">
              <div class="ai-input-right-buttons" style="margin-left: auto;">
                <button class="send-msg-btn" @click="handleSendMessage" title="Submit question">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="display:inline-block; vertical-align:middle;">
                    <line x1="12" y1="19" x2="12" y2="5M5 12l7-7 7 7" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </aside>
    <FloatingChatbot />
  </div>
</template>

<style scoped>
.overview-layout {
  display: flex;
  height: 100%;
  overflow: hidden;
  background: var(--bg);
}

.overview-main-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px 28px 40px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.overview-right-sidebar {
  width: 400px;
  border-left: 1px solid var(--border);
  background: #ffffff;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  height: 100%;
}

.right-sidebar-scroll-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px 20px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  padding: 20px;
}

/* Hero */
.hero {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 24px;
  align-items: center;
  background: radial-gradient(circle at 80% 20%, #eef4ff 0%, #f7f9fd 55%, #ffffff 100%);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 36px 40px;
}

.hero-copy h1 {
  margin: 0 0 14px;
  font-size: clamp(1.8rem, 3.2vw, 2.4rem);
  line-height: 1.2;
  color: var(--text-primary);
  font-weight: 800;
}

.hero-copy p {
  margin: 0 0 24px;
  color: var(--text-secondary);
  font-size: 0.95rem;
  line-height: 1.6;
  max-width: 48ch;
}

.hero-actions {
  display: flex;
  gap: 12px;
}

.hero-art {
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-img {
  width: 100%;
  max-height: 240px;
  object-fit: contain;
  filter: drop-shadow(0 10px 20px rgba(47, 111, 237, 0.08));
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 11px 18px;
  border-radius: 11px;
  font-size: 0.86rem;
  font-weight: 600;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.btn.primary {
  background: var(--brand);
  color: #fff;
}
.btn.primary:hover {
  background: var(--brand-dark);
  transform: translateY(-1px);
}

.btn.ghost {
  background: #fff;
  color: var(--text-primary);
  border: 1px solid var(--border);
}
.btn.ghost:hover {
  background: #f7f9fc;
  border-color: #cbd5e1;
  transform: translateY(-1px);
}

.btn.outline {
  border: 1px solid var(--border);
  color: var(--text-secondary);
  background: #fff;
}
.btn.outline:hover {
  background: #f7f9fc;
  color: var(--text-primary);
}

.btn.sm {
  padding: 7px 12px;
  font-size: 0.78rem;
}

.btn.block {
  width: 100%;
  margin-top: 12px;
}

/* Map Section Wrapper */
.map-section-wrapper {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.map-row {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(280px, 1fr);
  gap: 24px;
}

.map-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.map-head h3 {
  margin: 0 0 4px;
  font-size: 1.05rem;
  font-weight: 700;
}

.map-head p {
  margin: 0;
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.map-tabs {
  display: flex;
  gap: 6px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.map-tab {
  padding: 7px 13px;
  border-radius: 999px;
  font-size: 0.76rem;
  font-weight: 600;
  color: var(--text-secondary);
  border: 1px solid var(--border);
  background: #fff;
  transition: all 0.15s ease;
  cursor: pointer;
}

.map-tab:hover {
  border-color: #cbd5e1;
  color: var(--text-primary);
}

.map-tab.active {
  background: var(--brand);
  color: #fff;
  border-color: var(--brand);
}

.map-card {
  display: flex;
  flex-direction: column;
}

.map-canvas {
  position: relative;
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 1px solid var(--border);
  flex: 1;
  min-height: 360px;
  background: #f8fafc;
}

.zoom-controls {
  position: absolute;
  top: 14px;
  left: 14px;
  display: flex;
  flex-direction: column;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid var(--border);
  background: #fff;
  box-shadow: var(--shadow-sm);
}

.zoom-controls button {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border);
  transition: background 0.15s ease, color 0.15s ease;
  border: none;
  background: transparent;
  cursor: pointer;
}
.zoom-controls button:hover {
  background: #f8fafc;
  color: var(--text-primary);
}
.zoom-controls button:last-child {
  border-bottom: none;
}

.pill {
  font-size: 0.62rem;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 999px;
  white-space: nowrap;
}
.pill.high, .pill.very-high, .pill.high-risk {
  background: var(--red-bg);
  color: var(--red-text);
}
.pill.moderate, .pill.mid, .pill.mod-high {
  background: var(--amber-bg);
  color: var(--amber-text);
}
.pill.block {
  display: inline-flex;
  margin-top: 8px;
}
.pill.sm {
  padding: 1px 6px;
}

.popup-label {
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-tertiary);
  margin: 0 0 8px;
}

/* Community card */
.community-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.community-head h4 {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
}

.btn-heart {
  color: var(--text-tertiary);
  transition: color 0.15s ease, transform 0.15s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  cursor: pointer;
}
.btn-heart:hover {
  color: var(--red);
  transform: scale(1.08);
}

.community-sub {
  margin: 2px 0 16px;
  font-size: 0.76rem;
  color: var(--text-secondary);
}

.score-row {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding-bottom: 16px;
  margin-bottom: 16px;
  border-bottom: 1px solid var(--border);
}

.gauge {
  width: 82px;
  height: 82px;
}

.mini-stats {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 10px;
  width: 100%;
  margin-top: 12px;
}

.mini-stats div {
  display: flex;
  flex-direction: column;
  gap: 3px;
  align-items: center;
  text-align: center;
}

.mini-stats span {
  font-size: 0.66rem;
  color: var(--text-secondary);
}

.mini-stats b {
  font-size: 0.82rem;
  color: var(--text-primary);
}

.quick-insights {
  margin-bottom: 8px;
}

.insight-text {
  font-size: 0.78rem;
  color: var(--text-secondary);
  line-height: 1.55;
  margin: 0 0 8px;
}

.link-arrow {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--brand);
  transition: gap 0.15s ease;
  text-decoration: none;
}
.link-arrow:hover {
  gap: 6px;
}

/* Insight strip */
.insight-strip {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) repeat(3, minmax(0, 1fr));
  gap: 24px;
  align-items: start;
}

.insight-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 8px;
  font-weight: 700;
  color: var(--brand-dark);
  font-size: 0.9rem;
}

.insight-desc {
  margin: 0 0 10px;
  font-size: 0.82rem;
  color: var(--text-secondary);
  line-height: 1.55;
}

.insight-metric {
  border-left: 1px solid var(--border);
  padding-left: 20px;
}

.metric-label {
  margin: 0 0 6px;
  font-size: 0.7rem;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-weight: 700;
}

.metric-value {
  margin: 0 0 8px;
  font-size: 0.92rem;
  font-weight: 700;
  color: var(--text-primary);
}

.metric-bar {
  height: 6px;
  border-radius: 999px;
  background: #eef1f6;
  overflow: hidden;
  margin-bottom: 6px;
}

.metric-bar span {
  display: block;
  height: 100%;
  background: var(--red);
  border-radius: 999px;
}

.metric-caption {
  font-size: 0.72rem;
  color: var(--text-secondary);
  margin: 0;
}

.metric-caption b {
  color: var(--text-primary);
}

.high-text {
  color: var(--red-text);
}

.metric-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.78rem;
  font-weight: 700;
  margin: 0;
}
.metric-trend.up {
  color: var(--teal);
}

/* Right Rail Action Card */
.action-card h4 {
  margin: 0 0 16px;
  font-size: 0.95rem;
  font-weight: 700;
}

.compare-card h4 {
  margin: 0 0 16px;
  font-size: 0.84rem;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.score-big {
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin: 6px 0 14px;
}

.score-big .num {
  font-size: 2.1rem;
  font-weight: 800;
  color: var(--amber-text);
}

.score-big .denom {
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.score-big .pill {
  margin-left: auto;
}

.gap-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.84rem;
  color: var(--text-secondary);
}

.gap-row b {
  color: var(--text-primary);
  font-size: 1.05rem;
}

.gap-caption {
  margin: 2px 0 0;
  font-size: 0.72rem;
  color: var(--text-tertiary);
}

.compare-heads {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 18px;
}

.compare-chip {
  flex: 1;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid #c7d9f7;
  background: #eaf1ff;
  color: var(--brand);
  font-size: 0.72rem;
  font-weight: 600;
  text-align: center;
}

.compare-chip.alt {
  background: #fef3c7;
  color: var(--amber-text);
  border-color: #fde047;
}

.vs {
  font-size: 0.7rem;
  color: var(--text-secondary);
}

.compare-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.compare-row-title {
  margin: 0 0 6px;
  font-size: 0.76rem;
  color: var(--text-primary);
  font-weight: 500;
}

.compare-row-flex {
  display: flex;
  align-items: center;
  gap: 8px;
}

.compare-val {
  font-size: 0.74rem;
  font-weight: 700;
  min-width: 20px;
}

.compare-val.val-a {
  color: var(--brand);
  text-align: right;
}

.compare-val.val-b {
  color: var(--amber-text);
  text-align: left;
}

.compare-bar-container {
  flex: 1;
  height: 8px;
  background: #eef1f6;
  border-radius: 999px;
  overflow: hidden;
}

.compare-bar-fill {
  height: 100%;
  border-radius: 999px;
}

.compare-bar-fill.bar-a {
  background: var(--brand);
  float: right;
}

.compare-bar-fill.bar-b {
  background: #f59e0b;
  float: left;
}

@media (max-width: 1100px) {
  .overview-layout {
    flex-direction: column;
    height: 100%;
    overflow-y: auto;
  }

  .overview-main-content {
    height: auto;
    overflow: visible;
    padding: 16px 20px;
    flex-shrink: 0;
  }

  .overview-right-sidebar {
    width: 100%;
    height: auto;
    border-left: none;
    border-top: 1px solid var(--border);
    flex-shrink: 0;
  }

  .right-sidebar-scroll-container {
    height: auto;
    overflow: visible;
    padding: 20px;
  }
}

@media (max-width: 900px) {
  .map-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .hero {
    grid-template-columns: 1fr;
    text-align: center;
    padding: 24px;
  }
  .hero-copy p {
    margin-left: auto;
    margin-right: auto;
  }
  .hero-actions {
    justify-content: center;
  }
  .insight-strip {
    grid-template-columns: 1fr;
  }
  .insight-metric {
    border-left: none;
    padding-left: 0;
    border-top: 1px solid var(--border);
    padding-top: 12px;
  }
}

/* AI Chat Sidebar Panel (Full Height) */
.ai-sidebar-full {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #ffffff;
  color: #1e293b;
  font-family: 'Inter', sans-serif;
  overflow: hidden;
}

.ai-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid #f1f5f9;
}

.ai-search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #64748b;
  font-size: 0.8rem;
}

.ai-header .close-btn {
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
}

.ai-header .close-btn:hover {
  background: #f1f5f9;
  color: var(--text-primary);
}

/* Chat Feed */
.ai-chat-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Welcome Page */
.ai-welcome-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  margin-top: auto;
  margin-bottom: auto;
}

.ai-big-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: linear-gradient(135deg, var(--brand) 0%, #3b82f6 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  color: #ffffff;
  box-shadow: 0 4px 20px rgba(37, 99, 235, 0.2);
}

.ai-welcome-container h2 {
  font-size: 1.5rem;
  font-weight: 800;
  margin: 0 0 6px 0;
  background: linear-gradient(135deg, var(--brand) 0%, #3b82f6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.ai-welcome-container p {
  font-size: 0.85rem;
  color: #64748b;
  margin: 0 0 24px 0;
}

.ai-mode-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  width: 100%;
  margin-bottom: 24px;
}

.mode-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 14px;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mode-card.active, .mode-card:hover {
  border-color: var(--brand);
  box-shadow: 0 0 12px rgba(37, 99, 235, 0.1);
}

.mode-card h4 {
  font-size: 0.85rem;
  font-weight: 700;
  margin: 0 0 6px 0;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 6px;
}

.mode-card p {
  font-size: 0.72rem;
  color: #64748b;
  margin: 0;
  line-height: 1.4;
}

.great-for-box {
  border-left: 2px solid var(--brand);
  padding-left: 12px;
  text-align: left;
  width: 100%;
  font-size: 0.8rem;
}

.great-for-box b {
  color: #1e293b;
  display: block;
  margin-bottom: 6px;
}

.great-for-box ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  color: #64748b;
}

/* Chat Messages */
.chat-message {
  display: flex;
  flex-direction: column;
  max-width: 85%;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 0.82rem;
  line-height: 1.5;
}

.chat-message.user {
  background: var(--brand);
  color: #ffffff;
  align-self: flex-end;
  border-bottom-right-radius: 2px;
}

.chat-message.assistant {
  background: #f8fafc;
  color: #1e293b;
  align-self: flex-start;
  border-bottom-left-radius: 2px;
  border: 1px solid #e2e8f0;
}

/* Input Area */
.ai-input-area {
  padding: 20px;
  border-top: 1px solid #f1f5f9;
  background: #ffffff;
}

.ai-input-container {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ai-input-container textarea {
  background: transparent;
  border: none;
  color: #1e293b;
  font-size: 0.82rem;
  resize: none;
  outline: none;
  font-family: inherit;
}

.ai-input-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.ai-input-left-buttons {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #64748b;
}

.ai-input-left-buttons button {
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 2px;
}

.ai-input-left-buttons button:hover {
  color: var(--brand);
}

.ai-input-right-buttons {
  display: flex;
  align-items: center;
  gap: 12px;
}

.autopilot-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.72rem;
  color: #64748b;
}

/* Toggle Switch Style */
.switch {
  position: relative;
  display: inline-block;
  width: 28px;
  height: 16px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0; left: 0; right: 0; bottom: 0;
  background-color: #cbd5e1;
  transition: .2s;
  border-radius: 16px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 12px;
  width: 12px;
  left: 2px;
  bottom: 2px;
  background-color: white;
  transition: .2s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: var(--brand);
}

input:checked + .slider:before {
  transform: translateX(12px);
}

.send-msg-btn {
  background: var(--brand);
  color: #ffffff;
  border: none;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s ease;
}

.send-msg-btn:hover {
  background: var(--brand-dark);
}

.ai-quick-suggestions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  margin-top: 24px;
}

.suggest-pill {
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 0.78rem;
  color: #475569;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 500;
}

.suggest-pill:hover {
  background: var(--brand-light);
  border-color: var(--brand);
  color: var(--brand-dark);
  transform: translateY(-1px);
}

/* ── FILTERS DROPDOWN ── */
.dropdown-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1090;
  background: transparent;
}

.filter-dropdown-container {
  z-index: 1100;
}

.filter-trigger {
  transition: all 0.15s ease;
}

.filter-trigger.btn-active {
  border-color: var(--brand);
  background: var(--brand-light);
  color: var(--brand-dark);
}

.filter-dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 6px;
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
  padding: 8px;
  min-width: 200px;
  z-index: 1100;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.dropdown-header {
  font-size: 0.68rem;
  font-weight: 700;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 6px 10px 4px;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 10px;
  border: none;
  background: none;
  border-radius: 8px;
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--text-primary);
  text-align: left;
  cursor: pointer;
  transition: all 0.15s ease;
}

.dropdown-item:hover {
  background: #f1f5f9;
}

.dropdown-item.active {
  background: rgba(79, 70, 229, 0.05);
  color: var(--brand);
  font-weight: 600;
}

.status-indicator {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: transparent;
}

.status-indicator.active {
  background: var(--brand);
}

/* ── BUTTON SPARKLE SPIN ON HOVER ── */
.btn-consult-ai:hover :deep(.icon) {
  animation: spin-slow 8s linear infinite;
  transform-origin: center;
}

@keyframes spin-slow {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
