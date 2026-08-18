<script setup>
import { ref, computed } from 'vue'
import IconBase from '../components/dashboard/IconBase.vue'
import { patientData } from '../store/appState'

// View mode toggles
const activeView = ref('domain')

// Selected community
const selectedId = ref('cuyahoga')
const isLocationDropdownOpen = ref(false)
const countyOptionsList = [
  { id: 'cuyahoga', name: 'Cuyahoga County, OH' },
  { id: 'wayne', name: 'Wayne County, MI' },
  { id: 'marion', name: 'Marion County, IN' },
  { id: 'franklin', name: 'Franklin County, OH' }
]
const selectLocationCounty = (id) => {
  selectedId.value = id
  isLocationDropdownOpen.value = false
}

// Shared metadata for all communities
const communities = {
  cuyahoga: {
    name: 'Cuyahoga County, OH',
    state: 'Ohio',
    population: '1.25M',
    medianIncome: '$53,142',
    sviScore: '0.78',
    sviLevel: 'High',
    healthRisk: '0.72',
    healthRiskLevel: 'High',
    impact: '27%',
    domains: {
      social: { score: 72, level: 'High', class: 'red-text', comp: '8 pts vs state avg', arrow: 'arrow-up', trendClass: 'red-text' },
      healthcare: { score: 58, level: 'Moderate', class: 'orange-text', comp: '5 pts vs state avg', arrow: 'arrow-up', trendClass: 'green-text' },
      economic: { score: 64, level: 'Moderate', class: 'orange-text', comp: '6 pts vs state avg', arrow: 'arrow-up', trendClass: 'green-text' },
      environment: { score: 66, level: 'Moderate', class: 'orange-text', comp: '7 pts vs state avg', arrow: 'arrow-up', trendClass: 'green-text' },
      food: { score: 43, level: 'High', class: 'red-text', comp: '12 pts vs state avg', arrow: 'arrow-up', trendClass: 'red-text' }
    },
    factors: {
      social: [
        { label: 'Poverty', val: 0.82, level: 'High', barClass: 'red-bar' },
        { label: 'Unemployment', val: 0.71, level: 'High', barClass: 'red-bar' },
        { label: 'Education', val: 0.65, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Housing Instability', val: 0.78, level: 'High', barClass: 'red-bar' },
        { label: 'Transportation Access', val: 0.58, level: 'Moderate', barClass: 'orange-bar' }
      ],
      healthcare: [
        { label: 'Health Insurance Coverage', val: 0.62, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Primary Care Access', val: 0.55, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Preventive Care Access', val: 0.49, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Mental Health Providers', val: 0.41, level: 'High', barClass: 'red-bar' },
        { label: 'Specialist Availability', val: 0.63, level: 'Moderate', barClass: 'orange-bar' }
      ],
      economic: [
        { label: 'Median Household Income', val: 0.68, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Income Inequality', val: 0.63, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Employment Rate', val: 0.61, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Cost Burden', val: 0.57, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Financial Hardship', val: 0.69, level: 'High', barClass: 'red-bar' }
      ],
      environment: [
        { label: 'Air Quality (PM2.5)', val: 0.66, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Environmental Burden', val: 0.72, level: 'High', barClass: 'red-bar' },
        { label: 'Heat Exposure', val: 0.71, level: 'High', barClass: 'red-bar' },
        { label: 'Hazard Proximity', val: 0.64, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Green Space Access', val: 0.48, level: 'Moderate', barClass: 'orange-bar' }
      ],
      food: [
        { label: 'Food Desert Index', val: 0.78, level: 'High', barClass: 'red-bar' },
        { label: 'Distance to Healthy Food', val: 0.71, level: 'High', barClass: 'red-bar' },
        { label: 'Vehicle Access', val: 0.52, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'SNAP Participation', val: 0.43, level: 'High', barClass: 'red-bar' },
        { label: 'Food Insecurity', val: 0.76, level: 'High', barClass: 'red-bar' }
      ]
    },
    outcomes: [
      { label: 'Chronic Disease Prevalence', val: 0.78, barClass: 'blue-bar' },
      { label: 'Mental Health Risk', val: 0.72, barClass: 'blue-bar' },
      { label: 'Preventable Hospitalizations', val: 0.71, barClass: 'blue-bar' },
      { label: 'Low Birth Weight', val: 0.64, barClass: 'blue-bar' },
      { label: 'Life Expectancy', val: -0.58, barClass: 'red-bar-left' }
    ],
    needs: [
      { name: 'Food Access', level: 'High', colorClass: 'orange-box' },
      { name: 'Transportation Access', level: 'High', colorClass: 'purple-box' },
      { name: 'Environmental Burden', level: 'Medium', colorClass: 'green-box' }
    ],
    drivers: [
      { name: 'Housing Instability', pct: '82%', icon: 'home' },
      { name: 'Food Insecurity', pct: '74%', icon: 'pin' },
      { name: 'Transportation Barriers', pct: '68%', icon: 'trend' },
      { name: 'Environmental Exposure', pct: '52%', icon: 'bulb' },
      { name: 'Healthcare Accessibility', pct: '47%', icon: 'users' }
    ]
  },
  wayne: {
    name: 'Wayne County, MI',
    state: 'Michigan',
    population: '1.79M',
    medianIncome: '$45,821',
    sviScore: '0.88',
    sviLevel: 'Very High',
    healthRisk: '0.81',
    healthRiskLevel: 'Very High',
    impact: '39%',
    domains: {
      social: { score: 84, level: 'Very High', class: 'red-text', comp: '15 pts vs state avg', arrow: 'arrow-up', trendClass: 'red-text' },
      healthcare: { score: 48, level: 'High', class: 'red-text', comp: '12 pts vs state avg', arrow: 'arrow-up', trendClass: 'red-text' },
      economic: { score: 42, level: 'High', class: 'red-text', comp: '18 pts vs state avg', arrow: 'arrow-up', trendClass: 'red-text' },
      environment: { score: 76, level: 'Very High', class: 'red-text', comp: '14 pts vs state avg', arrow: 'arrow-up', trendClass: 'red-text' },
      food: { score: 31, level: 'Very High', class: 'red-text', comp: '24 pts vs state avg', arrow: 'arrow-up', trendClass: 'red-text' }
    },
    factors: {
      social: [
        { label: 'Poverty', val: 0.89, level: 'Very High', barClass: 'red-bar' },
        { label: 'Unemployment', val: 0.82, level: 'Very High', barClass: 'red-bar' },
        { label: 'Education', val: 0.76, level: 'High', barClass: 'red-bar' },
        { label: 'Housing Instability', val: 0.85, level: 'Very High', barClass: 'red-bar' },
        { label: 'Transportation Access', val: 0.68, level: 'High', barClass: 'red-bar' }
      ],
      healthcare: [
        { label: 'Health Insurance Coverage', val: 0.52, level: 'High', barClass: 'red-bar' },
        { label: 'Primary Care Access', val: 0.45, level: 'High', barClass: 'red-bar' },
        { label: 'Preventive Care Access', val: 0.38, level: 'High', barClass: 'red-bar' },
        { label: 'Mental Health Providers', val: 0.32, level: 'Very High', barClass: 'red-bar' },
        { label: 'Specialist Availability', val: 0.53, level: 'High', barClass: 'red-bar' }
      ],
      economic: [
        { label: 'Median Household Income', val: 0.54, level: 'High', barClass: 'red-bar' },
        { label: 'Income Inequality', val: 0.74, level: 'Very High', barClass: 'red-bar' },
        { label: 'Employment Rate', val: 0.51, level: 'High', barClass: 'red-bar' },
        { label: 'Cost Burden', val: 0.68, level: 'Very High', barClass: 'red-bar' },
        { label: 'Financial Hardship', val: 0.79, level: 'Very High', barClass: 'red-bar' }
      ],
      environment: [
        { label: 'Air Quality (PM2.5)', val: 0.78, level: 'Very High', barClass: 'red-bar' },
        { label: 'Environmental Burden', val: 0.84, level: 'Very High', barClass: 'red-bar' },
        { label: 'Heat Exposure', val: 0.81, level: 'Very High', barClass: 'red-bar' },
        { label: 'Hazard Proximity', val: 0.76, level: 'Very High', barClass: 'red-bar' },
        { label: 'Green Space Access', val: 0.38, level: 'High', barClass: 'red-bar' }
      ],
      food: [
        { label: 'Food Desert Index', val: 0.88, level: 'Very High', barClass: 'red-bar' },
        { label: 'Distance to Healthy Food', val: 0.81, level: 'Very High', barClass: 'red-bar' },
        { label: 'Vehicle Access', val: 0.42, level: 'High', barClass: 'red-bar' },
        { label: 'SNAP Participation', val: 0.31, level: 'Very High', barClass: 'red-bar' },
        { label: 'Food Insecurity', val: 0.86, level: 'Very High', barClass: 'red-bar' }
      ]
    },
    outcomes: [
      { label: 'Chronic Disease Prevalence', val: 0.85, barClass: 'blue-bar' },
      { label: 'Mental Health Risk', val: 0.79, barClass: 'blue-bar' },
      { label: 'Preventable Hospitalizations', val: 0.82, barClass: 'blue-bar' },
      { label: 'Low Birth Weight', val: 0.74, barClass: 'blue-bar' },
      { label: 'Life Expectancy', val: -0.68, barClass: 'red-bar-left' }
    ],
    needs: [
      { name: 'Food Desert Coverage', level: 'Critical', colorClass: 'red-box' },
      { name: 'Economic Security', level: 'Critical', colorClass: 'red-box' },
      { name: 'Environmental Burden', level: 'High', colorClass: 'orange-box' }
    ],
    drivers: [
      { name: 'Food Insecurity', pct: '88%', icon: 'pin' },
      { name: 'Housing Instability', pct: '85%', icon: 'home' },
      { name: 'Environmental Exposure', pct: '76%', icon: 'bulb' },
      { name: 'Economic Barriers', pct: '74%', icon: 'trend' },
      { name: 'Healthcare Access Gaps', pct: '62%', icon: 'users' }
    ]
  },
  marion: {
    name: 'Marion County, IN',
    state: 'Indiana',
    population: '967K',
    medianIncome: '$58,321',
    sviScore: '0.64',
    sviLevel: 'Mod-High',
    healthRisk: '0.68',
    healthRiskLevel: 'High',
    impact: '21%',
    domains: {
      social: { score: 64, level: 'Moderate', class: 'orange-text', comp: '4 pts vs state avg', arrow: 'arrow-up', trendClass: 'green-text' },
      healthcare: { score: 62, level: 'Moderate', class: 'orange-text', comp: '2 pts vs state avg', arrow: 'arrow-up', trendClass: 'green-text' },
      economic: { score: 55, level: 'Moderate', class: 'orange-text', comp: '5 pts vs state avg', arrow: 'arrow-up', trendClass: 'green-text' },
      environment: { score: 54, level: 'Moderate', class: 'orange-text', comp: '3 pts vs state avg', arrow: 'arrow-up', trendClass: 'green-text' },
      food: { score: 38, level: 'High', class: 'red-text', comp: '15 pts vs state avg', arrow: 'arrow-up', trendClass: 'red-text' }
    },
    factors: {
      social: [
        { label: 'Poverty', val: 0.68, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Unemployment', val: 0.61, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Education', val: 0.58, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Housing Instability', val: 0.69, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Transportation Access', val: 0.48, level: 'Moderate', barClass: 'orange-bar' }
      ],
      healthcare: [
        { label: 'Health Insurance Coverage', val: 0.68, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Primary Care Access', val: 0.59, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Preventive Care Access', val: 0.52, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Mental Health Providers', val: 0.49, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Specialist Availability', val: 0.67, level: 'Moderate', barClass: 'orange-bar' }
      ],
      economic: [
        { label: 'Median Household Income', val: 0.64, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Income Inequality', val: 0.58, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Employment Rate', val: 0.62, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Cost Burden', val: 0.49, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Financial Hardship', val: 0.58, level: 'Moderate', barClass: 'orange-bar' }
      ],
      environment: [
        { label: 'Air Quality (PM2.5)', val: 0.58, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Environmental Burden', val: 0.62, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Heat Exposure', val: 0.64, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Hazard Proximity', val: 0.58, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Green Space Access', val: 0.52, level: 'Moderate', barClass: 'orange-bar' }
      ],
      food: [
        { label: 'Food Desert Index', val: 0.72, level: 'High', barClass: 'red-bar' },
        { label: 'Distance to Healthy Food', val: 0.68, level: 'High', barClass: 'red-bar' },
        { label: 'Vehicle Access', val: 0.49, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'SNAP Participation', val: 0.38, level: 'High', barClass: 'red-bar' },
        { label: 'Food Insecurity', val: 0.70, level: 'High', barClass: 'red-bar' }
      ]
    },
    outcomes: [
      { label: 'Chronic Disease Prevalence', val: 0.68, barClass: 'blue-bar' },
      { label: 'Mental Health Risk', val: 0.65, barClass: 'blue-bar' },
      { label: 'Preventable Hospitalizations', val: 0.68, barClass: 'blue-bar' },
      { label: 'Low Birth Weight', val: 0.58, barClass: 'blue-bar' },
      { label: 'Life Expectancy', val: -0.49, barClass: 'red-bar-left' }
    ],
    needs: [
      { name: 'Food Access', level: 'High', colorClass: 'orange-box' },
      { name: 'Housing Quality', level: 'Medium', colorClass: 'green-box' },
      { name: 'Transportation Gaps', level: 'Medium', colorClass: 'purple-box' }
    ],
    drivers: [
      { name: 'Food Insecurity', pct: '72%', icon: 'pin' },
      { name: 'Transportation Gaps', pct: '68%', icon: 'trend' },
      { name: 'Housing Instability', pct: '64%', icon: 'home' },
      { name: 'Healthcare Access', pct: '52%', icon: 'users' },
      { name: 'Air Quality Burden', pct: '48%', icon: 'bulb' }
    ]
  },
  franklin: {
    name: 'Franklin County, OH',
    state: 'Ohio',
    population: '1.32M',
    medianIncome: '$66,921',
    sviScore: '0.52',
    sviLevel: 'Moderate',
    healthRisk: '0.55',
    healthRiskLevel: 'Moderate',
    impact: '12%',
    domains: {
      social: { score: 52, level: 'Moderate', class: 'orange-text', comp: '2 pts vs state avg', arrow: 'arrow-down', trendClass: 'green-text' },
      healthcare: { score: 71, level: 'Good', class: 'green-text', comp: '6 pts vs state avg', arrow: 'arrow-down', trendClass: 'green-text' },
      economic: { score: 68, level: 'Moderate', class: 'orange-text', comp: '4 pts vs state avg', arrow: 'arrow-down', trendClass: 'green-text' },
      environment: { score: 48, level: 'Moderate', class: 'orange-text', comp: '2 pts vs state avg', arrow: 'arrow-down', trendClass: 'green-text' },
      food: { score: 58, level: 'Moderate', class: 'orange-text', comp: '2 pts vs state avg', arrow: 'arrow-up', trendClass: 'green-text' }
    },
    factors: {
      social: [
        { label: 'Poverty', val: 0.54, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Unemployment', val: 0.48, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Education', val: 0.42, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Housing Instability', val: 0.58, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Transportation Access', val: 0.38, level: 'Moderate', barClass: 'orange-bar' }
      ],
      healthcare: [
        { label: 'Health Insurance Coverage', val: 0.78, level: 'Good', barClass: 'green-bar' },
        { label: 'Primary Care Access', val: 0.71, level: 'Good', barClass: 'green-bar' },
        { label: 'Preventive Care Access', val: 0.65, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Mental Health Providers', val: 0.58, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Specialist Availability', val: 0.74, level: 'Good', barClass: 'green-bar' }
      ],
      economic: [
        { label: 'Median Household Income', val: 0.72, level: 'Good', barClass: 'green-bar' },
        { label: 'Income Inequality', val: 0.52, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Employment Rate', val: 0.69, level: 'Good', barClass: 'green-bar' },
        { label: 'Cost Burden', val: 0.42, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Financial Hardship', val: 0.48, level: 'Moderate', barClass: 'orange-bar' }
      ],
      environment: [
        { label: 'Air Quality (PM2.5)', val: 0.48, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Environmental Burden', val: 0.52, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Heat Exposure', val: 0.49, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Hazard Proximity', val: 0.45, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Green Space Access', val: 0.62, level: 'Moderate', barClass: 'orange-bar' }
      ],
      food: [
        { label: 'Food Desert Index', val: 0.58, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Distance to Healthy Food', val: 0.52, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Vehicle Access', val: 0.64, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'SNAP Participation', val: 0.58, level: 'Moderate', barClass: 'orange-bar' },
        { label: 'Food Insecurity', val: 0.54, level: 'Moderate', barClass: 'orange-bar' }
      ]
    },
    outcomes: [
      { label: 'Chronic Disease Prevalence', val: 0.55, barClass: 'blue-bar' },
      { label: 'Mental Health Risk', val: 0.52, barClass: 'blue-bar' },
      { label: 'Preventable Hospitalizations', val: 0.54, barClass: 'blue-bar' },
      { label: 'Low Birth Weight', val: 0.48, barClass: 'blue-bar' },
      { label: 'Life Expectancy', val: -0.38, barClass: 'red-bar-left' }
    ],
    needs: [
      { name: 'Food Desert Pockets', level: 'Medium', colorClass: 'orange-box' },
      { name: 'Income Disparity', level: 'Medium', colorClass: 'purple-box' },
      { name: 'Green Space Access', level: 'Low', colorClass: 'green-box' }
    ],
    drivers: [
      { name: 'Housing Instability', pct: '58%', icon: 'home' },
      { name: 'Income Inequality', pct: '52%', icon: 'trend' },
      { name: 'Food Desert Pockets', pct: '48%', icon: 'pin' },
      { name: 'Air Quality Concerns', pct: '42%', icon: 'bulb' },
      { name: 'Transit Barriers', pct: '35%', icon: 'users' }
    ]
  }
}

const activeCommunity = computed(() => communities[selectedId.value])
</script>

<template>
  <div class="sdoh-insights-page">
    <div class="main-layout">
      
      <!-- 1. Central Content Panel -->
      <div class="content-body">
        
        <!-- Page Header -->
        <header class="page-header">
          <div>
            <h1>SDOH Insights</h1>
            <p class="subtitle">Why is this community at risk?</p>
            <p class="description">Explore the social, environmental, and economic factors that influence health outcomes.</p>
          </div>
        </header>

        <!-- National Sources Banner -->
        <section class="sources-banner">
          <div class="banner-left">
            <span class="info-dot-icon"><IconBase name="shield" :size="12" /></span>
            <p class="banner-text">Data includes 23 SDOH indicators from 4 national sources</p>
            <span class="info-tooltip-btn"><IconBase name="help" :size="12" /></span>
          </div>

          <div class="sources-chips">
            <span class="source-chip"><span class="chip-dot purple"></span> CDC/ATSDR SVI</span>
            <span class="source-chip"><span class="chip-dot teal"></span> U.S. Census ACS</span>
            <span class="source-chip"><span class="chip-dot orange"></span> USDA Food Access</span>
            <span class="source-chip"><span class="chip-dot green"></span> EPA EJScreen</span>
          </div>
        </section>

        <!-- SDOH Domains Overview circular widgets -->
        <section class="domains-overview-card card">
          <h4 class="section-title">SDOH Domains Overview</h4>
          
          <div class="domains-grid">
            <!-- Domain 1 -->
            <div class="domain-circle-item">
              <span class="domain-icon-box"><IconBase name="users" :size="16" /></span>
              <p class="domain-name">Social Conditions</p>
              
              <div class="radial-container">
                <svg viewBox="0 0 36 36" class="radial-svg">
                  <path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                  <path class="circle red" :stroke-dasharray="activeCommunity.domains.social.score + ', 100'" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                </svg>
                <div class="radial-center">
                  <span class="score">{{ activeCommunity.domains.social.score }}</span>
                  <span class="den">/100</span>
                </div>
              </div>
              <span class="level-lbl" :class="activeCommunity.domains.social.class">{{ activeCommunity.domains.social.level }}</span>
              <p class="comp-lbl" :class="activeCommunity.domains.social.trendClass">&uarr; {{ activeCommunity.domains.social.comp }}</p>
            </div>

            <!-- Domain 2 -->
            <div class="domain-circle-item">
              <span class="domain-icon-box"><IconBase name="shield" :size="16" /></span>
              <p class="domain-name">Healthcare Access</p>
              
              <div class="radial-container">
                <svg viewBox="0 0 36 36" class="radial-svg">
                  <path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                  <path class="circle blue" :stroke-dasharray="activeCommunity.domains.healthcare.score + ', 100'" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                </svg>
                <div class="radial-center">
                  <span class="score">{{ activeCommunity.domains.healthcare.score }}</span>
                  <span class="den">/100</span>
                </div>
              </div>
              <span class="level-lbl" :class="activeCommunity.domains.healthcare.class">{{ activeCommunity.domains.healthcare.level }}</span>
              <p class="comp-lbl" :class="activeCommunity.domains.healthcare.trendClass">&uarr; {{ activeCommunity.domains.healthcare.comp }}</p>
            </div>

            <!-- Domain 3 -->
            <div class="domain-circle-item">
              <span class="domain-icon-box"><IconBase name="trend" :size="16" /></span>
              <p class="domain-name">Economic Stability</p>
              
              <div class="radial-container">
                <svg viewBox="0 0 36 36" class="radial-svg">
                  <path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                  <path class="circle orange" :stroke-dasharray="activeCommunity.domains.economic.score + ', 100'" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                </svg>
                <div class="radial-center">
                  <span class="score">{{ activeCommunity.domains.economic.score }}</span>
                  <span class="den">/100</span>
                </div>
              </div>
              <span class="level-lbl" :class="activeCommunity.domains.economic.class">{{ activeCommunity.domains.economic.level }}</span>
              <p class="comp-lbl" :class="activeCommunity.domains.economic.trendClass">&uarr; {{ activeCommunity.domains.economic.comp }}</p>
            </div>

            <!-- Domain 4 -->
            <div class="domain-circle-item">
              <span class="domain-icon-box"><IconBase name="home" :size="16" /></span>
              <p class="domain-name">Neighborhood & Env</p>
              
              <div class="radial-container">
                <svg viewBox="0 0 36 36" class="radial-svg">
                  <path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                  <path class="circle green" :stroke-dasharray="activeCommunity.domains.environment.score + ', 100'" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                </svg>
                <div class="radial-center">
                  <span class="score">{{ activeCommunity.domains.environment.score }}</span>
                  <span class="den">/100</span>
                </div>
              </div>
              <span class="level-lbl" :class="activeCommunity.domains.environment.class">{{ activeCommunity.domains.environment.level }}</span>
              <p class="comp-lbl" :class="activeCommunity.domains.environment.trendClass">&uarr; {{ activeCommunity.domains.environment.comp }}</p>
            </div>

            <!-- Domain 5 -->
            <div class="domain-circle-item">
              <span class="domain-icon-box"><IconBase name="pin" :size="16" /></span>
              <p class="domain-name">Food Access</p>
              
              <div class="radial-container">
                <svg viewBox="0 0 36 36" class="radial-svg">
                  <path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                  <path class="circle red" :stroke-dasharray="activeCommunity.domains.food.score + ', 100'" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                </svg>
                <div class="radial-center">
                  <span class="score">{{ activeCommunity.domains.food.score }}</span>
                  <span class="den">/100</span>
                </div>
              </div>
              <span class="level-lbl" :class="activeCommunity.domains.food.class">{{ activeCommunity.domains.food.level }}</span>
              <p class="comp-lbl" :class="activeCommunity.domains.food.trendClass">&uarr; {{ activeCommunity.domains.food.comp }}</p>
            </div>
          </div>
        </section>

        <!-- SDOH Factors Breakdown column layout -->
        <section class="factors-breakdown-section">
          <div class="section-header">
            <h4>SDOH Factors Breakdown <span class="info-tooltip-btn"><IconBase name="help" :size="12" /></span></h4>
          </div>

          <div class="factors-columns-grid">
            <!-- 1. Social Conditions Factors -->
            <div class="card factor-col-card">
              <div class="col-header purple">
                <IconBase name="users" :size="13" /> <span>Social Conditions</span>
              </div>
              <ul class="indicators-bars-list">
                <li v-for="(fact, i) in activeCommunity.factors.social.slice(0, 3)" :key="i">
                  <div class="fact-top-info">
                    <span class="lbl">{{ fact.label }}</span>
                    <span class="val font-semibold">{{ fact.val }}</span>
                  </div>
                  <div class="bar-bg">
                    <div class="bar-fill" :class="fact.barClass" :style="{ width: (fact.val * 100) + '%' }"></div>
                  </div>
                  <span class="factor-level-tag" :class="fact.level.toLowerCase().replace(' ', '-')">{{ fact.level }}</span>
                </li>
              </ul>
            </div>

            <!-- 2. Healthcare Access Factors -->
            <div class="card factor-col-card">
              <div class="col-header blue">
                <IconBase name="shield" :size="13" /> <span>Healthcare Access</span>
              </div>
              <ul class="indicators-bars-list">
                <li v-for="(fact, i) in activeCommunity.factors.healthcare.slice(0, 3)" :key="i">
                  <div class="fact-top-info">
                    <span class="lbl">{{ fact.label }}</span>
                    <span class="val font-semibold">{{ fact.val }}</span>
                  </div>
                  <div class="bar-bg">
                    <div class="bar-fill" :class="fact.barClass" :style="{ width: (fact.val * 100) + '%' }"></div>
                  </div>
                  <span class="factor-level-tag" :class="fact.level.toLowerCase().replace(' ', '-')">{{ fact.level }}</span>
                </li>
              </ul>
            </div>

            <!-- 3. Economic Stability Factors -->
            <div class="card factor-col-card">
              <div class="col-header orange">
                <IconBase name="trend" :size="13" /> <span>Economic Stability</span>
              </div>
              <ul class="indicators-bars-list">
                <li v-for="(fact, i) in activeCommunity.factors.economic.slice(0, 3)" :key="i">
                  <div class="fact-top-info">
                    <span class="lbl">{{ fact.label }}</span>
                    <span class="val font-semibold">{{ fact.val }}</span>
                  </div>
                  <div class="bar-bg">
                    <div class="bar-fill" :class="fact.barClass" :style="{ width: (fact.val * 100) + '%' }"></div>
                  </div>
                  <span class="factor-level-tag" :class="fact.level.toLowerCase().replace(' ', '-')">{{ fact.level }}</span>
                </li>
              </ul>
            </div>

            <!-- 4. Neighborhood & Env Factors -->
            <div class="card factor-col-card">
              <div class="col-header green">
                <IconBase name="home" :size="13" /> <span>Neighborhood & Env</span>
              </div>
              <ul class="indicators-bars-list">
                <li v-for="(fact, i) in activeCommunity.factors.environment.slice(0, 3)" :key="i">
                  <div class="fact-top-info">
                    <span class="lbl">{{ fact.label }}</span>
                    <span class="val font-semibold">{{ fact.val }}</span>
                  </div>
                  <div class="bar-bg">
                    <div class="bar-fill" :class="fact.barClass" :style="{ width: (fact.val * 100) + '%' }"></div>
                  </div>
                  <span class="factor-level-tag" :class="fact.level.toLowerCase().replace(' ', '-')">{{ fact.level }}</span>
                </li>
              </ul>
            </div>

            <!-- 5. Food Access Factors -->
            <div class="card factor-col-card">
              <div class="col-header red">
                <IconBase name="pin" :size="13" /> <span>Food Access</span>
              </div>
              <ul class="indicators-bars-list">
                <li v-for="(fact, i) in activeCommunity.factors.food.slice(0, 3)" :key="i">
                  <div class="fact-top-info">
                    <span class="lbl">{{ fact.label }}</span>
                    <span class="val font-semibold">{{ fact.val }}</span>
                  </div>
                  <div class="bar-bg">
                    <div class="bar-fill" :class="fact.barClass" :style="{ width: (fact.val * 100) + '%' }"></div>
                  </div>
                  <span class="factor-level-tag" :class="fact.level.toLowerCase().replace(' ', '-')">{{ fact.level }}</span>
                </li>
              </ul>
            </div>
          </div>
        </section>

        <!-- Bottom Row (Health Outcomes / Timeline / Priority Areas) -->
        <section class="bottom-widgets-row">
          <!-- 1. SDOH vs Health Outcomes -->
          <div class="card outcomes-card">
            <h4>SDOH vs Health Outcomes <span class="info-tooltip-btn"><IconBase name="help" :size="12" /></span></h4>
            <p class="sub-label">Correlation with key health outcomes in this community</p>

            <ul class="outcomes-correlation-list">
              <li v-for="(out, i) in activeCommunity.outcomes" :key="i" :class="{ 'negative-row': out.val < 0 }">
                <span class="lbl">{{ out.label }}</span>
                
                <div class="correlation-bar-wrapper">
                  <!-- Centered zero bar line -->
                  <span class="zero-line"></span>

                  <div class="bar-channel">
                    <div 
                      v-if="out.val >= 0" 
                      class="bar-fill positive-bar" 
                      :style="{ width: (out.val * 100) + '%' }"
                    ></div>
                    <div 
                      v-else 
                      class="bar-fill negative-bar" 
                      :style="{ width: (Math.abs(out.val) * 100) + '%', right: '50%' }"
                    ></div>
                  </div>
                </div>

                <span class="val font-semibold" :class="out.val < 0 ? 'red-text' : 'blue-text'">
                  {{ out.val >= 0 ? '+' + out.val : out.val }}
                </span>
              </li>
            </ul>
          </div>

          <!-- 2. Trend Over Time Line Chart -->
          <div class="card timeline-card">
            <h4>Trend Over Time <span class="light">(last 12 months)</span></h4>
            
            <div class="legend-chips">
              <span class="chip"><span class="dot purple"></span> Social Vulnerability</span>
              <span class="chip"><span class="dot blue"></span> Health Risk</span>
              <span class="chip"><span class="dot orange"></span> Food Access</span>
              <span class="chip"><span class="dot green"></span> Environmental Risk</span>
            </div>

            <!-- SVG Timeline Line Graph -->
            <div class="chart-container">
              <svg viewBox="0 0 320 120" width="100%" height="100%">
                <!-- Grid Lines -->
                <line x1="0" y1="20" x2="320" y2="20" stroke="#f1f5f9" stroke-width="1" />
                <line x1="0" y1="50" x2="320" y2="50" stroke="#f1f5f9" stroke-width="1" />
                <line x1="0" y1="80" x2="320" y2="80" stroke="#f1f5f9" stroke-width="1" />
                <line x1="0" y1="110" x2="320" y2="110" stroke="#e2e8f0" stroke-width="1" />

                <!-- Values Grid Label -->
                <text x="0" y="15" class="axis-lbl">1.00</text>
                <text x="0" y="45" class="axis-lbl">0.75</text>
                <text x="0" y="75" class="axis-lbl">0.50</text>
                <text x="0" y="105" class="axis-lbl">0.25</text>

                <!-- Line paths (mock trend lines) -->
                <!-- Social Vulnerability (purple) -->
                <path d="M 10 32 Q 40 28, 80 40 T 160 35 T 240 38 T 310 25" fill="none" stroke="#8b5cf6" stroke-width="2" />
                <circle cx="310" cy="25" r="3" fill="#8b5cf6" />
                
                <!-- Health Risk (blue) -->
                <path d="M 10 48 Q 40 52, 80 45 T 160 50 T 240 43 T 310 38" fill="none" stroke="#3b82f6" stroke-width="2" />
                <circle cx="310" cy="38" r="3" fill="#3b82f6" />

                <!-- Food Access (orange) -->
                <path d="M 10 72 Q 40 68, 80 75 T 160 69 T 240 73 T 310 58" fill="none" stroke="#f59e0b" stroke-width="2" />
                <circle cx="310" cy="58" r="3" fill="#f59e0b" />

                <!-- Environmental Risk (green) -->
                <path d="M 10 92 Q 40 88, 80 94 T 160 88 T 240 91 T 310 82" fill="none" stroke="#10b981" stroke-width="2" />
                <circle cx="310" cy="82" r="3" fill="#10b981" />
              </svg>
            </div>
            
            <div class="month-axis">
              <span>Jun</span><span>Jul</span><span>Aug</span><span>Sep</span><span>Oct</span><span>Nov</span><span>Dec</span><span>Jan</span><span>Feb</span><span>Mar</span><span>Apr</span><span>May</span>
            </div>
          </div>

          <!-- 3. Areas Needing Attention List -->
          <div class="card attention-card">
            <h4>Areas Needing Attention</h4>
            <p class="subtitle">Focus on improving these factors to reduce health risk</p>
            
            <ul class="priorities-attention-list">
              <li v-for="(need, i) in activeCommunity.needs" :key="i">
                <span class="attention-icon-box" :class="need.colorClass">
                  <IconBase :name="need.name === 'Food Access' || need.name === 'Food Desert Coverage' ? 'pin' : (need.name === 'Transportation Access' || need.name === 'Transportation Gaps' ? 'trend' : 'bulb')" :size="15" />
                </span>
                
                <div class="need-details">
                  <b>{{ need.name }}</b>
                  <p>Priority: <span class="weight font-semibold">{{ need.level }}</span></p>
                </div>

                <button class="nav-arrow-btn">&gt;</button>
              </li>
            </ul>
          </div>
        </section>

      </div>

      <!-- 2. Right Community Snapshot Sidebar Rail -->
      <aside class="snapshot-rail">
        <h3 class="rail-title">Community Snapshot</h3>

        <!-- Interactive Location Selector Pin dropdown -->
        <div class="location-select-box custom-dropdown-box">
          <div class="custom-select-trigger" @click="isLocationDropdownOpen = !isLocationDropdownOpen">
            <span class="select-pin-icon"><IconBase name="pin" :size="16" /></span>
            <span class="selected-county-name font-bold">{{ communities[selectedId]?.name || 'Cuyahoga County, OH' }}</span>
            <span class="chevron-icon" :class="{ open: isLocationDropdownOpen }">
              <IconBase name="chevron-down" :size="12" />
            </span>
          </div>

          <!-- Click outside backdrop overlay -->
          <div v-if="isLocationDropdownOpen" class="dropdown-backdrop" @click="isLocationDropdownOpen = false"></div>

          <!-- Floating Custom Menu List -->
          <transition name="menu-fade">
            <ul v-if="isLocationDropdownOpen" class="custom-location-menu">
              <li 
                v-for="opt in countyOptionsList" 
                :key="opt.id" 
                class="location-menu-item"
                :class="{ active: selectedId === opt.id }"
                @click="selectLocationCounty(opt.id)"
              >
                <span class="item-pin">📍</span>
                <span class="item-label font-semibold">{{ opt.name }}</span>
                <span v-if="selectedId === opt.id" class="active-check">✓</span>
              </li>
            </ul>
          </transition>
        </div>

        <!-- Metric Snapshot stats grid -->
        <div class="card stats-summary-grid">
          <div class="stat-cell">
            <span class="lbl">Population</span>
            <b>{{ activeCommunity.population }}</b>
          </div>
          <div class="stat-cell">
            <span class="lbl">Median HH Income</span>
            <b>{{ activeCommunity.medianIncome }}</b>
          </div>
          <div class="stat-cell border-top">
            <span class="lbl">SVI Score</span>
            <b class="red-text">{{ activeCommunity.sviScore }} <span class="tag-lbl font-semibold">{{ activeCommunity.sviLevel }}</span></b>
          </div>
          <div class="stat-cell border-top">
            <span class="lbl">Health Risk Score</span>
            <b class="red-text">{{ activeCommunity.healthRisk }} <span class="tag-lbl font-semibold">{{ activeCommunity.healthRiskLevel }}</span></b>
          </div>
        </div>

        <!-- AI Explanation card -->
        <div class="card ai-explanation-card">
          <div class="sec-header">
            <h4>AI Explanation</h4>
            <span class="explain-badge"><IconBase name="shield" :size="11" /> Explainable AI</span>
          </div>

          <p class="explain-text">
            Elevated health risk in {{ activeCommunity.name }} is driven by high social vulnerability, limited food access, transportation barriers, and environmental exposures.
          </p>

          <p class="drivers-title">Key Drivers</p>
          <ul class="drivers-pct-list">
            <li v-for="(dr, i) in activeCommunity.drivers" :key="i">
              <span class="driver-icon"><IconBase :name="dr.icon" :size="13" /></span>
              <span class="lbl">{{ dr.name }}</span>
              <span class="val font-bold">{{ dr.pct }}</span>
            </li>
          </ul>
        </div>

        <!-- What does this mean card -->
        <div class="card meaning-explanation-card">
          <h4>What does this mean?</h4>
          <p>These factors can contribute to higher rates of chronic disease, poor health outcomes, and increased healthcare utilization.</p>
        </div>

        <!-- Population Impact indicator -->
        <div class="card impact-indicator-card">
          <div class="impact-header-row">
            <span class="icon-bubble"><IconBase name="users" :size="16" /></span>
            <div class="title-details">
              <h4>Population Impact</h4>
              <span class="badge" :class="activeCommunity.sviLevel.toLowerCase().replace(' ', '-')">{{ activeCommunity.sviLevel }}</span>
            </div>
          </div>
          <p class="impact-sub">{{ activeCommunity.impact }} of the population is living in high vulnerability areas.</p>
        </div>
      </aside>

    </div>
  </div>
</template>

<style scoped>
.sdoh-insights-page {
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

/* Central Column Content */
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
  margin: 0 0 2px;
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--text-primary);
}

.page-header .subtitle {
  margin: 0 0 2px;
  font-size: 1.15rem;
  font-weight: 700;
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

.header-actions .btn {
  background: #ffffff;
  border: 1px solid var(--border);
  color: var(--text-primary);
  font-size: 0.78rem;
  font-weight: 600;
  padding: 8px 16px;
}

/* Sources Banner badge */
.sources-banner {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: var(--radius-lg);
  padding: 12px 18px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.banner-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-dot-icon {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #dbeafe;
  color: #2563eb;
  display: flex;
  align-items: center;
  justify-content: center;
}

.banner-text {
  margin: 0;
  font-size: 0.76rem;
  font-weight: 700;
  color: #1e3a8a;
}

.info-tooltip-btn {
  color: #60a5fa;
  cursor: pointer;
}

.sources-chips {
  display: grid;
  grid-template-columns: repeat(4, auto);
  gap: 8px 24px;
}

@media (max-width: 1280px) {
  .sources-chips {
    grid-template-columns: repeat(2, auto);
  }
}

.source-chip {
  font-size: 0.72rem;
  font-weight: 600;
  color: #475569;
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.chip-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  display: inline-block;
}

.chip-dot.purple { background: #8b5cf6; }
.chip-dot.teal { background: #14b8a6; }
.chip-dot.orange { background: #f59e0b; }
.chip-dot.green { background: #10b981; }

/* Domains Overview circular cards */
.domains-overview-card {
  padding: 20px;
}

.section-title {
  margin: 0 0 16px;
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.domains-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}

.domain-circle-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 16px 12px;
  background: #fafbfe;
  position: relative;
}

.domain-icon-box {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #ffffff;
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  margin-bottom: 8px;
  box-shadow: var(--shadow-sm);
}

.domain-name {
  margin: 0 0 10px;
  font-size: 0.76rem;
  font-weight: 700;
  color: var(--text-primary);
}

.radial-container {
  position: relative;
  width: 68px;
  height: 68px;
  margin-bottom: 8px;
}

.radial-svg {
  display: block;
}

.circle-bg {
  fill: none;
  stroke: #e2e8f0;
  stroke-width: 2.8;
}

.circle {
  fill: none;
  stroke-width: 2.8;
  stroke-linecap: round;
}

.circle.red { stroke: #ef4444; }
.circle.blue { stroke: #3b82f6; }
.circle.orange { stroke: #f59e0b; }
.circle.green { stroke: #10b981; }

.radial-center {
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

.radial-center .score {
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--text-primary);
}

.radial-center .den {
  font-size: 0.54rem;
  color: var(--text-secondary);
  font-weight: 600;
}

.level-lbl {
  font-size: 0.7rem;
  font-weight: 700;
  margin-bottom: 4px;
}

.comp-lbl {
  margin: 0;
  font-size: 0.64rem;
  font-weight: 600;
}

/* Factors Breakdown column card */
.factors-breakdown-section {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.factors-breakdown-section .section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.factors-breakdown-section h4 {
  margin: 0;
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  display: flex;
  align-items: center;
  gap: 6px;
}

.toggle-view-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toggle-view-wrapper .lbl {
  font-size: 0.72rem;
  color: var(--text-secondary);
}

.capsule-toggle {
  display: inline-flex;
  background: #e2e8f0;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 3px;
}

.toggle-btn {
  border: none;
  background: transparent;
  padding: 5px 12px;
  font-size: 0.72rem;
  font-weight: 600;
  color: #475569;
  border-radius: 6px;
  cursor: pointer;
}

.toggle-btn.active {
  background: #2563eb;
  color: #ffffff;
}

.factors-columns-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}

.factor-col-card {
  padding: 14px;
  background: #ffffff;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 290px;
}

.col-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.74rem;
  font-weight: 700;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}

.col-header.purple { color: #8b5cf6; }
.col-header.blue { color: #3b82f6; }
.col-header.orange { color: #f59e0b; }
.col-header.green { color: #10b981; }
.col-header.red { color: #ef4444; }

.indicators-bars-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
}

.fact-top-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.68rem;
  margin-bottom: 2px;
}

.fact-top-info .lbl {
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 18ch;
}

.bar-bg {
  height: 5px;
  background: #e2e8f0;
  border-radius: 99px;
  overflow: hidden;
  margin-bottom: 2px;
}

.bar-fill {
  height: 100%;
  border-radius: 99px;
}

.bar-fill.red-bar { background: #ef4444; }
.bar-fill.orange-bar { background: #f59e0b; }
.bar-fill.green-bar { background: #10b981; }

.factor-level-tag {
  font-size: 0.58rem;
  font-weight: 700;
}

.factor-level-tag.high, .factor-level-tag.very-high { color: #ef4444; }
.factor-level-tag.moderate { color: #f59e0b; }
.factor-level-tag.good { color: #10b981; }

.view-all-link {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--brand);
  text-decoration: none;
  border-top: 1px solid var(--border);
  padding-top: 8px;
}

/* Bottom widgets row */
.bottom-widgets-row {
  display: grid;
  grid-template-columns: 1.1fr 1fr 0.9fr;
  gap: 16px;
}

.outcomes-card,
.timeline-card,
.attention-card {
  padding: 16px;
  background: #ffffff;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
}

.outcomes-card h4,
.timeline-card h4,
.attention-card h4 {
  margin: 0 0 4px;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-primary);
  text-transform: uppercase;
}

.outcomes-card .sub-label {
  margin: 0 0 12px;
  font-size: 0.7rem;
  color: var(--text-secondary);
}

.outcomes-correlation-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.outcomes-correlation-list li {
  display: grid;
  grid-template-columns: 100px 1fr 34px;
  align-items: center;
  gap: 10px;
  font-size: 0.68rem;
}

.outcomes-correlation-list .lbl {
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.correlation-bar-wrapper {
  position: relative;
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
}

.correlation-bar-wrapper .zero-line {
  position: absolute;
  left: 50%;
  top: 0;
  bottom: 0;
  width: 1.5px;
  background: #94a3b8;
  z-index: 2;
}

.bar-channel {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
}

.positive-bar {
  position: absolute;
  left: 50%;
  height: 100%;
  background: #3b82f6;
  border-radius: 0 4px 4px 0;
}

.negative-bar {
  position: absolute;
  height: 100%;
  background: #ef4444;
  border-radius: 4px 0 0 4px;
}

.outcomes-correlation-list .val {
  text-align: right;
  font-size: 0.72rem;
}

/* Timeline card trends lines */
.timeline-card .legend-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

.timeline-card .chip {
  font-size: 0.6rem;
  font-weight: 600;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 4px;
}

.timeline-card .chip .dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
}

.timeline-card .chip .dot.purple { background: #8b5cf6; }
.timeline-card .chip .dot.blue { background: #3b82f6; }
.timeline-card .chip .dot.orange { background: #f59e0b; }
.timeline-card .chip .dot.green { background: #10b981; }

.chart-container {
  height: 75px;
  margin-top: 4px;
}

.axis-lbl {
  font-size: 7px;
  fill: #94a3b8;
  font-weight: 600;
}

.month-axis {
  display: flex;
  justify-content: space-between;
  padding: 4px 6px 0;
  font-size: 7px;
  color: #94a3b8;
  font-weight: 700;
  border-top: 1px solid #f1f5f9;
}

/* Areas needing attention priority block */
.attention-card .subtitle {
  margin: 0 0 12px;
  font-size: 0.7rem;
  color: var(--text-secondary);
}

.priorities-attention-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.priorities-attention-list li {
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 8px 10px;
  display: flex;
  align-items: center;
  gap: 10px;
  background: #fdfdfd;
}

.attention-icon-box {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.attention-icon-box.orange-box { background: var(--amber-bg); color: var(--amber-text); }
.attention-icon-box.purple-box { background: var(--purple-bg); color: var(--purple); }
.attention-icon-box.green-box { background: var(--teal-bg); color: var(--teal); }
.attention-icon-box.red-box { background: var(--red-bg); color: var(--red-text); }

.need-details {
  display: flex;
  flex-direction: column;
  margin-right: auto;
  font-size: 0.7rem;
}

.need-details b {
  color: var(--text-primary);
}

.need-details p {
  margin: 1px 0 0;
  color: var(--text-secondary);
  font-size: 0.65rem;
}

.nav-arrow-btn {
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  font-size: 0.8rem;
  cursor: pointer;
}

/* 2. Right Community Snapshot Sidebar Rail */
.snapshot-rail {
  width: 320px;
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

.rail-title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--text-primary);
}

/* Custom Modern Dropdown Menu UI */
.custom-dropdown-box {
  position: relative;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 8px 12px;
  background: #ffffff;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.03);
  transition: all 0.2s ease;
  user-select: none;
}

.custom-dropdown-box:hover {
  border-color: #cbd5e1;
  box-shadow: var(--shadow-sm);
}

.custom-select-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  width: 100%;
}

.selected-county-name {
  font-size: 0.8rem;
  color: var(--text-primary);
  flex: 1;
}

.chevron-icon {
  color: #94a3b8;
  transition: transform 0.2s ease;
}

.chevron-icon.open {
  transform: rotate(180deg);
}

.dropdown-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 99;
}

.custom-location-menu {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: 10px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.12);
  padding: 6px;
  margin: 0;
  list-style: none;
  z-index: 100;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.location-menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.78rem;
  color: var(--text-primary);
  transition: background 0.15s ease;
}

.location-menu-item:hover {
  background: #f1f5f9;
}

.location-menu-item.active {
  background: #eff6ff;
  color: #1d4ed8;
  font-weight: 700;
}

.location-menu-item .active-check {
  margin-left: auto;
  font-weight: bold;
  color: #2563eb;
}

.menu-fade-enter-active,
.menu-fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.menu-fade-enter-from,
.menu-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.select-pin-icon {
  color: var(--brand);
}

/* Metric summary card */
.stats-summary-grid {
  padding: 0;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.stat-cell {
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 3px;
  background: #ffffff;
}

.stat-cell.border-top {
  border-top: 1px solid var(--border);
}

.stat-cell:nth-child(odd) {
  border-right: 1px solid var(--border);
}

.stat-cell .lbl {
  font-size: 0.65rem;
  color: var(--text-secondary);
}

.stat-cell b {
  font-size: 0.8rem;
  color: var(--text-primary);
}

.tag-lbl {
  font-size: 0.62rem;
  padding: 1px 5px;
  border-radius: 4px;
}

.red-text .tag-lbl {
  background: var(--red-bg);
  color: var(--red-text);
}

/* AI Explanation card */
.ai-explanation-card {
  padding: 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
}

.ai-explanation-card .sec-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.ai-explanation-card h4 {
  margin: 0;
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--text-primary);
}

.explain-badge {
  font-size: 0.62rem;
  font-weight: 700;
  color: var(--brand);
  background: var(--brand-light);
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  gap: 3px;
}

.explain-text {
  margin: 0 0 12px;
  font-size: 0.68rem;
  color: var(--text-secondary);
  line-height: 1.4;
}

.drivers-title {
  margin: 0 0 6px;
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--text-primary);
  text-transform: uppercase;
}

.drivers-pct-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.drivers-pct-list li {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.7rem;
}

.driver-icon {
  color: var(--text-secondary);
  display: flex;
  align-items: center;
}

.drivers-pct-list .lbl {
  color: var(--text-secondary);
  margin-right: auto;
}

.drivers-pct-list .val {
  color: var(--text-primary);
  font-size: 0.72rem;
}

/* Meaning card */
.meaning-explanation-card {
  padding: 14px;
  background: #f8fafc;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
}

.meaning-explanation-card h4 {
  margin: 0 0 4px;
  font-size: 0.74rem;
  font-weight: 700;
  color: var(--text-primary);
}

.meaning-explanation-card p {
  margin: 0;
  font-size: 0.68rem;
  color: var(--text-secondary);
  line-height: 1.4;
}

/* Population Impact card */
.impact-indicator-card {
  padding: 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
}

.impact-header-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.icon-bubble {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #e0f2fe;
  color: #0284c7;
  display: flex;
  align-items: center;
  justify-content: center;
}

.title-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.title-details h4 {
  margin: 0;
  font-size: 0.76rem;
  font-weight: 700;
  color: var(--text-primary);
}

.title-details .badge {
  font-size: 0.58rem;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 4px;
  align-self: flex-start;
}

.badge.high, .badge.very-high { background: var(--red-bg); color: var(--red-text); }
.badge.moderate, .badge.mod-high { background: var(--amber-bg); color: var(--amber-text); }

.impact-sub {
  margin: 0 0 10px;
  font-size: 0.68rem;
  color: var(--text-secondary);
  line-height: 1.4;
}

.view-risk-link {
  font-size: 0.68rem;
  font-weight: 700;
  color: var(--brand);
  text-decoration: none;
}

.view-risk-link:hover {
  text-decoration: underline;
}

/* ── RESPONSIVE OVERRIDES ── */
@media (max-width: 1100px) {
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

  .snapshot-rail {
    width: 100%;
    height: auto;
    border-left: none;
    border-top: 1px solid var(--border);
    overflow: visible;
    padding: 20px;
    flex-shrink: 0;
  }
  
  .domains-grid {
    grid-template-columns: repeat(3, 1fr);
  }

  .factors-columns-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 1280px) {
  .bottom-widgets-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .domains-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .bottom-widgets-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 580px) {
  .domains-grid {
    grid-template-columns: 1fr;
  }

  .factors-columns-grid {
    grid-template-columns: 1fr;
  }
  
  .sources-banner {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .sources-chips {
    justify-content: flex-start;
    flex-wrap: wrap;
  }
}
</style>
