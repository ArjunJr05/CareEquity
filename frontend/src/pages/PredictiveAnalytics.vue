<script setup>
import { ref, computed } from 'vue'
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

// Local State
const selectedId = ref('cuyahoga')
const activeTrendFilter = ref('all') // 'all', 'hosp', 'util', 'chronic', 'gap'
const activeGeoTab = ref('county') // 'county', 'zip', 'tract'
const activeCorrelationOutcome = ref('hosp') // 'hosp', 'util', 'chronic', 'gap'

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
        <section v-if="isAnalyzed" class="card active-patient-prediction-panel" style="background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%); color: white; border: none; border-radius: var(--radius-lg); padding: 24px; margin-bottom: 24px; box-shadow: 0 10px 30px rgba(49, 46, 129, 0.2);">
          <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 16px; margin-bottom: 20px;">
            <div style="display: flex; align-items: center; gap: 12px;">
              <span style="font-size: 24px;">👤</span>
              <div>
                <h3 style="margin: 0; color: white; font-size: 1.25rem; font-weight: 800;">Patient Risk Profile: {{ patientData.name }}</h3>
                <p style="margin: 4px 0 0; font-size: 0.85rem; color: rgba(255,255,255,0.7);">
                  Real-time clinical and geographic risk assessment powered by random forest and gradient boosted estimators.
                </p>
              </div>
            </div>
            <div style="text-align: right;">
              <span style="background: rgba(255,255,255,0.1); padding: 6px 14px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; color: #a5b4fc;">
                BMI: {{ ((patientData.weight_kg) / ((patientData.height_cm / 100) * (patientData.height_cm / 100))).toFixed(1) }} ({{ patientData.height_cm }}cm / {{ patientData.weight_kg }}kg)
              </span>
            </div>
          </div>

          <div style="display: flex; flex-wrap: wrap; gap: 24px;">
            <!-- Column 1: Overall Score Radial Gauge -->
            <div style="flex: 1; min-width: 200px; display: flex; flex-direction: column; align-items: center; justify-content: center; background: rgba(255,255,255,0.05); padding: 20px; border-radius: var(--radius-md); border: 1px solid rgba(255,255,255,0.05);">
              <p style="margin: 0 0 12px; font-size: 0.85rem; font-weight: bold; text-transform: uppercase; letter-spacing: 0.05em; color: rgba(255,255,255,0.7);">Patient Health Score</p>
              <div class="circle-gauge" style="width: 100px; height: 100px; position: relative; margin-bottom: 12px;">
                <svg width="100" height="100" viewBox="0 0 36 36" class="circular-chart" style="width: 100%; height: 100%;">
                  <path class="circle-bg" style="stroke: rgba(255,255,255,0.1); fill: none; stroke-width: 2.8;" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                  <path class="circle" style="stroke: #818cf8; fill: none; stroke-width: 2.8; stroke-linecap: round;" :stroke-dasharray="patientSidebarData.equityScore + ', 100'" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                </svg>
                <div class="gauge-center" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); display: flex; flex-direction: column; align-items: center;">
                  <span class="score-num" style="font-size: 22px; font-weight: 800; color: white;">{{ patientSidebarData.equityScore }}</span>
                  <span class="score-den" style="font-size: 10px; color: rgba(255,255,255,0.5);">/100</span>
                </div>
              </div>
              <span class="gauge-level-badge font-bold" :class="patientSidebarData.equityLevel.toLowerCase().replace(' ', '-')" style="font-size: 0.75rem; padding: 4px 10px; border-radius: 20px; color: white; display: inline-block;">
                {{ patientSidebarData.equityLevel }}
              </span>
              <p style="margin: 8px 0 0; font-size: 0.75rem; opacity: 0.7;">Health Gap: {{ 100 - patientSidebarData.equityScore }} pts vs National Avg</p>
            </div>

            <!-- Column 2: Disease Risk Predictions -->
            <div style="flex: 2; min-width: 300px; background: rgba(255,255,255,0.03); padding: 20px; border-radius: var(--radius-md); border: 1px solid rgba(255,255,255,0.05); display: flex; flex-direction: column; justify-content: space-between;">
              <p style="margin: 0 0 16px; font-size: 0.85rem; font-weight: bold; text-transform: uppercase; letter-spacing: 0.05em; color: rgba(255,255,255,0.7);">Clinical Disease Risk Probabilities</p>
              
              <div v-if="mlPredictionResults" style="display: flex; flex-direction: column; gap: 14px;">
                <div v-for="(val, disease) in mlPredictionResults.risk_scores" :key="disease">
                  <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 6px;">
                    <span style="text-transform: capitalize; font-weight: 700; color: rgba(255,255,255,0.9);">{{ disease.replace('_', ' ') }}</span>
                    <span style="font-weight: 800; color: white;">{{ Math.round(val * 100) }}%</span>
                  </div>
                  <div style="height: 8px; background-color: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden; display: flex;">
                    <div :style="{ width: (val * 100) + '%', backgroundColor: val > 0.7 ? '#f87171' : (val > 0.4 ? '#fbbf24' : '#34d399') }" style="height: 100%; border-radius: 4px;"></div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Column 3: Geocoded Location SDoH Risk -->
            <div style="flex: 2; min-width: 300px; background: rgba(255,255,255,0.03); padding: 20px; border-radius: var(--radius-md); border: 1px solid rgba(255,255,255,0.05); display: flex; flex-direction: column; justify-content: space-between;">
              <p style="margin: 0 0 16px; font-size: 0.85rem; font-weight: bold; text-transform: uppercase; letter-spacing: 0.05em; color: rgba(255,255,255,0.7);">Geocoded Location SDoH Barriers</p>
              
              <div v-if="predictionModelResults" style="display: flex; flex-direction: column; gap: 12px; font-size: 0.8rem;">
                <div style="display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 4px;">
                  <span style="color: rgba(255,255,255,0.7);">Estimated Location</span>
                  <b style="color: white;">{{ predictionModelResults.city }}, {{ predictionModelResults.state }}</b>
                </div>
                <div style="display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 4px;">
                  <span style="color: rgba(255,255,255,0.7);">SVI Risk Score</span>
                  <b style="color: #f87171;">{{ predictionModelResults.overall_risk_score.toFixed(2) }} ({{ predictionModelResults.overall_risk_category }})</b>
                </div>
                
                <!-- Individual SDoH scores -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 8px;">
                  <div style="background: rgba(255,255,255,0.02); padding: 8px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.04);">
                    <span style="font-size: 0.7rem; color: rgba(255,255,255,0.5); display: block;">Healthcare Access</span>
                    <b style="color: white; font-size: 0.85rem;">{{ Math.round(predictionModelResults.scores.healthcare_access * 100) }}%</b>
                  </div>
                  <div style="background: rgba(255,255,255,0.02); padding: 8px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.04);">
                    <span style="font-size: 0.7rem; color: rgba(255,255,255,0.5); display: block;">Social Context</span>
                    <b style="color: white; font-size: 0.85rem;">{{ Math.round(predictionModelResults.scores.social_context * 100) }}%</b>
                  </div>
                  <div style="background: rgba(255,255,255,0.02); padding: 8px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.04);">
                    <span style="font-size: 0.7rem; color: rgba(255,255,255,0.5); display: block;">Food Security</span>
                    <b style="color: white; font-size: 0.85rem;">{{ Math.round(predictionModelResults.scores.food_security * 100) }}%</b>
                  </div>
                  <div style="background: rgba(255,255,255,0.02); padding: 8px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.04);">
                    <span style="font-size: 0.7rem; color: rgba(255,255,255,0.5); display: block;">Neighborhood Env</span>
                    <b style="color: white; font-size: 0.85rem;">{{ Math.round(predictionModelResults.scores.neighborhood_environment * 100) }}%</b>
                  </div>
                </div>
              </div>
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
            <div class="sparkline-container">
              <svg viewBox="0 0 80 30" class="spark-svg">
                <path 
                  fill="none" 
                  stroke="#3b82f6" 
                  stroke-width="1.8" 
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  :d="'M ' + getSparklinePoints(activeCommunity.metrics.hospRisk.sparkline)" 
                />
              </svg>
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
            <div class="sparkline-container">
              <svg viewBox="0 0 80 30" class="spark-svg">
                <path 
                  fill="none" 
                  stroke="#10b981" 
                  stroke-width="1.8" 
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  :d="'M ' + getSparklinePoints(activeCommunity.metrics.utilRisk.sparkline)" 
                />
              </svg>
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
            <div class="sparkline-container">
              <svg viewBox="0 0 80 30" class="spark-svg">
                <path 
                  fill="none" 
                  stroke="#8b5cf6" 
                  stroke-width="1.8" 
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  :d="'M ' + getSparklinePoints(activeCommunity.metrics.chronicRisk.sparkline)" 
                />
              </svg>
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
            <div class="sparkline-container">
              <svg viewBox="0 0 80 30" class="spark-svg">
                <path 
                  fill="none" 
                  stroke="#f59e0b" 
                  stroke-width="1.8" 
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  :d="'M ' + getSparklinePoints(activeCommunity.metrics.gapProb.sparkline)" 
                />
              </svg>
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
            <div class="sparkline-container">
              <svg viewBox="0 0 80 30" class="spark-svg">
                <path 
                  fill="none" 
                  stroke="#10b981" 
                  stroke-width="1.8" 
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  :d="'M ' + getSparklinePoints(activeCommunity.metrics.sdohImpact.sparkline)" 
                />
              </svg>
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
                  
                  <div class="toggle-pill-wrapper">
                    <button class="toggle-pill-btn" :class="{ active: activeTrendFilter === 'all' }" @click="activeTrendFilter = 'all'">All Risks</button>
                    <button class="toggle-pill-btn" :class="{ active: activeTrendFilter === 'hosp' }" @click="activeTrendFilter = 'hosp'">Hospitalization</button>
                    <button class="toggle-pill-btn" :class="{ active: activeTrendFilter === 'util' }" @click="activeTrendFilter = 'util'">Preventable Utilization</button>
                    <button class="toggle-pill-btn" :class="{ active: activeTrendFilter === 'chronic' }" @click="activeTrendFilter = 'chronic'">Chronic Disease</button>
                    <button class="toggle-pill-btn" :class="{ active: activeTrendFilter === 'gap' }" @click="activeTrendFilter = 'gap'">Care Gap</button>
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
                  <h4>{{ isAnalyzed ? 'Local Location SDoH Breakdown' : 'Risk by Geographic Area' }} <span v-if="!isAnalyzed" class="light">(Top 10)</span> <span class="info-tooltip-btn"><IconBase name="help" :size="11" /></span></h4>
                  
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
                        <th class="text-left">{{ isAnalyzed ? 'SDoH Barrier Domain' : 'Name' }}</th>
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
                <select v-model="activeCorrelationOutcome" class="select-outcome">
                  <option value="hosp">Hospitalization Risk</option>
                  <option value="util">Preventable Utilization</option>
                  <option value="chronic">Chronic Disease Risk</option>
                  <option value="gap">Care Gap Probability</option>
                </select>
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

.toggle-pill-wrapper {
  display: flex;
  background: #f1f5f9;
  border-radius: 8px;
  padding: 2.5px;
}

.toggle-pill-btn {
  border: none;
  background: transparent;
  padding: 4px 8px;
  font-size: 0.68rem;
  font-weight: 700;
  color: var(--text-secondary);
  border-radius: 6px;
  cursor: pointer;
  white-space: nowrap;
}

.toggle-pill-btn.active {
  background: #ffffff;
  color: var(--brand);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
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
</style>
