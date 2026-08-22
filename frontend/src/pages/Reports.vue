<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import IconBase from '../components/dashboard/IconBase.vue'
import { isLoggedIn, setShowLoginScreen, isAnalyzed, patientData, mlPredictionResults, ocrExtractedJson, mlInputPayload, agentReport, isAgentLoading, userPlan } from '../store/appState'

import { MAIN_BACKEND_URL } from '../config'


const router = useRouter()

// Agent Tab state
const activeAgentTab = ref('care_plan')

// Format raw LLM Markdown report into structured, clean HTML
const formatAgentReport = (text) => {
  if (!text) return ''
  let formatted = text
    .replace(/^#\s+(.*$)/gim, '<h3 style="font-size: 1.1rem; font-weight: 800; color: #0f172a; margin: 12px 0 8px 0;">$1</h3>')
    .replace(/^##\s+(.*$)/gim, '<h4 style="font-size: 1.0rem; font-weight: 700; color: #0f766e; margin: 10px 0 6px 0;">$1</h4>')
    .replace(/^###\s+(.*$)/gim, '<h5 style="font-size: 0.92rem; font-weight: 700; color: #1e293b; margin: 8px 0 4px 0;">$1</h5>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.*?)`/g, '<code style="background: #e2e8f0; color: #0f172a; padding: 2px 6px; border-radius: 4px; font-weight: 600; font-family: monospace;">$1</code>')
    .replace(/^---\s*$/gim, '<hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 12px 0;"/>')
    .replace(/^\*\s+(.*$)/gim, '<li style="margin-bottom: 4px;">$1</li>')
    .replace(/^-\s+(.*$)/gim, '<li style="margin-bottom: 4px;">$1</li>')

  return formatted
}

// Active configuration state


const activeGeography = ref('Cuyahoga County, OH')
const activePopulation = ref('All Populations')
const activeDateRange = ref('May 1 – May 31, 2025')
const selectedSDOHCount = ref(8)
const selectedOutcomesCount = ref(6)

// Report Generation state
const isGenerating = ref(false)
const toastMsg = ref('')
const showToast = ref(false)

function triggerToast(msg) {
  toastMsg.value = msg
  showToast.value = true
  setTimeout(() => {
    showToast.value = false
  }, 3000)
}

// Mock Data for report previews by geography
const reportTemplatesData = {
  'Cuyahoga County, OH': {
    title: 'Health Equity Summary Report',
    completedDate: 'Cuyahoga County, OH &bull; May 1 – May 31, 2025',
    equityScore: 64,
    equityLabel: 'Moderate',
    population: '1.25M',
    popTrend: '↑ 12.4% vs previous 30 days',
    highRiskPop: '412K',
    highRiskPct: '16.6% of population',
    equityGap: '28 pts',
    interventions: 48,
    domains: [
      { name: 'Healthcare Access', score: 58, color: '#3b82f6' },
      { name: 'Social Stability', score: 72, color: '#10b981' },
      { name: 'Economic Stability', score: 60, color: '#eab308' },
      { name: 'Food Access', score: 43, color: '#f97316' },
      { name: 'Environmental Safety', score: 70, color: '#14b8a6' },
      { name: 'Health Outcomes', score: 68, color: '#8b5cf6' }
    ],
    riskDistribution: [
      { label: 'Low (0 - 25)', pct: '45.2%', color: '#10b981' },
      { label: 'Moderate (26 - 50)', pct: '31.5%', color: '#eab308' },
      { label: 'High (51 - 75)', pct: '16.6%', color: '#f97316' },
      { label: 'Critical (76 - 100)', pct: '6.7%', color: '#ef4444' }
    ],
    riskDistributionCounts: { low: 45.2, mod: 31.5, high: 16.6, crit: 6.7 },
    drivers: [
      { name: 'Housing Instability', score: 0.82, color: '#3b82f6' },
      { name: 'Food Insecurity', score: 0.74, color: '#10b981' },
      { name: 'Transportation Barriers', score: 0.68, color: '#8b5cf6' },
      { name: 'Environmental Exposure', score: 0.52, color: '#f97316' },
      { name: 'Healthcare Accessibility', score: 0.47, color: '#ef4444' }
    ],
    tableAreas: [
      { name: 'Cuyahoga County, OH', score: 0.72, svi: 0.78, pop: '1.25M' },
      { name: 'Mahoning County, OH', score: 0.66, svi: 0.71, pop: '312K' },
      { name: 'Summit County, OH', score: 0.63, svi: 0.69, pop: '205K' },
      { name: 'Lorain County, OH', score: 0.61, svi: 0.66, pop: '198K' },
      { name: 'Lake County, OH', score: 0.58, svi: 0.64, pop: '184K' }
    ],
    correlation: 0.63,
    correlationLabel: 'Positive correlation',
    scatterDots: [
      { x: 30, y: 110 }, { x: 50, y: 100 }, { x: 80, y: 90 }, { x: 120, y: 85 }, { x: 160, y: 80 },
      { x: 190, y: 70 }, { x: 210, y: 65 }, { x: 240, y: 55 }, { x: 280, y: 45 }, { x: 310, y: 40 },
      { x: 45, y: 112 }, { x: 90, y: 95 }, { x: 140, y: 88 }, { x: 175, y: 75 }, { x: 220, y: 60 }
    ]
  },
  'Wayne County, MI': {
    title: 'Population Risk Profile Report',
    completedDate: 'Wayne County, MI &bull; May 1 – May 31, 2025',
    equityScore: 52,
    equityLabel: 'Moderate',
    population: '1.75M',
    popTrend: '↑ 14.8% vs previous 30 days',
    highRiskPop: '680K',
    highRiskPct: '38.8% of population',
    equityGap: '36 pts',
    interventions: 56,
    domains: [
      { name: 'Healthcare Access', score: 48, color: '#3b82f6' },
      { name: 'Social Stability', score: 61, color: '#10b981' },
      { name: 'Economic Stability', score: 49, color: '#eab308' },
      { name: 'Food Access', score: 38, color: '#f97316' },
      { name: 'Environmental Safety', score: 58, color: '#14b8a6' },
      { name: 'Health Outcomes', score: 54, color: '#8b5cf6' }
    ],
    riskDistribution: [
      { label: 'Low (0 - 25)', pct: '35.2%', color: '#10b981' },
      { label: 'Moderate (26 - 50)', pct: '26.0%', color: '#eab308' },
      { label: 'High (51 - 75)', pct: '27.8%', color: '#f97316' },
      { label: 'Critical (76 - 100)', pct: '11.0%', color: '#ef4444' }
    ],
    riskDistributionCounts: { low: 35.2, mod: 26.0, high: 27.8, crit: 11.0 },
    drivers: [
      { name: 'Food Insecurity', score: 0.88, color: '#3b82f6' },
      { name: 'Housing Instability', score: 0.84, color: '#10b981' },
      { name: 'Transportation Barriers', score: 0.76, color: '#8b5cf6' },
      { name: 'Economic Gaps', score: 0.72, color: '#f97316' },
      { name: 'Primary Care Shortage', score: 0.65, color: '#ef4444' }
    ],
    tableAreas: [
      { name: 'Wayne County, MI', score: 0.81, svi: 0.86, pop: '1.75M' },
      { name: 'Macomb County, MI', score: 0.56, svi: 0.52, pop: '860K' },
      { name: 'Genesee County, MI', score: 0.74, svi: 0.79, pop: '405K' },
      { name: 'Oakland County, MI', score: 0.42, svi: 0.38, pop: '1.20M' },
      { name: 'Washtenaw County, MI', score: 0.38, svi: 0.34, pop: '365K' }
    ],
    correlation: 0.72,
    correlationLabel: 'Strong correlation',
    scatterDots: [
      { x: 30, y: 120 }, { x: 60, y: 110 }, { x: 90, y: 95 }, { x: 130, y: 90 }, { x: 170, y: 78 },
      { x: 200, y: 65 }, { x: 230, y: 55 }, { x: 260, y: 48 }, { x: 290, y: 35 }, { x: 320, y: 25 },
      { x: 50, y: 118 }, { x: 100, y: 102 }, { x: 150, y: 84 }, { x: 180, y: 70 }, { x: 240, y: 50 }
    ]
  },
  'Marion County, IN': {
    title: 'Community Health Profile',
    completedDate: 'Marion County, IN &bull; May 1 – May 31, 2025',
    equityScore: 71,
    equityLabel: 'Moderate',
    population: '960K',
    popTrend: '↑ 11.2% vs previous 30 days',
    highRiskPop: '240K',
    highRiskPct: '25.0% of population',
    equityGap: '21 pts',
    interventions: 32,
    domains: [
      { name: 'Healthcare Access', score: 74, color: '#3b82f6' },
      { name: 'Social Stability', score: 78, color: '#10b981' },
      { name: 'Economic Stability', score: 69, color: '#eab308' },
      { name: 'Food Access', score: 62, color: '#f97316' },
      { name: 'Environmental Safety', score: 73, color: '#14b8a6' },
      { name: 'Health Outcomes', score: 70, color: '#8b5cf6' }
    ],
    riskDistribution: [
      { label: 'Low (0 - 25)', pct: '52.0%', color: '#10b981' },
      { label: 'Moderate (26 - 50)', pct: '23.0%', color: '#eab308' },
      { label: 'High (51 - 75)', pct: '18.0%', color: '#f97316' },
      { label: 'Critical (76 - 100)', pct: '7.0%', color: '#ef4444' }
    ],
    riskDistributionCounts: { low: 52.0, mod: 23.0, high: 18.0, crit: 7.0 },
    drivers: [
      { name: 'Transit Impediments', score: 0.65, color: '#3b82f6' },
      { name: 'Food Access', score: 0.58, color: '#10b981' },
      { name: 'Housing Cost', score: 0.52, color: '#8b5cf6' }
    ],
    tableAreas: [
      { name: 'Marion County, IN', score: 0.64, svi: 0.68, pop: '960K' },
      { name: 'Hamilton County, IN', score: 0.28, svi: 0.22, pop: '350K' },
      { name: 'Hendricks County, IN', score: 0.32, svi: 0.26, pop: '175K' }
    ],
    correlation: 0.58,
    correlationLabel: 'Moderate correlation',
    scatterDots: [
      { x: 30, y: 100 }, { x: 70, y: 92 }, { x: 110, y: 88 }, { x: 150, y: 78 }, { x: 200, y: 72 },
      { x: 230, y: 62 }, { x: 260, y: 58 }, { x: 280, y: 52 }, { x: 310, y: 44 }
    ]
  },
  'Franklin County, OH': {
    title: 'Executive Strategic Report',
    completedDate: 'Franklin County, OH &bull; May 1 – May 31, 2025',
    equityScore: 68,
    equityLabel: 'Moderate',
    population: '1.32M',
    popTrend: '↑ 12.8% vs previous 30 days',
    highRiskPop: '360K',
    highRiskPct: '27.2% of population',
    equityGap: '24 pts',
    interventions: 38,
    domains: [
      { name: 'Healthcare Access', score: 68, color: '#3b82f6' },
      { name: 'Social Stability', score: 71, color: '#10b981' },
      { name: 'Economic Stability', score: 65, color: '#eab308' },
      { name: 'Food Access', score: 54, color: '#f97316' },
      { name: 'Environmental Safety', score: 68, color: '#14b8a6' },
      { name: 'Health Outcomes', score: 66, color: '#8b5cf6' }
    ],
    riskDistribution: [
      { label: 'Low (0 - 25)', pct: '47.0%', color: '#10b981' },
      { label: 'Moderate (26 - 50)', pct: '25.8%', color: '#eab308' },
      { label: 'High (51 - 75)', pct: '21.0%', color: '#f97316' },
      { label: 'Critical (76 - 100)', pct: '6.2%', color: '#ef4444' }
    ],
    riskDistributionCounts: { low: 47.0, mod: 25.8, high: 21.0, crit: 6.2 },
    drivers: [
      { name: 'Rent Burden', score: 0.70, color: '#3b82f6' },
      { name: 'Air Pollution Index', score: 0.62, color: '#10b981' },
      { name: 'Diabetic Complications', score: 0.58, color: '#8b5cf6' }
    ],
    tableAreas: [
      { name: 'Franklin County, OH', score: 0.62, svi: 0.66, pop: '1.32M' },
      { name: 'Delaware County, OH', score: 0.25, svi: 0.18, pop: '220K' },
      { name: 'Licking County, OH', score: 0.44, svi: 0.41, pop: '180K' }
    ],
    correlation: 0.61,
    correlationLabel: 'Positive correlation',
    scatterDots: [
      { x: 30, y: 105 }, { x: 60, y: 98 }, { x: 100, y: 92 }, { x: 140, y: 84 }, { x: 180, y: 76 },
      { x: 210, y: 68 }, { x: 240, y: 58 }, { x: 270, y: 50 }, { x: 300, y: 45 }
    ]
  }
}

const activeReportData = computed(() => {
  if (isAnalyzed.value && activeGeography.value === 'Active Patient' && mlPredictionResults.value) {
    const risk = mlPredictionResults.value.risk_scores || { diabetes: 0.5, hypertension: 0.5, heart_disease: 0.5, asthma: 0.5 }
    const avgRisk = Object.values(risk).reduce((a, b) => a + b, 0) / Object.values(risk).length
    const pctHigh = Math.round(avgRisk * 100)
    
    return {
      title: 'Individual Patient Health Risk Assessment',
      completedDate: `${patientData.value.name} &bull; Individual Report`,
      equityScore: Math.round((1 - avgRisk) * 100),
      equityLabel: avgRisk > 0.7 ? 'Critical Risk' : (avgRisk > 0.5 ? 'High Risk' : 'Moderate'),
      population: '1 (Individual)',
      popTrend: 'N/A',
      highRiskPop: '1 Active Patient',
      highRiskPct: `${pctHigh}% Clinical Risk Index`,
      equityGap: `${Math.round(avgRisk * 100)} pts`,
      interventions: mlPredictionResults.value.sdoh_barriers?.length || 3,
      domains: [
        { name: 'Diabetes Risk', score: Math.round((risk.diabetes || 0.5) * 100), color: '#3b82f6' },
        { name: 'Hypertension Risk', score: Math.round((risk.hypertension || 0.5) * 100), color: '#10b981' },
        { name: 'Heart Disease Risk', score: Math.round((risk.heart_disease || 0.5) * 100), color: '#eab308' },
        { name: 'Asthma Risk', score: Math.round((risk.asthma || 0.5) * 100), color: '#f97316' }
      ],
      riskDistribution: [
        { label: 'Diabetes', pct: `${Math.round((risk.diabetes || 0) * 100)}%`, color: '#ef4444' },
        { label: 'Hypertension', pct: `${Math.round((risk.hypertension || 0) * 100)}%`, color: '#f97316' },
        { label: 'Heart Disease', pct: `${Math.round((risk.heart_disease || 0) * 100)}%`, color: '#eab308' },
        { label: 'Asthma', pct: `${Math.round((risk.asthma || 0) * 100)}%`, color: '#3b82f6' }
      ],
      riskDistributionCounts: { low: 25, mod: 25, high: 25, crit: 25 },
      drivers: ((mlPredictionResults.value.sdoh_barriers && mlPredictionResults.value.sdoh_barriers.length > 0)
        ? mlPredictionResults.value.sdoh_barriers
        : [
            'High economic stability concerns',
            'Limited access to primary care providers',
            'Transportation accessibility limits'
          ]).map((barrier, index) => ({
        name: barrier,
        score: 0.85 - index * 0.1,
        color: ['#8b5cf6', '#10b981', '#f97316', '#3b82f6', '#ef4444'][index % 5]
      })),
      tableAreas: [
        { name: `${patientData.value.name} (Patient)`, score: avgRisk.toFixed(2), svi: 0.65, pop: '1' },
        { name: patientData.value.locations && patientData.value.locations[0] ? `${patientData.value.locations[0].county} (County Avg)` : 'Bronx County (County Avg)', score: (avgRisk * 0.85).toFixed(2), svi: 0.58, pop: '1.4M' },
        { name: 'Metro Health District', score: (avgRisk * 0.72).toFixed(2), svi: 0.52, pop: '850K' },
        { name: 'State Baseline Average', score: '0.38', svi: 0.42, pop: '11.7M' },
        { name: 'National Health Target', score: '0.25', svi: 0.30, pop: '330M' }
      ],
      correlation: 0.78,
      correlationLabel: 'Strong SDOH-Outcome Correlation',
      scatterDots: [
        { x: 45, y: 110 },
        { x: 80, y: 102 },
        { x: 120, y: 90 },
        { x: 165, y: 78 },
        { x: 210, y: 65 },
        { x: 255, y: 52 },
        { x: 295, y: 38 },
        { x: Math.round(0.65 * 280) + 30, y: Math.round((1 - avgRisk) * 100) + 20 }
      ]
    }
  }
  return reportTemplatesData[activeGeography.value] || reportTemplatesData['Cuyahoga County, OH']
})

const domainSegments = computed(() => {
  const list = activeReportData.value.domains || []
  const total = list.reduce((sum, d) => sum + d.score, 0)
  if (total === 0) return []
  
  let accumulated = 0
  return list.map(d => {
    const value = (d.score / total) * 238
    const offset = -accumulated
    accumulated += value
    return {
      name: d.name,
      color: d.color,
      dashArray: `${value} 238`,
      dashOffset: offset
    }
  })
})

const riskSegments = computed(() => {
  const list = activeReportData.value.riskDistribution || []
  const total = list.reduce((sum, r) => sum + parseFloat(r.pct), 0)
  if (total === 0) return []
  
  let accumulated = 0
  return list.map(r => {
    const val = parseFloat(r.pct)
    const value = (val / total) * 238
    const offset = -accumulated
    accumulated += value
    return {
      label: r.label,
      color: r.color,
      dashArray: `${value} 238`,
      dashOffset: offset
    }
  })
})

function handleSavedReportsClick() {
  if (!isLoggedIn.value) {
    setShowLoginScreen(true)
    return
  }
  triggerToast('Downloading the report...')
}

// Triggering report generation animation
function generateReport() {
  if (!isLoggedIn.value) {
    setShowLoginScreen(true)
    return
  }
  isGenerating.value = true
  triggerToast('Downloading the report...')
  setTimeout(() => {
    isGenerating.value = false
    triggerToast('Report generated successfully!')
  }, 1200)
}

// Select preset template
function selectTemplate(geographyName) {
  if (!isLoggedIn.value) {
    setShowLoginScreen(true)
    return
  }
  activeGeography.value = geographyName
  generateReport()
}

// Local resources state for reports
const scrapedResources = ref([])

async function fetchLocalResources() {
  if (!patientData.value.lat || !patientData.value.long) return
  try {
    const res = await fetch(`${MAIN_BACKEND_URL}/api/patients/scrape-resources?lat=${patientData.value.lat}&lon=${patientData.value.long}`)
    if (res.ok) {
      const data = await res.json()
      scrapedResources.value = data.resources || []
    }
  } catch (err) {
    console.error("Error fetching local resources for report:", err)
  }
}

onMounted(() => {
  if (isAnalyzed.value) {
    fetchLocalResources()
    activeGeography.value = 'Active Patient'
  }
})

watch(isAnalyzed, (newVal) => {
  if (newVal) {
    fetchLocalResources()
    activeGeography.value = 'Active Patient'
  }
})

function downloadPatientReport() {
  const origin = window.location.origin
  const p = patientData.value
  const risk = mlPredictionResults.value?.risk_scores || { diabetes: 0.5, hypertension: 0.5, heart_disease: 0.5, asthma: 0.5 }
  const barriers = (mlPredictionResults.value?.sdoh_barriers && mlPredictionResults.value.sdoh_barriers.length > 0)
    ? mlPredictionResults.value.sdoh_barriers
    : [
        'High economic stability concerns',
        'Limited access to primary care providers',
        'Transportation accessibility limits'
      ]
  
  // Format dates
  const dateStr = new Date().toLocaleDateString('en-US', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })

  // Format resources HTML
  let resourcesSectionHtml = ''
  if (scrapedResources.value && scrapedResources.value.length > 0) {
    resourcesSectionHtml = `
      <div class="section-title">Nearby Community Resources (Local Environment)</div>
      <div style="margin-bottom: 20px;">
        ${scrapedResources.value.map(r => `
          <div class="resource-item">
            <div class="resource-header">
              <span class="resource-name">${r.name}</span>
              <span class="resource-category category-${r.category}">${r.categoryLabel}</span>
            </div>
            <div class="resource-meta">
              <span><strong>Distance:</strong> ${r.distance} miles</span> | 
              <span><strong>Address:</strong> ${r.address}</span>
            </div>
            ${r.phone ? `<div><strong>Phone:</strong> ${r.phone}</div>` : ''}
            ${r.website ? `<div><strong>Website:</strong> <a href="https://${r.website}" target="_blank">${r.website}</a></div>` : ''}
            ${r.about ? `<div class="resource-desc">${r.about}</div>` : ''}
          </div>
        `).join('')}
      </div>
    `
  }

  // Format barriers HTML
  let barriersSectionHtml = ''
  if (barriers && barriers.length > 0) {
    barriersSectionHtml = `
      <div class="section-title">Identified SDOH Barriers</div>
      <div class="card" style="margin-bottom: 20px;">
        ${barriers.map(b => `<span class="barrier-tag">${b}</span>`).join(' ')}
      </div>
    `
  }

  const printWindow = window.open('', '_blank')
  printWindow.document.write(`
    <html>
      <head>
        <title>CareEquity - Health Assessment Report - ${p.name}</title>
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
          
          body {
            font-family: 'Inter', sans-serif;
            color: #1e293b;
            background: #ffffff;
            margin: 0;
            padding: 24px;
            line-height: 1.4;
          }

          .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #10b981;
            padding-bottom: 12px;
            margin-bottom: 20px;
          }

          .logo-container {
            display: flex;
            align-items: center;
            gap: 12px;
          }

          .logo-img {
            height: 38px;
            width: auto;
          }

          .name-img {
            height: 58px;
            width: auto;
          }

          .report-meta {
            text-align: right;
            font-size: 13px;
            color: #64748b;
          }

          .report-title {
            font-size: 24px;
            font-weight: 800;
            color: #0f172a;
            margin-top: 0;
            margin-bottom: 6px;
            letter-spacing: -0.5px;
          }

          .report-subtitle {
            font-size: 14px;
            color: #64748b;
            margin-bottom: 20px;
          }

          .section-title {
            font-size: 16px;
            font-weight: 700;
            color: #0f172a;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 6px;
            margin-top: 20px;
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
          }

          .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            margin-bottom: 24px;
          }

          .card {
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
            background: #f8fafc;
          }

          .data-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px dashed #e2e8f0;
          }

          .data-row:last-child {
            border-bottom: none;
          }

          .data-label {
            font-weight: 500;
            color: #64748b;
          }

          .data-value {
            font-weight: 600;
            color: #0f172a;
          }

          .risk-meter-wrapper {
            margin-bottom: 12px;
          }

          .risk-meter-header {
            display: flex;
            justify-content: space-between;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 4px;
          }

          .risk-bar {
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
          }

          .risk-fill {
            height: 100%;
            border-radius: 4px;
          }

          .bg-diabetes { background-color: #3b82f6; }
          .bg-hypertension { background-color: #10b981; }
          .bg-heart { background-color: #eab308; }
          .bg-asthma { background-color: #f97316; }

          .barrier-tag {
            display: inline-block;
            background: #fee2e2;
            color: #991b1b;
            padding: 6px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 13px;
            margin-right: 8px;
            margin-bottom: 8px;
          }

          .resource-item {
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 12px;
            background: #ffffff;
          }

          .resource-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 6px;
          }

          .resource-name {
            font-weight: 700;
            color: #0f172a;
          }

          .resource-category {
            font-size: 11px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 4px;
            text-transform: uppercase;
          }

          .category-food { background: #ffedd5; color: #c2410c; }
          .category-clinic { background: #d1fae5; color: #065f46; }
          .category-gym { background: #f3e8ff; color: #6b21a8; }
          .category-park { background: #dbeafe; color: #1e40af; }

          .resource-meta {
            font-size: 13px;
            color: #64748b;
            margin-bottom: 4px;
          }

          .resource-desc {
            font-size: 13px;
            color: #334155;
            margin-top: 6px;
            font-style: italic;
          }

          .footer {
            margin-top: 40px;
            border-top: 1px solid #e2e8f0;
            padding-top: 16px;
            text-align: center;
            font-size: 12px;
            color: #94a3b8;
          }

          @media print {
            body {
              padding: 0;
            }
            .no-print {
              display: none;
            }
          }
        </style>
      </head>
      <body>
        <div class="header">
          <div class="logo-container">
            <img src="${origin}/assets/careequity_logo.png" class="logo-img" alt="Logo" />
            <img src="${origin}/assets/careequity_name.png" class="name-img" alt="CareEquity" />
          </div>
          <div class="report-meta">
            <div>Generated: ${dateStr}</div>
            <div>Status: SECURED</div>
          </div>
        </div>

        <h1 class="report-title">Overall Health & SDOH Assessment Report</h1>
        <div class="report-subtitle">Comprehensive analysis of clinical risks, social determinants barriers, and local environmental support assets.</div>

        <div class="section-title">Patient Profile Summary</div>
        <div class="grid-2">
          <div class="card">
            <div class="data-row">
              <span class="data-label">Patient Name</span>
              <span class="data-value">${p.name}</span>
            </div>
            <div class="data-row">
              <span class="data-label">Age</span>
              <span class="data-value">${p.age}</span>
            </div>
            <div class="data-row">
              <span class="data-label">Gender</span>
              <span class="data-value">${p.gender}</span>
            </div>
            <div class="data-row">
              <span class="data-label">Location (Lat, Long)</span>
              <span class="data-value">${p.lat}, ${p.long}</span>
            </div>
          </div>

          <div class="card">
            <div class="data-row">
              <span class="data-label">Medication Adherence</span>
              <span class="data-value">${p.medication_adherence}%</span>
            </div>
            <div class="data-row">
              <span class="data-label">ER Visits (Last Year)</span>
              <span class="data-value">${p.er_visits}</span>
            </div>
            <div class="data-row">
              <span class="data-label">Previous Admission</span>
              <span class="data-value">${p.previous_admission}</span>
            </div>
          </div>
        </div>

        <div class="section-title">Clinical Risk Assessment</div>
        <div class="grid-2">
          <div class="card">
            <div class="risk-meter-wrapper">
              <div class="risk-meter-header">
                <span>Diabetes Risk Index</span>
                <span>${Math.round((risk.diabetes || 0.5) * 100)}%</span>
              </div>
              <div class="risk-bar">
                <div class="risk-fill bg-diabetes" style="width: ${Math.round((risk.diabetes || 0.5) * 100)}%"></div>
              </div>
            </div>
            <div class="risk-meter-wrapper">
              <div class="risk-meter-header">
                <span>Hypertension Risk Index</span>
                <span>${Math.round((risk.hypertension || 0.5) * 100)}%</span>
              </div>
              <div class="risk-bar">
                <div class="risk-fill bg-hypertension" style="width: ${Math.round((risk.hypertension || 0.5) * 100)}%"></div>
              </div>
            </div>
          </div>

          <div class="card">
            <div class="risk-meter-wrapper">
              <div class="risk-meter-header">
                <span>Heart Disease Risk Index</span>
                <span>${Math.round((risk.heart_disease || 0.5) * 100)}%</span>
              </div>
              <div class="risk-bar">
                <div class="risk-fill bg-heart" style="width: ${Math.round((risk.heart_disease || 0.5) * 100)}%"></div>
              </div>
            </div>
            <div class="risk-meter-wrapper">
              <div class="risk-meter-header">
                <span>Asthma Risk Index</span>
                <span>${Math.round((risk.asthma || 0.5) * 100)}%</span>
              </div>
              <div class="risk-bar">
                <div class="risk-fill bg-asthma" style="width: ${Math.round((risk.asthma || 0.5) * 100)}%"></div>
              </div>
            </div>
          </div>
        </div>

        ${barriersSectionHtml}
        ${resourcesSectionHtml}

        ${agentReport.value ? `
        <div class="section-title">Multi-Agent Research Assistant Synthesis</div>
        <div class="card" style="margin-bottom: 20px;">
          ${agentReport.value.comprehensive_report ? `
            <h4 style="margin: 0 0 8px 0; color: #0f172a;">📋 Clinical Care Plan</h4>
            <div style="font-size: 13px; color: #334155; line-height: 1.5; margin-bottom: 16px; background: #ffffff; padding: 12px; border-radius: 6px; border: 1px solid #e2e8f0;">${formatAgentReport(agentReport.value.comprehensive_report)}</div>
          ` : ''}

          <h4 style="margin: 0 0 10px 0; color: #0d9488;">💡 Evidence-Based Interventions (${agentReport.value.interventions?.length || 0})</h4>
          ${(agentReport.value.interventions || []).map((item, idx) => `
            <div style="margin-bottom: 10px; padding: 10px; border-left: 3px solid #0d9488; background: #ffffff; border-radius: 4px;">
              <strong>${idx + 1}. ${item.name}</strong> (${item.target_sdoh})<br/>
              <span style="font-size: 13px; color: #475569;">${item.description}</span><br/>
              <span style="font-size: 12px; color: #0f766e;">• <strong>Action:</strong> ${item.how_to_access} | <strong>Outcome:</strong> ${item.expected_outcome}</span>
            </div>
          `).join('')}

          ${agentReport.value.live_surveillance ? `
            <h4 style="margin: 14px 0 6px 0; color: #d97706;">🌐 Live Regional Disease Surveillance — ${agentReport.value.live_surveillance.location || ''}</h4>
            <p style="font-size: 13px; color: #475569; margin-bottom: 8px;">${agentReport.value.live_surveillance.surveillance_summary || ''}</p>
            ${(agentReport.value.live_surveillance.active_disease_alerts || []).map(a => `<div style="background:#fffbeb; color:#92400e; padding:6px 10px; border-radius:4px; font-size:12px; margin-bottom:4px;">⚠️ ${a}</div>`).join('')}
          ` : ''}

          ${agentReport.value.local_resources ? `
            <h4 style="margin: 14px 0 6px 0; color: #0284c7;">📍 Local Safety Net Services</h4>
            <div style="font-size: 12px; color: #334155;">
              <div><strong>Clinics:</strong> ${(agentReport.value.local_resources.healthcare_providers || []).join(', ')}</div>
              <div><strong>Transport:</strong> ${(agentReport.value.local_resources.transportation_programs || []).join(', ')}</div>
              <div><strong>Food:</strong> ${(agentReport.value.local_resources.food_nutrition_services || []).join(', ')}</div>
            </div>
          ` : ''}
        </div>
        ` : ''}



        <div class="footer">
          <p>Confidential Medical Record. This report was compiled using CareEquity predictive models and local geolocation scraping endpoints.</p>
          <p>&copy; ${new Date().getFullYear()} CareEquity Inc. All rights reserved.</p>
        </div>
      </body>
    </html>
  `)
  printWindow.document.close()
  setTimeout(() => {
    printWindow.print()
  }, 500)
}

// Export functions
function exportPDF() {
  if (!isLoggedIn.value) {
    setShowLoginScreen(true)
    return
  }
  if (!userPlan.value) {
    router.push('/plan')
    return
  }
  if (isAnalyzed.value) {
    triggerToast('Generating Patient Report PDF...')
    downloadPatientReport()
  } else {
    triggerToast('Exporting active county report preview to PDF...')
    window.print()
  }
}
function exportCSV() {
  if (!isLoggedIn.value) {
    setShowLoginScreen(true)
    return
  }
  if (!userPlan.value) {
    router.push('/plan')
    return
  }
  triggerToast('Downloading CSV data...')
}
</script>

<template>
  <div class="reports-page">
    
    <!-- Top toast alerts notifications -->
    <Transition name="fade">
      <div v-if="showToast" class="toast-popup">
        <IconBase name="shield" :size="14" />
        <span>{{ toastMsg }}</span>
      </div>
    </Transition>

    <div class="main-layout">
      <!-- 1. Central Report Preview Panel -->
      <div class="content-body">
        
        <!-- Header -->
        <header class="page-header">
          <div>
            <h1>Reports</h1>
            <p class="description">Generate and customize evidence-based reports to support data-driven decisions and health equity.</p>
          </div>
        </header>

        <!-- Recent Report Preview Section -->
        <section class="report-preview-section card">
          
          <!-- Generator Overlay Spinner -->
          <div v-if="isGenerating" class="generating-spinner-overlay">
            <div class="spinner"></div>
            <p class="font-bold">Generating Report Preview...</p>
          </div>

          <div class="preview-header-row">
            <div>
              <h3 class="preview-title">Recent Report Preview</h3>
              <p class="preview-meta font-bold">
                {{ activeReportData.title }} 
                <span class="status-tag">Completed</span>
              </p>
              <p class="preview-sub" v-html="activeReportData.completedDate"></p>
            </div>
            
            <div class="actions" style="display: flex; gap: 10px; align-items: center;">
              <button class="btn outlined" @click="exportPDF">
                <IconBase name="report" :size="13" /> Export PDF
              </button>
            </div>
          </div>

          

          <!-- Top Highlight metrics cards -->
          <div class="preview-stats-row">
            
            <div class="stat-mini-card">
              <div class="card-icon-bubble purple">
                <IconBase name="shield" :size="16" />
              </div>
              <div class="card-content">
                <span class="lbl font-semibold">Health Equity Score</span>
                <div class="val-row">
                  <h2>{{ activeReportData.equityScore }} <span class="max">/100</span></h2>
                  <span class="meta-label orange font-bold">{{ activeReportData.equityLabel }}</span>
                </div>
              </div>
            </div>

            <div class="stat-mini-card">
              <div class="card-icon-bubble green">
                <IconBase name="users" :size="16" />
              </div>
              <div class="card-content">
                <span class="lbl font-semibold">Population Analyzed</span>
                <div class="val-row">
                  <h2>{{ activeReportData.population }}</h2>
                  <span class="trend green font-semibold">{{ activeReportData.popTrend }}</span>
                </div>
              </div>
            </div>

            <div class="stat-mini-card">
              <div class="card-icon-bubble orange">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
              </div>
              <div class="card-content">
                <span class="lbl font-semibold">High-Risk Population</span>
                <div class="val-row">
                  <h2>{{ activeReportData.highRiskPop }}</h2>
                  <span class="trend purple font-semibold">{{ activeReportData.highRiskPct }}</span>
                </div>
              </div>
            </div>

            <div class="stat-mini-card">
              <div class="card-icon-bubble blue">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="2" x2="12" y2="22"/><line x1="5" y1="5" x2="19" y2="5"/><path d="M19 5l-3 7H8L5 5"/></svg>
              </div>
              <div class="card-content">
                <span class="lbl font-semibold">Equity Gap Identified</span>
                <div class="val-row">
                  <h2>{{ activeReportData.equityGap }}</h2>
                  <span class="trend orange font-semibold">vs national average</span>
                </div>
              </div>
            </div>

            <div class="stat-mini-card">
              <div class="card-icon-bubble red">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
              </div>
              <div class="card-content">
                <span class="lbl font-semibold">Intervention Opportunities</span>
                <div class="val-row">
                  <h2>{{ activeReportData.interventions }}</h2>
                  <span class="trend green font-semibold">Active opportunities</span>
                </div>
              </div>
            </div>

          </div>

          <!-- Charts Middle Row layout -->
          <div class="preview-charts-grid">
            
            <!-- Donut 1: Equity score by domain -->
            <div class="card chart-card">
              <h4 class="chart-title font-bold">Equity Score by Domain</h4>
              <div class="chart-flex">
                <div class="donut-svg-wrapper">
                  <svg viewBox="0 0 100 100" class="donut-svg">
                    <circle cx="50" cy="50" r="38" fill="none" stroke="#f1f5f9" stroke-width="12" />
                    <!-- Dynamic end-to-end colorful segments -->
                    <circle 
                      v-for="seg in domainSegments"
                      :key="seg.name"
                      cx="50" 
                      cy="50" 
                      r="38" 
                      fill="none" 
                      :stroke="seg.color" 
                      stroke-width="12" 
                      :stroke-dasharray="seg.dashArray" 
                      :stroke-dashoffset="seg.dashOffset" 
                      transform="rotate(-90 50 50)"
                    />
                  </svg>
                  <div class="center-text">
                    <span class="score font-bold">{{ activeReportData.equityScore }}</span>
                    <span class="label font-bold">{{ activeReportData.equityLabel }}</span>
                  </div>
                </div>

                <div class="donut-legend-col">
                  <div v-for="d in activeReportData.domains" :key="d.name" class="legend-row-item">
                    <span class="legend-dot" :style="{ backgroundColor: d.color }"></span>
                    <span class="name font-semibold">{{ d.name }}</span>
                    <span class="val font-bold">{{ d.score }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Donut 2: SDOH Risk distribution -->
            <div class="card chart-card">
              <h4 class="chart-title font-bold">SDOH Risk Distribution</h4>
              <div class="chart-flex">
                
                <div class="donut-svg-wrapper">
                  <svg viewBox="0 0 100 100" class="donut-svg">
                    <circle cx="50" cy="50" r="38" fill="none" stroke="#f1f5f9" stroke-width="12" />
                    <!-- Dynamic end-to-end colorful segments -->
                    <circle 
                      v-for="seg in riskSegments"
                      :key="seg.label"
                      cx="50" 
                      cy="50" 
                      r="38" 
                      fill="none" 
                      :stroke="seg.color" 
                      stroke-width="12" 
                      :stroke-dasharray="seg.dashArray" 
                      :stroke-dashoffset="seg.dashOffset" 
                      transform="rotate(-90 50 50)"
                    />
                  </svg>
                  <div class="center-text">
                    <span class="score font-bold">{{ isAnalyzed ? '1' : activeReportData.population }}</span>
                    <span class="label font-bold" style="font-size: 0.44rem;">{{ isAnalyzed ? 'Individual' : 'Members' }}</span>
                  </div>
                </div>

                <div class="donut-legend-col">
                  <div v-for="rd in activeReportData.riskDistribution" :key="rd.label" class="legend-row-item">
                    <span class="legend-dot" :style="{ backgroundColor: rd.color }"></span>
                    <span class="name font-semibold">{{ rd.label }}</span>
                    <span class="val font-bold">{{ rd.pct }}</span>
                  </div>
                </div>

              </div>
            </div>

            <!-- List 3: Top contributing progress bars -->
            <div class="card chart-card">
              <h4 class="chart-title font-bold">Top Contributing Factors</h4>
              <div class="factors-progress-list">
                <div v-for="(fact, index) in activeReportData.drivers" :key="fact.name" class="factor-progress-item">
                  <div class="factor-icon-bubble" :class="index === 0 ? 'purple' : (index === 1 ? 'green' : 'orange')">
                    <svg v-if="index === 0" viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
                    <svg v-else-if="index === 1" viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="12" y1="9" x2="12" y2="17"/><line x1="8" y1="13" x2="16" y2="13"/></svg>
                    <svg v-else viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.9A3.7 3.7 0 0 0 2 12v4c0 .6.4 1 1 1h2"/><circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/></svg>
                  </div>
                  <div class="factor-content">
                    <div class="label-row font-semibold">
                      <span class="name">{{ fact.name }}</span>
                      <span class="score-val">{{ typeof fact.score === 'number' ? (fact.score % 1 === 0 ? fact.score : fact.score.toFixed(2)) : fact.score }}</span>
                    </div>
                    <div class="bar-bg">
                      <div class="bar-fill" :style="{ width: (fact.score * 100) + '%', backgroundColor: fact.color }"></div>
                    </div>
                  </div>
                </div>
              </div>
              <span class="impact-axis font-bold">Impact score (0 - 1)</span>
            </div>

          </div>

          <!-- Bottom area table & outcomes scatter plot -->
          <div class="preview-bottom-grid">
            
            <!-- Table: Risk by geographic area -->
            <div class="card table-card">
              <div class="card-header-with-icon">
                <span class="card-icon-bubble purple">
                  <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                </span>
                <h4 class="sec-title font-bold" style="margin: 0;">Risk by Geographic Area (Top 5)</h4>
              </div>
              
              <table class="areas-table">
                <thead>
                  <tr class="font-bold">
                    <th>Area</th>
                    <th class="text-right">Health Risk Score</th>
                    <th class="text-right">SVI Score</th>
                    <th class="text-right">Population</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="area in activeReportData.tableAreas" :key="area.name" class="font-semibold">
                    <td class="name-val">{{ area.name }}</td>
                    <td class="text-right risk-hl">{{ area.score }}</td>
                    <td class="text-right">{{ area.svi }}</td>
                    <td class="text-right count-hl">{{ area.pop }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Scatter Plot: Health Outcomes Correlation -->
            <div class="card scatter-card">
              <h4 class="sec-title font-bold" style="margin-bottom: 8px;">Health Outcomes Correlation</h4>
              
              <div class="scatter-body-row">
                <!-- Left Column: Plot Canvas -->
                <div class="scatter-plot-col">
                  <div class="plot-y-axis-lbl font-semibold">Health Outcomes Risk</div>
                  
                  <div class="plot-canvas" style="flex: 1;">
                    <svg viewBox="0 0 350 140" class="scatter-svg">
                      <!-- Grid background lines -->
                      <line x1="30" y1="20" x2="330" y2="20" stroke="#f1f5f9" stroke-width="1.2" />
                      <line x1="30" y1="50" x2="330" y2="50" stroke="#f1f5f9" stroke-width="1.2" />
                      <line x1="30" y1="80" x2="330" y2="80" stroke="#f1f5f9" stroke-width="1.2" />
                      <line x1="30" y1="110" x2="330" y2="110" stroke="#f1f5f9" stroke-width="1.2" />

                      <!-- Regression dashed line -->
                      <line x1="35" y1="115" x2="320" y2="35" stroke="#8b5cf6" stroke-width="1.5" stroke-dasharray="4,4" />

                      <!-- Scatter plot points -->
                      <circle 
                        v-for="(dot, idx) in activeReportData.scatterDots" 
                        :key="idx" 
                        :cx="dot.x" 
                        :cy="dot.y" 
                        r="3.5" 
                        fill="#8b5cf6" 
                        opacity="0.85" 
                      />
                    </svg>

                    <!-- Axes ticks -->
                    <div class="x-ticks-row font-semibold">
                      <span>0.00</span>
                      <span>0.25</span>
                      <span>0.50</span>
                      <span>0.75</span>
                      <span>1.00</span>
                    </div>
                    <div class="x-axis-title font-semibold">Social Vulnerability Index (SVI)</div>
                  </div>
                </div>

                <!-- Right Column: Sidebar Stats -->
                <div class="scatter-sidebar-col">
                  <div class="correlation-score-card">
                    <span class="lbl font-bold">Correlation (R)</span>
                    <h2 class="val font-bold">{{ activeReportData.correlation }}</h2>
                    <span class="desc font-semibold">{{ activeReportData.correlationLabel }}</span>
                  </div>

                  <div class="explanation-box">
                    <span class="bulb-icon">
                      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A5 5 0 0 0 8 8c0 1 .5 2.5 1.5 3.5.7.8 1.3 1.5 1.5 2.5"/><line x1="9" y1="18" x2="15" y2="18"/><line x1="10" y1="22" x2="14" y2="22"/></svg>
                    </span>
                    <p class="explanation font-semibold">Higher social vulnerability is associated with poorer health outcomes.</p>
                  </div>
                </div>
              </div>
            </div>

          </div>

          <!-- Multi-Agent Research Assistant Intelligence Section (Tabs & Content) -->
          <div class="agent-intelligence-wrapper card" style="margin-top: 24px; padding: 20px; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0;">
            
            <!-- Agent Header Strip -->
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #f1f5f9;">
              <div>
                <h3 style="margin: 0 0 4px 0; font-size: 1.15rem; font-weight: 800; color: #0f172a; display: flex; align-items: center; gap: 8px;">
                  <span>🤖 Multi-Agent Research Assistant Synthesis</span>
                  <span v-if="isAgentLoading" style="font-size: 0.75rem; background: #fef3c7; color: #92400e; padding: 2px 8px; border-radius: 12px; font-weight: 600;">⚡ Synthesizing Live LLM Intelligence...</span>
                  <span v-else-if="agentReport" style="font-size: 0.75rem; background: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 12px; font-weight: 600;">✓ Live Synthesis Ready</span>
                </h3>
                <p style="margin: 0; font-size: 0.82rem; color: #64748b;">Multi-agent SDOH evaluation, live web surveillance, targeted interventions, and local safety net services.</p>
              </div>
            </div>

            <!-- Tab Navigation Strip (matching image 1) -->
            <div class="agent-tabs-nav">
              <button 
                class="agent-tab-btn" 
                :class="{ active: activeAgentTab === 'care_plan' }"
                @click="activeAgentTab = 'care_plan'"
              >
                📋 Clinical Care Plan
              </button>
              <button 
                class="agent-tab-btn" 
                :class="{ active: activeAgentTab === 'interventions' }"
                @click="activeAgentTab = 'interventions'"
              >
                💡 Targeted Interventions
              </button>
              <button 
                class="agent-tab-btn" 
                :class="{ active: activeAgentTab === 'live_alerts' }"
                @click="activeAgentTab = 'live_alerts'"
              >
                🌐 Live Disease Alerts
              </button>
              <button 
                class="agent-tab-btn" 
                :class="{ active: activeAgentTab === 'safety_net' }"
                @click="activeAgentTab = 'safety_net'"
              >
                📍 Local Safety Net
              </button>
              <button 
                class="agent-tab-btn" 
                :class="{ active: activeAgentTab === 'demographics' }"
                @click="activeAgentTab = 'demographics'"
              >
                🗺️ Area Demographics
              </button>
            </div>

            <!-- Tab Contents -->
            <div class="agent-tab-content" style="margin-top: 18px;">
              
              <!-- Tab 1: Clinical Care Plan -->
              <div v-if="activeAgentTab === 'care_plan'">
                <div 
                  v-if="agentReport && agentReport.comprehensive_report" 
                  class="agent-care-plan-body" 
                  style="font-size: 0.9rem; line-height: 1.6; color: #334155; background: #f8fafc; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0;"
                  v-html="formatAgentReport(agentReport.comprehensive_report)"
                ></div>
                <div v-else style="padding: 24px; text-align: center; color: #64748b;">
                  <p style="font-size: 0.9rem; font-weight: 600;">📋 Comprehensive Clinical Care Plan</p>
                  <p style="font-size: 0.82rem;">Run analysis in <strong>Data Setup</strong> to populate live multi-agent care plan synthesis.</p>
                  <div style="background: #f1f5f9; padding: 14px; border-radius: 8px; text-align: left; margin-top: 12px; font-size: 0.85rem;">
                    <strong>Baseline Guidance:</strong> Initiate multidisciplinary SDOH screening for chronic disease management, food security support, and medical transport coordination.
                  </div>
                </div>
              </div>

              <!-- Tab 2: Targeted Interventions -->
              <div v-if="activeAgentTab === 'interventions'">
                <div v-if="agentReport && agentReport.interventions && agentReport.interventions.length > 0">
                  <h4 style="margin: 0 0 12px 0; font-size: 0.95rem; font-weight: 700; color: #0f172a;">Evidence-Based Interventions ({{ agentReport.interventions.length }})</h4>
                  <div style="display: grid; grid-template-columns: 1fr; gap: 12px;">
                    <div v-for="(item, i) in agentReport.interventions" :key="i" style="background: #f8fafc; border-left: 4px solid #0d9488; padding: 14px; border-radius: 6px; border: 1px solid #e2e8f0;">
                      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <strong style="color: #0f766e; font-size: 0.95rem;">{{ i + 1 }}. {{ item.name }}</strong>
                        <span style="background: #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 700;">{{ item.target_sdoh }}</span>
                      </div>
                      <p style="margin: 0 0 8px 0; font-size: 0.85rem; color: #334155;">{{ item.description }}</p>
                      <div style="font-size: 0.8rem; color: #475569; display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                        <div><strong>Action:</strong> {{ item.how_to_access }}</div>
                        <div><strong>Outcome:</strong> {{ item.expected_outcome }}</div>
                        <div><strong>Contact:</strong> {{ item.contact_info }}</div>
                        <div><strong>Timeline:</strong> {{ item.timeline }}</div>
                      </div>
                    </div>
                  </div>
                </div>
                <div v-else style="padding: 24px; text-align: center; color: #64748b;">
                  <p style="font-size: 0.9rem; font-weight: 600;">💡 Targeted Evidence-Based Interventions</p>
                  <p style="font-size: 0.82rem;">No custom agent interventions loaded yet. Prescribing default evidence-based protocol.</p>
                  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; text-align: left; margin-top: 12px;">
                    <div style="background: #f8fafc; padding: 10px; border-radius: 6px; border-left: 3px solid #3b82f6; font-size: 0.82rem;">
                      <strong>1. Produce Prescription & Food Pantry Referral</strong><br/>
                      Provides fresh fruits & vegetables vouchers to low-income patients with chronic conditions.
                    </div>
                    <div style="background: #f8fafc; padding: 10px; border-radius: 6px; border-left: 3px solid #10b981; font-size: 0.82rem;">
                      <strong>2. Non-Emergency Medical Transportation (NEMT)</strong><br/>
                      Rideshare vouchers & shuttle passes for routine clinic & pharmacy visits.
                    </div>
                  </div>
                </div>
              </div>

              <!-- Tab 3: Live Disease Alerts -->
              <div v-if="activeAgentTab === 'live_alerts'">
                <div v-if="agentReport && agentReport.live_surveillance">
                  <div style="background: #eff6ff; border: 1px solid #bfdbfe; padding: 12px; border-radius: 6px; margin-bottom: 12px; font-size: 0.85rem; color: #1e40af;">
                    <strong>Surveillance Location:</strong> {{ agentReport.live_surveillance.location || 'Regional Monitor' }}<br/>
                    <span>{{ agentReport.live_surveillance.surveillance_summary }}</span>
                  </div>

                  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                    <div>
                      <h5 style="margin: 0 0 8px 0; color: #991b1b; font-size: 0.85rem; font-weight: 700;">⚠️ Active Regional Disease & Health Alerts</h5>
                      <div v-if="agentReport.live_surveillance.active_disease_alerts && agentReport.live_surveillance.active_disease_alerts.length > 0">
                        <div v-for="(alert, aIdx) in agentReport.live_surveillance.active_disease_alerts" :key="aIdx" style="background: #fef2f2; color: #991b1b; padding: 8px 12px; border-radius: 6px; font-size: 0.82rem; font-weight: 600; margin-bottom: 6px; border: 1px solid #fecaca;">
                          ⚠️ {{ alert }}
                        </div>
                      </div>
                      <div v-else style="font-size: 0.82rem; color: #64748b;">No active epidemic warnings reported.</div>

                      <h5 style="margin: 12px 0 8px 0; color: #0f172a; font-size: 0.85rem; font-weight: 700;">📈 Public Health Trends</h5>
                      <ul style="margin: 0; padding-left: 18px; font-size: 0.82rem; color: #334155;">
                        <li v-for="(tr, tIdx) in (agentReport.live_surveillance.public_health_trends || ['Seasonal flu surveillance active', 'Community heat vulnerability monitoring'])" :key="tIdx">
                          {{ tr }}
                        </li>
                      </ul>
                    </div>

                    <div>
                      <h5 style="margin: 0 0 8px 0; color: #0f172a; font-size: 0.85rem; font-weight: 700;">📰 Live Web News & Advisories</h5>
                      <div v-if="agentReport.live_surveillance.recent_news_snippets && agentReport.live_surveillance.recent_news_snippets.length > 0">
                        <div v-for="(news, nIdx) in agentReport.live_surveillance.recent_news_snippets.slice(0, 3)" :key="nIdx" style="margin-bottom: 8px; padding: 8px; background: #f8fafc; border-radius: 6px; font-size: 0.8rem;">
                          <a :href="news.url || '#'" target="_blank" style="font-weight: 700; color: #2563eb; text-decoration: underline;">{{ news.title || 'Health Advisory' }}</a>
                          <p style="margin: 2px 0 0 0; color: #475569;">{{ news.snippet }}</p>
                        </div>
                      </div>
                      <div v-else style="font-size: 0.82rem; color: #64748b;">Active live web crawler monitoring local health department portals.</div>
                    </div>
                  </div>
                </div>
                <div v-else style="padding: 24px; text-align: center; color: #64748b;">
                  <p style="font-size: 0.9rem; font-weight: 600;">🌐 Live Regional Disease Surveillance</p>
                  <p style="font-size: 0.82rem;">Real-time web monitoring for regional outbreaks, heat waves, and public health advisories.</p>
                </div>
              </div>

              <!-- Tab 4: Local Safety Net -->
              <div v-if="activeAgentTab === 'safety_net'">
                <div v-if="agentReport && agentReport.local_resources">
                  <h4 style="margin: 0 0 12px 0; font-size: 0.95rem; font-weight: 700; color: #0f172a;">Local Safety Net Assets — {{ agentReport.local_resources.location }}</h4>
                  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                    <div>
                      <h5 style="margin: 0 0 6px 0; font-size: 0.85rem; color: #0369a1;">🏥 Clinics & Healthcare Providers</h5>
                      <ul style="margin: 0 0 12px 0; padding-left: 18px; font-size: 0.82rem; color: #334155;">
                        <li v-for="(hc, hcIdx) in (agentReport.local_resources.healthcare_providers || [])" :key="hcIdx"><strong>{{ hc }}</strong></li>
                      </ul>

                      <h5 style="margin: 0 0 6px 0; font-size: 0.85rem; color: #0369a1;">🚌 Transportation Assistance</h5>
                      <ul style="margin: 0; padding-left: 18px; font-size: 0.82rem; color: #334155;">
                        <li v-for="(tr, trIdx) in (agentReport.local_resources.transportation_programs || [])" :key="trIdx">{{ tr }}</li>
                      </ul>
                    </div>

                    <div>
                      <h5 style="margin: 0 0 6px 0; font-size: 0.85rem; color: #0369a1;">🍎 Food & Nutrition Services</h5>
                      <ul style="margin: 0 0 12px 0; padding-left: 18px; font-size: 0.82rem; color: #334155;">
                        <li v-for="(fd, fdIdx) in (agentReport.local_resources.food_nutrition_services || [])" :key="fdIdx">{{ fd }}</li>
                      </ul>

                      <h5 style="margin: 0 0 6px 0; font-size: 0.85rem; color: #991b1b;">🚨 24/7 Crisis Helplines</h5>
                      <div style="font-size: 0.82rem; color: #334155;">
                        <div v-for="(val, key) in (agentReport.local_resources.emergency_contacts || {})" :key="key">
                          <strong>{{ key }}:</strong> <code style="background: #f1f5f9; padding: 2px 6px; border-radius: 4px;">{{ val }}</code>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div v-else style="padding: 24px; text-align: center; color: #64748b;">
                  <p style="font-size: 0.9rem; font-weight: 600;">📍 Local Safety Net Services</p>
                  <p style="font-size: 0.82rem;">Locates nearby community clinics, food banks, transit vouchers, and crisis support lines.</p>
                </div>
              </div>

              <!-- Tab 5: Area Demographics -->
              <div v-if="activeAgentTab === 'demographics'">
                <div v-if="agentReport && agentReport.geographic_analysis">
                  <h4 style="margin: 0 0 12px 0; font-size: 0.95rem; font-weight: 700; color: #0f172a;">Regional Demographics — {{ agentReport.geographic_analysis.location }}</h4>
                  <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 14px;">
                    <div style="background: #f8fafc; padding: 10px; border-radius: 6px; border: 1px solid #e2e8f0; text-align: center;">
                      <span style="font-size: 0.75rem; color: #64748b; font-weight: 600;">Median Age</span>
                      <div style="font-size: 1.1rem; font-weight: 800; color: #0f172a;">{{ agentReport.geographic_analysis.demographics?.median_age || 36 }} yrs</div>
                    </div>
                    <div style="background: #f8fafc; padding: 10px; border-radius: 6px; border: 1px solid #e2e8f0; text-align: center;">
                      <span style="font-size: 0.75rem; color: #64748b; font-weight: 600;">Poverty Rate</span>
                      <div style="font-size: 1.1rem; font-weight: 800; color: #eab308;">{{ agentReport.geographic_analysis.demographics?.poverty_rate || 18 }}%</div>
                    </div>
                    <div style="background: #f8fafc; padding: 10px; border-radius: 6px; border: 1px solid #e2e8f0; text-align: center;">
                      <span style="font-size: 0.75rem; color: #64748b; font-weight: 600;">Diabetes Rate</span>
                      <div style="font-size: 1.1rem; font-weight: 800; color: #ef4444;">{{ agentReport.geographic_analysis.health_statistics?.diabetes_rate || 12 }}%</div>
                    </div>
                    <div style="background: #f8fafc; padding: 10px; border-radius: 6px; border: 1px solid #e2e8f0; text-align: center;">
                      <span style="font-size: 0.75rem; color: #64748b; font-weight: 600;">Hypertension Rate</span>
                      <div style="font-size: 1.1rem; font-weight: 800; color: #3b82f6;">{{ agentReport.geographic_analysis.health_statistics?.hypertension_rate || 35 }}%</div>
                    </div>
                  </div>
                  <div style="font-size: 0.85rem; color: #334155; line-height: 1.5; background: #f8fafc; padding: 12px; border-radius: 6px; border: 1px solid #e2e8f0;">
                    <strong>Area Profile:</strong> {{ agentReport.geographic_analysis.area_health_profile || 'Urban environment profile with elevated socioeconomic vulnerability.' }}<br/><br/>
                    <strong>Environmental Factors:</strong> {{ agentReport.geographic_analysis.environmental_factors || 'Air quality index moderate, transit corridor proximity.' }}
                  </div>
                </div>
                <div v-else style="padding: 24px; text-align: center; color: #64748b;">
                  <p style="font-size: 0.9rem; font-weight: 600;">🗺️ Regional Demographics & Environmental Drivers</p>
                  <p style="font-size: 0.82rem;">Displays area-specific SVI metrics, poverty rates, and clinical disease prevalence.</p>
                </div>
              </div>

            </div>

          </div>

          <div class="data-refreshed-bar font-semibold">
            <span class="left-info"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px; vertical-align: middle;"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg> Report generated on May 31, 2025 &bull; 10:24 AM</span>
            <span class="secured"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px; vertical-align: middle;"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg> Data privacy &amp; security protected</span>
            <span class="right-info"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px; vertical-align: middle;"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg> Data refreshed May 31, 2025</span>
          </div>

        </section>

      </div>

      <!-- 2. Right Configuration Sidebar Panel -->
      
    </div>

  </div>
</template>

<style scoped>
/* Agent Tabs Styling */
.agent-tabs-nav {
  display: flex;
  gap: 16px;
  border-bottom: 2px solid #e2e8f0;
  padding-bottom: 2px;
  overflow-x: auto;
}

.agent-tab-btn {
  background: none;
  border: none;
  padding: 8px 16px;
  font-size: 0.88rem;
  font-weight: 700;
  color: #64748b;
  cursor: pointer;
  border-bottom: 3px solid transparent;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.agent-tab-btn:hover {
  color: #0f172a;
}

.agent-tab-btn.active {
  color: #ef4444;
  border-bottom-color: #ef4444;
}

.reports-page {
  background: #f8fafc;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}


/* Toast popup notification */
.toast-popup {
  position: absolute;
  top: 24px;
  left: 50%;
  transform: translateX(-50%);
  background: #1e293b;
  color: #ffffff;
  padding: 10px 18px;
  border-radius: 8px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 1000;
  font-size: 0.74rem;
  font-weight: 600;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translate(-50%, -10px);
}

/* Grid Layout */
.main-layout {
  display: grid;
  grid-template-columns: 1fr;
  height: 100%;
}

.content-body {
  padding: 24px 32px 32px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
  min-height: 0;
}

/* Header */
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

/* Card */
.card {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  padding: 16px;
}

/* Buttons */
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
  border: none;
  color: #ffffff;
}
.btn.primary:hover {
  background: var(--brand-dark);
}

/* Preset Template cards row */
.templates-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.template-card {
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
  align-items: flex-start;
}

.template-card:hover {
  border-color: #cbd5e1;
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.template-card .icon-bubble {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.icon-bubble.blue { background: #eff6ff; color: #3b82f6; }
.icon-bubble.green { background: #ecfdf5; color: #10b981; }
.icon-bubble.purple { background: #f5f3ff; color: #8b5cf6; }
.icon-bubble.orange { background: #fffbeb; color: #f59e0b; }
.icon-bubble.rose { background: #fff1f2; color: #f43f5e; }

.template-card h4 {
  margin: 0;
  font-size: 0.76rem;
  color: var(--text-primary);
}

.template-card p {
  margin: 0;
  font-size: 0.64rem;
  color: var(--text-secondary);
  line-height: 1.35;
  flex-grow: 1;
}

.use-tpl-btn {
  background: transparent;
  border: none;
  color: var(--brand);
  font-size: 0.68rem;
  padding: 0;
  margin-top: 6px;
  cursor: pointer;
}
.use-tpl-btn:hover {
  text-decoration: underline;
}

/* Recent Report Preview Section */
.report-preview-section {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Spinner Overlay for generation */
.generating-spinner-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.85);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  z-index: 100;
  border-radius: var(--radius-lg);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3.5px solid #cbd5e1;
  border-top-color: var(--brand);
  border-radius: 50%;
  animation: spinner-spin 0.8s linear infinite;
}

@keyframes spinner-spin {
  to { transform: rotate(360deg); }
}

.generating-spinner-overlay p {
  font-size: 0.82rem;
  color: var(--text-primary);
}

.preview-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border-bottom: 1px solid var(--border);
  padding-bottom: 12px;
}

.preview-title {
  margin: 0 0 2px;
  font-size: 0.95rem;
  font-weight: 800;
  color: var(--text-primary);
}

.preview-meta {
  margin: 0;
  font-size: 0.84rem;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-tag {
  font-size: 0.54rem;
  background: #d1fae5;
  color: #065f46;
  padding: 1px 5px;
  border-radius: 4px;
  font-weight: 700;
}

.preview-sub {
  margin: 2px 0 0;
  font-size: 0.72rem;
  color: var(--text-tertiary);
}

.preview-header-row .actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.three-dots-btn {
  border: none;
  background: transparent;
  color: #cbd5e1;
  cursor: pointer;
  font-size: 0.85rem;
}

/* Highlights stats row */
.preview-stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.preview-stats-row .stat-mini-card {
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 12px;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 12px;
  background: #ffffff;
  transition: all 0.15s ease;
  overflow: hidden;
  box-sizing: border-box;
}

.preview-stats-row .stat-mini-card:hover {
  border-color: #cbd5e1;
  box-shadow: var(--shadow-sm);
  transform: translateY(-1px);
}

.stat-mini-card .card-icon-bubble {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.card-icon-bubble.purple { background: #f5f3ff; color: #8b5cf6; }
.card-icon-bubble.green { background: #ecfdf5; color: #10b981; }
.card-icon-bubble.orange { background: #fffbeb; color: #f59e0b; }
.card-icon-bubble.blue { background: #eff6ff; color: #3b82f6; }
.card-icon-bubble.red { background: #fff1f2; color: #ef4444; }

.stat-mini-card .card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.stat-mini-card .lbl {
  font-size: 0.58rem;
  color: var(--text-secondary);
  text-transform: uppercase;
}

.stat-mini-card .val-row {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 4px;
}

.stat-mini-card h2 {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1.2;
  word-break: break-word;
}

.stat-mini-card h2 .max {
  font-size: 0.65rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.stat-mini-card .meta-label {
  font-size: 0.56rem;
  padding: 1px 5px;
  border-radius: 4px;
}
.meta-label.orange { background: #ffedd5; color: #c2410c; }

.stat-mini-card .trend {
  font-size: 0.58rem;
}
.trend.green { color: #10b981; }
.trend.purple { color: #8b5cf6; }
.trend.orange { color: #f97316; }

.mini-sparkline {
  width: 100%;
  height: 15px;
}

/* Charts middle row grid */
.preview-charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
}

.chart-card {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.chart-title {
  margin: 0;
  font-size: 0.76rem;
  color: var(--text-primary);
}

.chart-flex {
  display: flex;
  align-items: center;
  gap: 14px;
}

.donut-svg-wrapper {
  width: 100px;
  height: 100px;
  position: relative;
  flex-shrink: 0;
}

.donut-svg {
  width: 100%;
  height: 100%;
}

.center-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  line-height: 1.15;
}

.center-text .score {
  font-size: 1.25rem;
  color: var(--text-primary);
  text-align: center;
}

.center-text .label {
  font-size: 0.54rem;
  color: var(--text-tertiary);
  text-transform: uppercase;
}

.donut-legend-col {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex-grow: 1;
}

.legend-row-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-row-item .name {
  font-size: 0.62rem;
  color: var(--text-secondary);
  flex-grow: 1;
  white-space: nowrap;
}

.legend-row-item .val {
  font-size: 0.62rem;
  color: var(--text-primary);
}

/* Factors Progress List */
.factors-progress-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.factor-progress-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 12px;
  margin-bottom: 4px;
}

.factor-progress-item .factor-icon-bubble {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.factor-icon-bubble.purple { background: #f5f3ff; color: #8b5cf6; }
.factor-icon-bubble.green { background: #ecfdf5; color: #10b981; }
.factor-icon-bubble.orange { background: #fffbeb; color: #f59e0b; }

.factor-progress-item .factor-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.factor-progress-item .label-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.62rem;
  color: var(--text-primary);
}

.factor-progress-item .name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bar-bg {
  height: 4px;
  background: #f1f5f9;
  border-radius: 2px;
}

.bar-fill {
  height: 100%;
  border-radius: 2px;
}

.impact-axis {
  font-size: 0.54rem;
  color: var(--text-tertiary);
  text-transform: uppercase;
  margin-top: auto;
  align-self: flex-end;
}

/* Bottom area grid */
.preview-bottom-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  gap: 12px;
}

.sec-title {
  margin: 0 0 10px;
  font-size: 0.74rem;
  color: var(--text-primary);
}

/* Areas Table */
.areas-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 8px;
}

.areas-table th {
  font-size: 0.56rem;
  color: var(--text-tertiary);
  text-transform: uppercase;
  padding: 4px 6px;
  border-bottom: 1px solid var(--border);
}

.areas-table td {
  font-size: 0.66rem;
  padding: 5px 6px;
  border-bottom: 1px dashed #f1f5f9;
}

.areas-table .text-right {
  text-align: right;
}

.areas-table .name-val {
  color: var(--text-primary);
}

.areas-table .risk-hl {
  color: #ef4444;
}

.areas-table .count-hl {
  color: var(--text-secondary);
}

.more-link, .details-link {
  font-size: 0.66rem;
  color: var(--brand);
  text-decoration: none;
}
.more-link:hover, .details-link:hover {
  text-decoration: underline;
}

/* Card Header with Icon */
.card-header-with-icon {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.card-header-with-icon .card-icon-bubble {
  width: 26px;
  height: 26px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.card-header-with-icon .card-icon-bubble.purple {
  background: #f5f3ff;
  color: #8b5cf6;
}

/* View areas button */
.view-areas-btn {
  background: transparent;
  border: 1px solid #cbd5e1;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 0.68rem;
  color: #8b5cf6;
  cursor: pointer;
  transition: all 0.15s ease;
}
.view-areas-btn:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
  box-shadow: var(--shadow-sm);
}

/* Scatter plot card */
.scatter-body-row {
  display: flex;
  gap: 16px;
  align-items: center;
  margin-top: 10px;
}

.scatter-plot-col {
  flex: 1.5;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
}

.scatter-sidebar-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.correlation-score-card {
  background: #f5f3ff;
  border-radius: 8px;
  padding: 10px;
  text-align: center;
}

.correlation-score-card .lbl {
  font-size: 0.52rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  display: block;
  margin-bottom: 2px;
}

.correlation-score-card .val {
  font-size: 1.25rem;
  color: #8b5cf6;
  margin: 0;
}

.correlation-score-card .desc {
  font-size: 0.56rem;
  color: #8b5cf6;
  display: block;
  margin-top: 2px;
}

.explanation-box {
  background: #f5f3ff;
  border-radius: 8px;
  padding: 10px;
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.explanation-box .bulb-icon {
  color: #8b5cf6;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 1px;
}

.explanation-box .explanation {
  margin: 0;
  font-size: 0.58rem;
  color: var(--text-secondary);
  line-height: 1.35;
}

.plot-y-axis-lbl {
  font-size: 0.54rem;
  color: var(--text-tertiary);
  text-transform: uppercase;
  writing-mode: vertical-rl;
  transform: rotate(180deg);
  text-align: center;
}

.plot-canvas {
  display: flex;
  flex-direction: column;
}

.scatter-svg {
  width: 100%;
  height: 90px;
  background: #fafbfe;
  border-left: 1.5px solid #cbd5e1;
  border-bottom: 1.5px solid #cbd5e1;
}

.x-ticks-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.52rem;
  color: var(--text-tertiary);
  padding: 2px 4px 0;
}

.x-axis-title {
  font-size: 0.54rem;
  color: var(--text-tertiary);
  text-transform: uppercase;
  text-align: center;
  margin-top: 2px;
}

/* bottom data refreshed bar */
.data-refreshed-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.6rem;
  color: var(--text-tertiary);
  border-top: 1px solid var(--border);
  padding-top: 12px;
  margin-top: 8px;
}

.data-refreshed-bar .secured {
  color: var(--text-tertiary);
  display: flex;
  align-items: center;
  gap: 4px;
}

.data-refreshed-bar .left-info,
.data-refreshed-bar .right-info {
  display: flex;
  align-items: center;
}

/* Right sidebar panels */
.reports-sidebar-rail {
  background: #ffffff;
  border-left: 1px solid var(--border);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

.creator-panel .panel-title, .recent-reports-panel .panel-title {
  margin: 0 0 2px;
  font-size: 0.86rem;
  color: var(--text-primary);
}

.creator-panel .panel-sub {
  margin: 0 0 14px;
  font-size: 0.74rem;
  color: var(--text-secondary);
}

.config-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.config-form .form-group {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.step-num {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #f1f5f9;
  color: var(--text-secondary);
  font-size: 0.64rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}

.input-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex-grow: 1;
}

.input-content.flex-row {
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
}

.input-content label {
  font-size: 0.62rem;
  color: var(--text-secondary);
  text-transform: uppercase;
}

.select-field {
  width: 100%;
  border: 1px solid var(--border);
  background: #ffffff;
  border-radius: 6px;
  padding: 5px 8px;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-primary);
  outline: none;
  cursor: pointer;
}

.clickable-selector {
  border-bottom: 1px dashed var(--border);
  padding-bottom: 8px;
  cursor: pointer;
}

.selection-desc {
  margin: 1px 0 0;
  font-size: 0.76rem;
  color: var(--brand);
}

.arrow {
  color: var(--text-tertiary);
  font-weight: 600;
  font-size: 0.74rem;
}

.generate-btn {
  width: 100%;
  margin-top: 6px;
  justify-content: center;
}

/* History items */
.recent-reports-panel .panel-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.view-all-link {
  font-size: 0.66rem;
  color: var(--brand);
  text-decoration: none;
}

.reports-history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 6px 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.history-item:hover {
  background: #f8fafc;
}

.icon-circle {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}
.icon-circle.blue { background: #eff6ff; color: #3b82f6; }
.icon-circle.green { background: #ecfdf5; color: #10b981; }
.icon-circle.purple { background: #f5f3ff; color: #8b5cf6; }
.icon-circle.orange { background: #fffbeb; color: #f59e0b; }
.icon-circle.rose { background: #fff1f2; color: #f43f5e; }

.history-item .info {
  display: flex;
  flex-direction: column;
  flex-grow: 1;
  min-width: 0;
}

.history-item .title {
  margin: 0;
  font-size: 0.74rem;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.history-item .meta {
  margin: 1px 0 3px;
  font-size: 0.58rem;
  color: var(--text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-badge.completed {
  font-size: 0.52rem;
  color: #16a34a;
  align-self: flex-start;
}

.menu-btn {
  border: none;
  background: transparent;
  color: #94a3b8;
  cursor: pointer;
  font-size: 0.65rem;
  padding: 0 4px;
}

/* ── RESPONSIVE OVERRIDES ── */
@media (max-width: 1100px) {
  .preview-stats-row {
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  }
  
  .preview-charts-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .preview-charts-grid {
    grid-template-columns: 1fr;
  }

  .preview-bottom-grid {
    grid-template-columns: 1fr;
  }

  .scatter-body-row {
    flex-direction: column;
    align-items: stretch;
  }
  
  .scatter-plot-col {
    width: 100%;
  }
  
  .scatter-sidebar-col {
    width: 100%;
    flex-direction: row;
    gap: 8px;
  }
  
  .correlation-score-card,
  .explanation-box {
    flex: 1;
  }

  .data-refreshed-bar {
    flex-direction: column;
    gap: 8px;
    align-items: flex-start;
  }
}

@media (max-width: 650px) {
  .preview-stats-row {
    grid-template-columns: 1fr;
  }

  .preview-header-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .scatter-sidebar-col {
    flex-direction: column;
  }
}
</style>
