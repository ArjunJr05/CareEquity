<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { Network } from 'vis-network/standalone'

const API_BASE = 'http://localhost:8002'

// State
const counties = ref([])
const selectedFips = ref('1001')
const searchInput = ref('1001')
const loading = ref(false)
const error = ref(null)

const overview = ref({
  county_name: 'Autauga County',
  state_abbr: 'AL',
  population: 58761,
  median_household_income: 68315,
  svi_overall: 0.2663
})

const graphData = ref(null)
const sdohBarriers = ref([])
const healthOutcomes = ref([])
const activeTab = ref('graph') // 'graph', 'sdoh', 'health'

const graphContainer = ref(null)
let networkInstance = null

// Zipcode map for instant lookup
const ZIP_TO_FIPS = {
  "36003": "1001", "36006": "1001", "36008": "1001", "36066": "1001", "36067": "1001",
  "36507": "1003", "36526": "1003", "36532": "1003", "36535": "1003", "36580": "1003",
  "90001": "6037", "90012": "6037", "90210": "6037", "90401": "6037", "91101": "6037",
  "94102": "6075", "94103": "6075", "94107": "6075", "94110": "6075",
  "30301": "13121", "30303": "13121", "30305": "13121", "30309": "13121",
  "10001": "36061", "10002": "36061", "10011": "36061", "10019": "36061",
  "33101": "12086", "33139": "12086", "33140": "12086",
  "60601": "17031", "60602": "17031", "60606": "17031",
  "77001": "48201", "77002": "48201", "77004": "48201",
  "98101": "53033", "98104": "53033", "98109": "53033",
}

// Fetch list of counties for dropdown
const fetchCounties = async () => {
  try {
    const res = await fetch(`${API_BASE}/api/counties`)
    if (res.ok) {
      counties.value = await res.json()
    }
  } catch (err) {
    console.warn('Could not load county list from API:', err)
  }
}

// Load county data
const loadCountyData = async (fips) => {
  loading.value = true
  error.value = null
  try {
    // Overview
    const resOverview = await fetch(`${API_BASE}/api/county/${fips}`)
    if (resOverview.ok) {
      overview.value = await resOverview.json()
    }

    // Graph (Fetch Top 5 Highest Risk Factors)
    const resGraph = await fetch(`${API_BASE}/api/county/${fips}/graph?top_k=5`)
    if (resGraph.ok) {
      graphData.value = await resGraph.json()
    }

    // SDoH Barriers
    const resSdoh = await fetch(`${API_BASE}/api/county/${fips}/sdoh`)
    if (resSdoh.ok) {
      sdohBarriers.value = await resSdoh.json()
    }

    // Health Outcomes
    const resHealth = await fetch(`${API_BASE}/api/county/${fips}/health-outcomes`)
    if (resHealth.ok) {
      healthOutcomes.value = await resHealth.json()
    }
  } catch (err) {
    error.value = 'Failed to fetch data from kg-backend server. Please check service status.'
    console.error(err)
  } finally {
    loading.value = false
    await nextTick()
    setTimeout(renderNetworkGraph, 100)
  }
}

// Render Pyvis / Vis-network Graph natively
const renderNetworkGraph = () => {
  if (!graphContainer.value || !graphData.value) return

  const nodes = graphData.value.nodes.map(n => ({
    id: n.id,
    label: n.label,
    color: {
      background: n.color,
      border: '#ffffff',
      highlight: { background: n.color, border: '#0f172a' }
    },
    size: n.size,
    font: { color: '#0f172a', size: 14, face: 'Inter, sans-serif', strokeWidth: 3, strokeColor: '#ffffff' },
    title: n.title
  }))

  const edges = graphData.value.edges.map(e => ({
    from: e.from,
    to: e.to,
    label: e.label,
    color: { color: e.color || '#94a3b8' },
    width: e.width || 2,
    dashes: e.dashes || false,
    font: { color: '#1e293b', size: 12, face: 'Inter, sans-serif', strokeWidth: 2, strokeColor: '#ffffff' }
  }))

  const data = { nodes, edges }

  const options = {
    nodes: {
      shape: 'dot',
      shadow: true
    },
    edges: {
      smooth: { type: 'continuous' }
    },
    physics: {
      solver: 'forceAtlas2Based',
      forceAtlas2Based: {
        gravitationalConstant: -50,
        centralGravity: 0.01,
        springLength: 100,
        springConstant: 0.08
      },
      stabilization: { iterations: 150 }
    },
    interaction: {
      hover: true,
      tooltipDelay: 100,
      zoomView: true
    }
  }

  if (networkInstance) {
    networkInstance.destroy()
  }

  networkInstance = new Network(graphContainer.value, data, options)
  networkInstance.once('stabilizationIterationsDone', () => {
    networkInstance.fit()
  })
  setTimeout(() => {
    if (networkInstance) networkInstance.fit()
  }, 400)
}

// Handlers
const handleSearchInput = () => {
  const val = searchInput.value.trim()
  if (ZIP_TO_FIPS[val]) {
    selectedFips.value = ZIP_TO_FIPS[val]
  } else if (val.length >= 4) {
    selectedFips.value = val
  }
}

const handleSelectChange = () => {
  searchInput.value = selectedFips.value
}

watch(selectedFips, (newFips) => {
  loadCountyData(newFips)
})

watch(activeTab, (newTab) => {
  if (newTab === 'graph') {
    nextTick(() => {
      setTimeout(renderNetworkGraph, 100)
    })
  }
})

onMounted(() => {
  fetchCounties()
  loadCountyData(selectedFips.value)
})
</script>

<template>
  <div class="sdoh-insights-native">
    <!-- Top Header -->
    <header class="header-section">
      <div class="header-titles">
        <h2>SDoH Knowledge Graph Insights</h2>
        <p>Direct Native Vue.js Interface connected to FastAPI & Neo4j Aura</p>
      </div>

      <!-- Controls Row: Select + Action -->
      <div class="search-controls-bar">
        <div class="control-group flex-2">
          <label>Select County by Name, FIPS, or Zipcode:</label>
          <select 
            v-model="selectedFips" 
            @change="handleSelectChange"
            class="select-field"
          >
            <option 
              v-for="c in counties" 
              :key="c.fips" 
              :value="c.fips"
            >
              {{ c.display_label }}
            </option>
            <option v-if="!counties.length" value="1001">Autauga County, AL (1001)</option>
          </select>
        </div>

        <button @click="loadCountyData(selectedFips)" class="btn-analyze">
          Analyze Graph
        </button>
      </div>
    </header>

    <!-- Main Content Container -->
    <div class="main-body">
      <!-- Error Alert -->
      <div v-if="error" class="error-card">
        <span class="icon">⚠️</span>
        <p>{{ error }}</p>
        <button @click="loadCountyData(selectedFips)" class="btn-retry">Retry Connection</button>
      </div>

      <!-- Overview KPI Cards -->
      <div v-else class="kpi-grid">
        <div class="kpi-card">
          <span class="lbl">County Name</span>
          <span class="val">{{ overview.county_name }}</span>
        </div>
        <div class="kpi-card">
          <span class="lbl">State</span>
          <span class="val">{{ overview.state_abbr }}</span>
        </div>
        <div class="kpi-card">
          <span class="lbl">Population</span>
          <span class="val">{{ overview.population ? overview.population.toLocaleString() : 'N/A' }}</span>
        </div>
        <div class="kpi-card">
          <span class="lbl">Median Income</span>
          <span class="val">{{ overview.median_household_income ? '$' + overview.median_household_income.toLocaleString() : 'N/A' }}</span>
        </div>
        <div class="kpi-card">
          <span class="lbl">SVI Score (Overall)</span>
          <span class="val highlight">{{ overview.svi_overall ? overview.svi_overall.toFixed(4) : 'N/A' }}</span>
        </div>
      </div>

      <!-- Section 1: Interactive Knowledge Graph (Always Visible On Top) -->
      <div class="section-pane">
        <div class="graph-card">
          <div class="graph-header">
            <h3>🕸️ Interactive Knowledge Graph</h3>
            <p>Clean radial graph showing central County node connected to its State and SDoH risk features (Neo4j Aura)</p>
          </div>
          <div v-if="loading" class="graph-loading">
            <div class="spinner"></div>
            <span>Querying Neo4j Aura Database...</span>
          </div>
          <div ref="graphContainer" class="vis-canvas"></div>
        </div>
      </div>

      <!-- Section 2: Side-by-Side Data Tables Below Graph -->
      <div class="tables-grid">
        <!-- SDoH Socioeconomic Risk Factors -->
        <div class="data-table-card">
          <div class="table-card-header">
            <h3>📊 SDoH Risk Factors</h3>
            <p>County-level socioeconomic drivers vs. US National average</p>
          </div>
          <table class="custom-table">
            <thead>
              <tr>
                <th>Factor Name</th>
                <th>County Value</th>
                <th>National Avg</th>
                <th>Difference</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in sdohBarriers" :key="item.factor_name">
                <td class="font-bold">{{ item.factor_name }}</td>
                <td>{{ item.county_value }} {{ item.unit }}</td>
                <td>{{ item.us_avg }} {{ item.unit }}</td>
                <td :class="item.difference > 0 ? 'text-red' : 'text-green'">
                  {{ item.difference > 0 ? '+' : '' }}{{ item.difference }} {{ item.unit }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Health Outcomes -->
        <div class="data-table-card">
          <div class="table-card-header">
            <h3>🩺 Health Outcomes</h3>
            <p>Chronic condition prevalence vs. US National average</p>
          </div>
          <table class="custom-table">
            <thead>
              <tr>
                <th>Condition Name</th>
                <th>County Prevalence (%)</th>
                <th>National Avg (%)</th>
                <th>Difference</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in healthOutcomes" :key="item.condition_name">
                <td class="font-bold">{{ item.condition_name }}</td>
                <td>{{ item.county_prevalence }}%</td>
                <td>{{ item.us_avg }}%</td>
                <td :class="item.difference > 0 ? 'text-red' : 'text-green'">
                  {{ item.difference > 0 ? '+' : '' }}{{ item.difference }}%
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sdoh-insights-native {
  display: flex;
  flex-direction: column;
  width: 100%;
  flex: 1;
  overflow-y: auto;
  background: var(--bg);
  color: var(--text-primary);
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  padding: 24px 32px 60px;
  box-sizing: border-box;
}

.header-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
}

.header-titles h2 {
  margin: 0 0 4px;
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--text-primary);
}

.header-titles p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.search-controls-bar {
  display: flex;
  align-items: flex-end;
  gap: 16px;
  background: var(--surface);
  padding: 20px 24px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.control-group.flex-2 {
  flex: 2;
}

.control-group label {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-primary);
}

.input-field, .select-field {
  background: #f8fafc;
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 11px 14px;
  color: var(--text-primary);
  font-size: 0.9rem;
  outline: none;
  transition: all 0.2s ease;
}

.input-field:focus, .select-field:focus {
  border-color: var(--brand);
  background: #ffffff;
  box-shadow: 0 0 0 3px rgba(47, 111, 237, 0.12);
}

.btn-analyze {
  background: var(--brand);
  color: #ffffff;
  border: none;
  padding: 12px 26px;
  border-radius: 10px;
  font-weight: 700;
  font-size: 0.9rem;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(47, 111, 237, 0.25);
  transition: all 0.2s ease;
}

.btn-analyze:hover {
  background: var(--brand-dark);
  transform: translateY(-1px);
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.kpi-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  box-shadow: var(--shadow-sm);
}

.kpi-card .lbl {
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.kpi-card .val {
  font-size: 1.35rem;
  font-weight: 800;
  color: var(--text-primary);
}

.kpi-card .val.highlight {
  color: var(--amber-text);
  background: var(--amber-bg);
  padding: 2px 8px;
  border-radius: 6px;
  align-self: flex-start;
}

.section-pane {
  margin-bottom: 24px;
}

.tables-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
  margin-bottom: 32px;
}

.table-card-header h3 {
  margin: 0 0 4px;
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--text-primary);
}

.table-card-header p {
  margin: 0 0 16px;
  color: var(--text-secondary);
  font-size: 0.85rem;
}

@media (max-width: 1024px) {
  .tables-grid {
    grid-template-columns: 1fr;
  }
}

.graph-card, .data-table-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 24px;
  box-shadow: var(--shadow-sm);
}

.graph-header h3, .data-table-card h3 {
  margin: 0 0 4px;
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--text-primary);
}

.graph-header p {
  margin: 0 0 18px;
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.vis-canvas {
  width: 100%;
  height: 520px;
  background: #f8fafc;
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
}

.custom-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 12px;
}

.custom-table th, .custom-table td {
  padding: 14px 18px;
  text-align: left;
  border-bottom: 1px solid var(--border);
  font-size: 0.9rem;
}

.custom-table th {
  color: var(--text-secondary);
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.custom-table tbody tr:hover {
  background-color: #f8fafc;
}

.font-bold { font-weight: 700; color: var(--text-primary); }
.text-red { color: var(--red-text); font-weight: 700; }
.text-green { color: var(--teal); font-weight: 700; }

.error-card {
  background: var(--red-bg);
  border: 1px solid var(--red-soft);
  color: var(--red-text);
  padding: 24px;
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.btn-retry {
  background: var(--brand);
  color: #ffffff;
  border: none;
  padding: 8px 18px;
  border-radius: 8px;
  font-weight: 700;
  cursor: pointer;
}
</style>
