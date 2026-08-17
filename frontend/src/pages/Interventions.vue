<script setup>
import { ref, computed } from 'vue'
import IconBase from '../components/dashboard/IconBase.vue'
import { isAnalyzed, patientData, mlPredictionResults } from '../store/appState'

// Community Selector State
const selectedCounty = ref('cuyahoga')

// Filter States
const selectedPriority = ref('All')
const selectedDomain = ref('All')
const selectedPopulation = ref('All')
const selectedType = ref('All')
const selectedStatus = ref('All')

// Modal States
const showCreateModal = ref(false)
const showOutreachModal = ref(false)

// Toast alerts state
const toastMsg = ref('')
const showToast = ref(false)

function triggerToast(msg) {
  toastMsg.value = msg
  showToast.value = true
  setTimeout(() => {
    showToast.value = false
  }, 3000)
}

// Modal Form Data
const newIntervention = ref({
  title: '',
  domain: 'Food Access',
  targetPop: '45K',
  impact: '12.5%',
  priority: 'High',
  status: 'Planned',
  description: ''
})

const outreachData = ref({
  campaignName: 'Winter Nutrition Outreach',
  channel: 'SMS Text Message',
  cohortSize: '24,500 members',
  startDate: '2025-11-15'
})

// Mock Interventions Data by county
const interventionsByCounty = {
  cuyahoga: {
    recommended: 48,
    highPriority: 16,
    impactedPop: '632K',
    expectedReached: '284K',
    potentialImpact: '24.7%',
    impactMembersReached: '142K',
    impactRiskReduction: '21.6%',
    impactVisitsAvoided: '8,432',
    impactCostSavings: '$4.2M',
    list: [
      {
        id: 'cuy-1',
        title: 'Expand Food Assistance Programs',
        domain: 'food',
        domainLabel: 'Food Access',
        description: 'Connect eligible members with local food assistance and nutrition programs.',
        drivers: ['Food Insecurity', 'Low Income'],
        targetPop: '125K Members',
        targetPopExact: '125,240 Members',
        expectedImpact: '↓ 18.4% Health Risk',
        priority: 'High',
        status: 'Active',
        whyIntervention: 'This community has a high rate of food insecurity and limited access to affordable, healthy foods.',
        keyDrivers: [
          { name: 'Food Insecurity', val: 74, color: 'red' },
          { name: 'Low Income', val: 68, color: 'orange' },
          { name: 'Unemployment', val: 52, color: 'orange' },
          { name: 'Transportation Barriers', val: 41, color: 'orange' }
        ],
        activities: [
          'Partner with local food banks and pantries',
          'Expand SNAP outreach and enrollment',
          'Provide nutrition education and support',
          'Mobile food distribution events'
        ],
        implementation: {
          startDate: 'Jun 1, 2025',
          owner: 'Community Health Team',
          partners: '8 Organizations',
          budget: '$245,000',
          duration: '12 months'
        }
      },
      {
        id: 'cuy-2',
        title: 'Transportation Support Initiative',
        domain: 'transit',
        domainLabel: 'Transportation',
        description: 'Provide transportation support for medical and preventive care.',
        drivers: ['Transportation Barriers', 'Healthcare Access'],
        targetPop: '98K Members',
        targetPopExact: '98,150 Members',
        expectedImpact: '↓ 14.2% Preventable Visits',
        priority: 'High',
        status: 'Planned',
        whyIntervention: 'Limited public transit and vehicle ownership rates lead to high medical appointment cancellation rates.',
        keyDrivers: [
          { name: 'Transit Barriers', val: 81, color: 'red' },
          { name: 'No Vehicle Ownership', val: 65, color: 'orange' },
          { name: 'Medical Missed Visits', val: 48, color: 'orange' }
        ],
        activities: [
          'Distribute free rideshare credits/vouchers',
          'Coordinate shuttle service to clinical hubs',
          'Deploy mobile medical clinics directly to neighborhoods'
        ],
        implementation: {
          startDate: 'Sep 1, 2025',
          owner: 'Transit Coordination Group',
          partners: '3 Transit Providers',
          budget: '$180,000',
          duration: '6 months'
        }
      },
      {
        id: 'cuy-3',
        title: 'Housing Stability Assistance',
        domain: 'housing',
        domainLabel: 'Housing & Utilities',
        description: 'Connect members to housing assistance and stability programs.',
        drivers: ['Housing Instability', 'High Rent Burden'],
        targetPop: '74K Members',
        targetPopExact: '74,300 Members',
        expectedImpact: '↓ 20.7% Health Risk',
        priority: 'High',
        status: 'Draft',
        whyIntervention: 'Substandard housing and high eviction rates directly aggravate asthma and mental distress cases.',
        keyDrivers: [
          { name: 'Rent Burden', val: 88, color: 'red' },
          { name: 'Substandard Housing', val: 72, color: 'red' },
          { name: 'Eviction Rates', val: 56, color: 'orange' }
        ],
        activities: [
          'Provide legal aid for eviction prevention',
          'Distribute emergency utility assistance funds',
          'Inspect homes for mold/lead hazard remediations'
        ],
        implementation: {
          startDate: 'Jan 15, 2026',
          owner: 'Housing Program Directorate',
          partners: '5 Municipal Agencies',
          budget: '$320,000',
          duration: '18 months'
        }
      },
      {
        id: 'cuy-4',
        title: 'Environmental Health Outreach',
        domain: 'environment',
        domainLabel: 'Environmental Health',
        description: 'Target outreach in areas with high environmental burden.',
        drivers: ['Environmental Exposure', 'Air Pollution'],
        targetPop: '56K Members',
        targetPopExact: '56,120 Members',
        expectedImpact: '↓ 11.3% Asthma Risk',
        priority: 'Medium',
        status: 'Active',
        whyIntervention: 'Industrial proximity and high particulate matter index increase respiratory crises.',
        keyDrivers: [
          { name: 'Air Pollution (PM2.5)', val: 76, color: 'red' },
          { name: 'Industrial Proximity', val: 62, color: 'orange' },
          { name: 'Asthma Hospitalization Rate', val: 59, color: 'orange' }
        ],
        activities: [
          'Distribute air purifiers to asthmatic members',
          'Plant urban foliage/green walls in buffer zones',
          'Conduct clean indoor air home assessments'
        ],
        implementation: {
          startDate: 'Mar 1, 2025',
          owner: 'Environmental Health Team',
          partners: '4 Green Non-profits',
          budget: '$95,000',
          duration: '12 months'
        }
      },
      {
        id: 'cuy-5',
        title: 'Mental Health Access Program',
        domain: 'mental',
        domainLabel: 'Mental Health',
        description: 'Increase access to local mental health and counseling services.',
        drivers: ['Mental Health Risk', 'Stress'],
        targetPop: '62K Members',
        targetPopExact: '62,400 Members',
        expectedImpact: '↓ 13.6% ER Visits',
        priority: 'Medium',
        status: 'Planned',
        whyIntervention: 'Isolation, socioeconomic stress, and lack of neighborhood psychiatrists escalate crisis cases.',
        keyDrivers: [
          { name: 'Reported Mental Distress', val: 69, color: 'orange' },
          { name: 'Provider Shortage Index', val: 64, color: 'orange' },
          { name: 'Substance Abuse Rates', val: 45, color: 'orange' }
        ],
        activities: [
          'Deploy tele-health mental counseling terminals',
          'Integrate therapy visits in community hubs',
          'Support peer-led trauma recovery circles'
        ],
        implementation: {
          startDate: 'Nov 1, 2025',
          owner: 'Behavioral Care Initiative',
          partners: '6 Counseling Centers',
          budget: '$150,000',
          duration: '12 months'
        }
      }
    ]
  },
  wayne: {
    recommended: 56,
    highPriority: 20,
    impactedPop: '720K',
    expectedReached: '340K',
    potentialImpact: '27.2%',
    impactMembersReached: '168K',
    impactRiskReduction: '24.1%',
    impactVisitsAvoided: '10,120',
    impactCostSavings: '$5.6M',
    list: [
      {
        id: 'way-1',
        title: 'Gleaners Mobile Food Pantries',
        domain: 'food',
        domainLabel: 'Food Access',
        description: 'Establish recurring mobile food distributions across Detroit food deserts.',
        drivers: ['Food Insecurity', 'Transit Barriers'],
        targetPop: '145K Members',
        targetPopExact: '145,500 Members',
        expectedImpact: '↓ 20.3% Health Risk',
        priority: 'High',
        status: 'Active',
        whyIntervention: 'Multiple communities in Wayne county lack a full-service supermarket within a 3-mile radius.',
        keyDrivers: [
          { name: 'Food Insecurity', val: 82, color: 'red' },
          { name: 'No Vehicle Access', val: 71, color: 'red' }
        ],
        activities: [
          'Schedule bi-weekly truck deliveries to public plazas',
          'Partner with local farmers to procure fresh produce'
        ],
        implementation: {
          startDate: 'Feb 1, 2025',
          owner: 'Mobile Pantry Taskforce',
          partners: '12 Organizations',
          budget: '$310,000',
          duration: '24 months'
        }
      }
    ]
  },
  marion: {
    recommended: 32,
    highPriority: 10,
    impactedPop: '410K',
    expectedReached: '185K',
    potentialImpact: '19.5%',
    impactMembersReached: '92K',
    impactRiskReduction: '17.2%',
    impactVisitsAvoided: '5,240',
    impactCostSavings: '$2.9M',
    list: [
      {
        id: 'mar-1',
        title: 'Diabetes Management Support',
        domain: 'health',
        domainLabel: 'Healthcare Access',
        description: 'Provide blood glucose monitors and continuous education to high-risk patients.',
        drivers: ['Chronic Disease Burden', 'Low Income'],
        targetPop: '48K Members',
        targetPopExact: '48,200 Members',
        expectedImpact: '↓ 15.6% ER Visits',
        priority: 'High',
        status: 'Active',
        whyIntervention: 'Diabetes complication rates remain 30% higher in low-income tracts compared to state averages.',
        keyDrivers: [
          { name: 'A1C Levels > 9%', val: 78, color: 'red' },
          { name: 'Medication Non-adherence', val: 62, color: 'orange' }
        ],
        activities: [
          'Deliver free glucose testing kits',
          'Offer weekly virtual nutrition workshops'
        ],
        implementation: {
          startDate: 'May 1, 2025',
          owner: 'Endocrinology Outreach Group',
          partners: '4 Clinics',
          budget: '$140,000',
          duration: '12 months'
        }
      }
    ]
  },
  franklin: {
    recommended: 38,
    highPriority: 12,
    impactedPop: '512K',
    expectedReached: '220K',
    potentialImpact: '21.8%',
    impactMembersReached: '110K',
    impactRiskReduction: '19.4%',
    impactVisitsAvoided: '6,800',
    impactCostSavings: '$3.5M',
    list: [
      {
        id: 'fra-1',
        title: 'Maternal Care Support Services',
        domain: 'health',
        domainLabel: 'Healthcare Access',
        description: 'Increase prenatal care access for pregnant mothers in social SVI zones.',
        drivers: ['Infant Mortality Risk', 'Clinical Access Gaps'],
        targetPop: '34K Members',
        targetPopExact: '34,600 Members',
        expectedImpact: '↓ 18.2% Birth Complications',
        priority: 'High',
        status: 'Planned',
        whyIntervention: 'SVI tracts show heightened risk for preterm birth rates and gaps in early prenatal screenings.',
        keyDrivers: [
          { name: 'Lack of Prenatal Care', val: 75, color: 'red' },
          { name: 'Socioeconomic Distress', val: 69, color: 'orange' }
        ],
        activities: [
          'Provide free rides to prenatal clinic appointments',
          'Deploy peer doula support programs'
        ],
        implementation: {
          startDate: 'Aug 1, 2025',
          owner: 'Women & Child Health Team',
          partners: '6 Local Clinics',
          budget: '$195,000',
          duration: '12 months'
        }
      }
    ]
  }
}

const activeCountyData = computed(() => {
  if (isAnalyzed.value && mlPredictionResults.value) {
    const barriers = (mlPredictionResults.value.sdoh_barriers && mlPredictionResults.value.sdoh_barriers.length > 0)
      ? mlPredictionResults.value.sdoh_barriers
      : [
          'High economic stability concerns',
          'Limited access to primary care providers',
          'Transportation accessibility limits'
        ]
    const list = barriers.map((barrier, index) => {
      const domains = ['food', 'transit', 'housing', 'environment', 'mental', 'health']
      const domainLabels = ['Food Access', 'Transportation', 'Housing Stability', 'Environmental Health', 'Mental Health', 'Healthcare Access']
      const domainIndex = index % domains.length
      
      return {
        id: `pat-int-${index}`,
        title: `Address ${barrier}`,
        domain: domains[domainIndex],
        domainLabel: domainLabels[domainIndex],
        description: `Direct action plan to address patient barrier: "${barrier}".`,
        drivers: [barrier],
        targetPop: '1 Patient',
        targetPopExact: '1 Active Patient',
        expectedImpact: '↓ 15.0% Patient Risk',
        priority: 'High',
        status: 'Planned',
        whyIntervention: `Identified SDoH barrier: "${barrier}". Resolving this barrier is key to improving health outcomes for ${patientData.value.name}.`,
        keyDrivers: [
          { name: barrier, val: 85, color: 'red' }
        ],
        activities: [
          'Coordinate primary care follow-up',
          'Deploy local community resources and services',
          'Track progress in next check-in call'
        ],
        implementation: {
          startDate: 'Immediate',
          owner: 'Community Care Coordinator',
          partners: '1 Care Team',
          budget: '$250',
          duration: '30 days'
        }
      }
    })

    return {
      recommended: list.length,
      highPriority: list.length,
      impactedPop: '1 Patient',
      expectedReached: '1 Patient',
      potentialImpact: 'SDoH Barrier Mitigation',
      impactMembersReached: '1',
      impactRiskReduction: 'High',
      impactVisitsAvoided: '1',
      impactCostSavings: 'N/A',
      list: list
    }
  }
  return interventionsByCounty[selectedCounty.value]
})

// Selected Intervention Detail Rail State
const selectedIntervention = ref(null)

// Auto-sync selected intervention
function syncSelected() {
  if (activeCountyData.value.list.length > 0) {
    selectedIntervention.value = activeCountyData.value.list[0]
  } else {
    selectedIntervention.value = null
  }
}
syncSelected()

function selectCounty(county) {
  selectedCounty.value = county
  syncSelected()
}

// Filters logic
const filteredList = computed(() => {
  let list = activeCountyData.value.list

  if (selectedPriority.value !== 'All') {
    list = list.filter(item => item.priority === selectedPriority.value)
  }
  if (selectedDomain.value !== 'All') {
    list = list.filter(item => item.domainLabel.toLowerCase().includes(selectedDomain.value.toLowerCase()))
  }
  if (selectedStatus.value !== 'All') {
    list = list.filter(item => item.status === selectedStatus.value)
  }

  return list
})

function resetFilters() {
  selectedPriority.value = 'All'
  selectedDomain.value = 'All'
  selectedPopulation.value = 'All'
  selectedType.value = 'All'
  selectedStatus.value = 'All'
  triggerToast('Filters reset successfully')
}

// Add Custom Intervention
function submitCustomIntervention() {
  if (!newIntervention.value.title) {
    triggerToast('Please provide a title')
    return
  }

  const customObj = {
    id: 'custom-' + Date.now(),
    title: newIntervention.value.title,
    domain: 'custom',
    domainLabel: newIntervention.value.domain,
    description: newIntervention.value.description || 'No description provided.',
    drivers: ['Custom Driver'],
    targetPop: newIntervention.value.targetPop + ' Members',
    targetPopExact: newIntervention.value.targetPop + ' Members',
    expectedImpact: '↓ ' + newIntervention.value.impact + ' Health Risk',
    priority: newIntervention.value.priority,
    status: newIntervention.value.status,
    whyIntervention: 'Created by User Campaign Officer.',
    keyDrivers: [
      { name: 'Custom Concern', val: 70, color: 'orange' }
    ],
    activities: ['Coordinate community meetings', 'Review progress quarterly'],
    implementation: {
      startDate: 'Dec 1, 2025',
      owner: 'Custom Team',
      partners: '1 Organization',
      budget: '$50,000',
      duration: '12 months'
    }
  }

  activeCountyData.value.list.push(customObj)
  selectedIntervention.value = customObj
  showCreateModal.value = false
  triggerToast('Custom intervention added successfully!')
  
  // reset form
  newIntervention.value = {
    title: '',
    domain: 'Food Access',
    targetPop: '45K',
    impact: '12.5%',
    priority: 'High',
    status: 'Planned',
    description: ''
  }
}

// Launch outreach
function launchOutreach() {
  showOutreachModal.value = false
  triggerToast(`Outreach Campaign "${outreachData.value.campaignName}" launched successfully!`)
}

// Get Domain Icon Color
function getDomainColor(domain) {
  switch (domain) {
    case 'food': return 'orange'
    case 'transit': return 'blue'
    case 'housing': return 'pink'
    case 'environment': return 'green'
    case 'mental': return 'rose'
    default: return 'purple'
  }
}
</script>

<template>
  <div class="interventions-page">
    
    <!-- Top-level Toast Popup -->
    <Transition name="fade">
      <div v-if="showToast" class="toast-popup">
        <IconBase name="shield" :size="14" />
        <span>{{ toastMsg }}</span>
      </div>
    </Transition>

    <!-- Create Custom Intervention Modal -->
    <div v-if="showCreateModal" class="modal-overlay">
      <div class="modal-box card">
        <div class="modal-header">
          <h3>Create Custom Intervention Plan</h3>
          <button class="close-modal-btn" @click="showCreateModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Intervention Title</label>
            <input v-model="newIntervention.title" type="text" placeholder="e.g. Clean Energy Outreach" />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>SDOH Domain</label>
              <select v-model="newIntervention.domain">
                <option>Food Access</option>
                <option>Healthcare Access</option>
                <option>Transportation</option>
                <option>Housing Stability</option>
                <option>Environmental Health</option>
              </select>
            </div>
            <div class="form-group">
              <label>Priority</label>
              <select v-model="newIntervention.priority">
                <option>High</option>
                <option>Medium</option>
                <option>Low</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Target Population size</label>
              <input v-model="newIntervention.targetPop" type="text" placeholder="e.g. 50K" />
            </div>
            <div class="form-group">
              <label>Expected Impact (%)</label>
              <input v-model="newIntervention.impact" type="text" placeholder="e.g. 15.4%" />
            </div>
          </div>
          <div class="form-group">
            <label>Description & Scope</label>
            <textarea v-model="newIntervention.description" rows="3" placeholder="Brief outline of target objectives..."></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn outlined" @click="showCreateModal = false">Cancel</button>
          <button class="btn primary" @click="submitCustomIntervention">Submit Plan</button>
        </div>
      </div>
    </div>

    <!-- Assign Outreach Campaign Modal -->
    <div v-if="showOutreachModal" class="modal-overlay">
      <div class="modal-box card">
        <div class="modal-header">
          <h3>Launch AI Outreach Campaign</h3>
          <button class="close-modal-btn" @click="showOutreachModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Campaign Name</label>
            <input v-model="outreachData.campaignName" type="text" />
          </div>
          <div class="form-group">
            <label>Outreach Channel</label>
            <select v-model="outreachData.channel">
              <option>SMS Text Message</option>
              <option>Email Newsletter</option>
              <option>Phone Call Outreach</option>
              <option>Direct Mailer Campaign</option>
            </select>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Audience Cohort Size</label>
              <input v-model="outreachData.cohortSize" type="text" readonly />
            </div>
            <div class="form-group">
              <label>Launch Date</label>
              <input v-model="outreachData.startDate" type="date" />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn outlined" @click="showOutreachModal = false">Cancel</button>
          <button class="btn primary" @click="launchOutreach">Launch Campaign</button>
        </div>
      </div>
    </div>

    <!-- Main Grid Content -->
    <div class="main-layout">
      
      <!-- 1. Left Content Area -->
      <div class="content-body">
        
        <!-- Header -->
        <header class="page-header">
          <div>
            <h1>Interventions</h1>
            <p class="description">AI-powered recommendations to reduce risk and improve health equity.</p>
          </div>
        </header>

        <!-- Patient Specific Context Banner -->
        <section v-if="isAnalyzed" class="card active-patient-banner" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; border: none; display: flex; justify-content: space-between; align-items: center; padding: 14px 20px; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.2); border-radius: 12px; margin-bottom: 8px; flex-shrink: 0;">
          <div style="display: flex; align-items: center; gap: 12px;">
            <div style="background: rgba(255,255,255,0.2); width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 18px;">🔬</div>
            <div>
              <h3 style="margin: 0; color: white; font-size: 0.95rem; font-weight: 700;">Viewing Interventions for: {{ patientData.name }}</h3>
              <p style="margin: 2px 0 0; font-size: 0.78rem; opacity: 0.9; color: rgba(255,255,255,0.95);">
                Clinical pathways generated from patient SDoH barriers using Neo4j knowledge graph pathways.
              </p>
            </div>
          </div>
        </section>

        <!-- Top Stat Cards Row -->
        <section class="stat-cards-grid">
          
          <div class="stat-card card">
            <div class="header-row">
              <span class="bubble green"><IconBase name="plus" :size="14" /></span>
              <span class="title">Interventions Recommended</span>
            </div>
            <div class="value-row">
              <h2>{{ activeCountyData.recommended }}</h2>
              <span class="trend green">&uarr; 16.7% <span class="trend-lbl">vs last 30d</span></span>
            </div>
            <div class="sparkline-wrapper">
              <svg viewBox="0 0 100 24" class="sparkline-svg green">
                <path d="M0,18 Q15,10 30,14 T60,8 T90,12" fill="none" stroke="#10b981" stroke-width="2" />
              </svg>
            </div>
          </div>

          <div class="stat-card card">
            <div class="header-row">
              <span class="bubble purple"><IconBase name="shield" :size="14" /></span>
              <span class="title">High Priority Interventions</span>
            </div>
            <div class="value-row">
              <h2>{{ activeCountyData.highPriority }}</h2>
              <span class="trend purple">&uarr; 23.1% <span class="trend-lbl">vs last 30d</span></span>
            </div>
            <div class="sparkline-wrapper">
              <svg viewBox="0 0 100 24" class="sparkline-svg purple">
                <path d="M0,15 Q15,19 30,10 T60,16 T90,5" fill="none" stroke="#8b5cf6" stroke-width="2" />
              </svg>
            </div>
          </div>

          

          <div class="stat-card card">
            <div class="header-row">
              <span class="bubble orange"><IconBase name="trend" :size="14" /></span>
              <span class="title">Expected Members Reached</span>
            </div>
            <div class="value-row">
              <h2>{{ activeCountyData.expectedReached }}</h2>
              <span class="trend orange">&uarr; 18.6% <span class="trend-lbl">vs last 30d</span></span>
            </div>
            <div class="sparkline-wrapper">
              <svg viewBox="0 0 100 24" class="sparkline-svg orange">
                <path d="M0,17 Q15,13 30,16 T60,9 T90,7" fill="none" stroke="#f59e0b" stroke-width="2" />
              </svg>
            </div>
          </div>

          <div class="stat-card card">
            <div class="header-row">
              <span class="bubble rose"><IconBase name="pulse" :size="14" /></span>
              <span class="title">Potential Impact (Risk Reduction)</span>
            </div>
            <div class="value-row">
              <h2>{{ activeCountyData.potentialImpact }}</h2>
              <span class="trend rose">&uarr; 3.2 pts <span class="trend-lbl">vs last 30d</span></span>
            </div>
            <div class="sparkline-wrapper">
              <svg viewBox="0 0 100 24" class="sparkline-svg rose">
                <path d="M0,14 Q15,16 30,11 T60,15 T90,4" fill="none" stroke="#f43f5e" stroke-width="2" />
              </svg>
            </div>
          </div>

        </section>

        <!-- Recommended Interventions Table -->
        <section class="recommended-interventions-section card">
          <div class="sec-header-row">
            <div>
              <h3>Recommended Interventions</h3>
              <p class="subtitle">AI-generated recommendations based on community needs and risk factors.</p>
            </div>
            <button class="filters-btn" @click="triggerToast('Advanced filter toggled')">
              <IconBase name="filter" :size="14" /> Filters
            </button>
          </div>

          <!-- Dropdowns Filter row -->
          <div class="filters-row">
            <div class="filter-select-col">
              <span class="lbl font-bold">Priority</span>
              <select v-model="selectedPriority">
                <option>All</option>
                <option>High</option>
                <option>Medium</option>
                <option>Low</option>
              </select>
            </div>

            <div class="filter-select-col">
              <span class="lbl font-bold">SDOH Domain</span>
              <select v-model="selectedDomain">
                <option value="All">All Domains</option>
                <option value="Food">Food Access</option>
                <option value="Transit">Transportation</option>
                <option value="Housing">Housing Stability</option>
                <option value="Environment">Environmental Health</option>
                <option value="Mental">Mental Health</option>
              </select>
            </div>

            <div class="filter-select-col">
              <span class="lbl font-bold">Population</span>
              <select v-model="selectedPopulation">
                <option value="All">All Populations</option>
                <option>Low-income Adults</option>
                <option>Seniors</option>
              </select>
            </div>

            <div class="filter-select-col">
              <span class="lbl font-bold">Intervention Type</span>
              <select v-model="selectedType">
                <option value="All">All Types</option>
                <option>Clinical Outreach</option>
                <option>Socioeconomic Support</option>
              </select>
            </div>

            <div class="filter-select-col">
              <span class="lbl font-bold">Status</span>
              <select v-model="selectedStatus">
                <option>All</option>
                <option>Active</option>
                <option>Planned</option>
                <option>Draft</option>
              </select>
            </div>

            <button class="reset-btn" @click="resetFilters">
              <IconBase name="trend" :size="12" style="transform: rotate(180deg);" /> Reset
            </button>
          </div>

          <!-- Interventions List Table -->
          <div class="interventions-list">
            <div 
              v-for="item in filteredList" 
              :key="item.id"
              class="intervention-row"
              :class="{ active: item.id === selectedIntervention?.id }"
              @click="selectedIntervention = item"
            >
              <div class="icon-cell">
                <span class="category-icon" :class="getDomainColor(item.domain)">
                  <IconBase 
                    :name="item.domain === 'food' ? 'pin' : item.domain === 'transit' ? 'trend' : item.domain === 'housing' ? 'home' : item.domain === 'environment' ? 'puzzle' : 'heart'" 
                    :size="15" 
                  />
                </span>
              </div>

              <div class="info-cell">
                <div class="title-badge-row">
                  <h4 class="item-title font-bold">{{ item.title }}</h4>
                  <span class="priority-badge-small font-bold" :class="item.priority.toLowerCase()">
                    {{ item.priority }}
                  </span>
                </div>
                <p class="item-desc">{{ item.description }}</p>
              </div>

              <div class="drivers-cell">
                <span class="header-lbl font-bold">Top Drivers</span>
                <div class="drivers-tags">
                  <span v-for="dr in item.drivers" :key="dr" class="driver-tag font-semibold">{{ dr }}</span>
                </div>
              </div>

              <div class="pop-cell">
                <span class="header-lbl font-bold">Target Population</span>
                <p class="pop-val font-semibold">{{ item.targetPop }}</p>
              </div>

              <div class="impact-cell">
                <span class="header-lbl font-bold">Expected Impact</span>
                <p class="impact-val font-bold">{{ item.expectedImpact }}</p>
              </div>

              <div class="priority-cell">
                <span class="header-lbl font-bold">Priority</span>
                <p class="priority-val font-semibold">
                  <span class="priority-dot" :class="item.priority.toLowerCase()"></span> {{ item.priority }}
                </p>
              </div>

              <div class="status-cell">
                <span class="status-pill font-bold" :class="item.status.toLowerCase()">{{ item.status }}</span>
              </div>

              <div class="action-cell">
                <button class="three-dots-btn" @click.stop="triggerToast('Actions panel opened')">
                  &bull;&bull;&bull;
                </button>
              </div>

            </div>

            <div v-if="filteredList.length === 0" class="empty-state">
              <IconBase name="alert" :size="24" class="empty-icon" />
              <h4>No matching interventions found.</h4>
              <p>Try clearing your active filter fields.</p>
            </div>
          </div>

          <div class="load-more-row">
            <button class="load-more-btn font-bold" @click="triggerToast('Loading additional recommended interventions...')">
              Load more interventions &darr;
            </button>
          </div>
        </section>

        <!-- Bottom Impact Overview Grid Section -->
        <section class="impact-overview-section card">
          <h3 class="sec-title">Impact Overview <span class="sub font-normal">(All Active Interventions)</span></h3>
          <div class="impact-grid">
            
            <div class="impact-card">
              <span class="lbl font-bold">Members Reached</span>
              <div class="val-row">
                <h4 class="val font-bold">{{ activeCountyData.impactMembersReached }}</h4>
                <span class="trend green">&uarr; 12.5% <span class="sub">vs last 30d</span></span>
              </div>
            </div>

            <div class="impact-card">
              <span class="lbl font-bold">Health Risk Reduction</span>
              <div class="val-row">
                <h4 class="val font-bold">{{ activeCountyData.impactRiskReduction }}</h4>
                <span class="trend green">&uarr; 3.4 pts <span class="sub">vs last 30d</span></span>
              </div>
            </div>

            <div class="impact-card">
              <span class="lbl font-bold">Preventable Visits Avoided</span>
              <div class="val-row">
                <h4 class="val font-bold">{{ activeCountyData.impactVisitsAvoided }}</h4>
                <span class="trend green">&uarr; 9.8% <span class="sub">vs last 30d</span></span>
              </div>
            </div>

            <div class="impact-card">
              <span class="lbl font-bold">Total Cost Impact</span>
              <div class="val-row">
                <h4 class="val font-bold">{{ activeCountyData.impactCostSavings }}</h4>
                <span class="trend-sub font-semibold">Projected annual savings</span>
              </div>
            </div>

            <div class="impact-card report-link-card" @click="triggerToast('Redirecting to Impact Report page...')">
              <div class="report-info">
                <span class="link-text font-bold">View Impact Report &rarr;</span>
                <p class="desc">Detailed savings breakdown</p>
              </div>
              <div class="chart-thumbnail">
                <!-- Mini Bar chart representation -->
                <svg viewBox="0 0 40 25" width="40" height="25">
                  <rect x="2" y="15" width="5" height="10" fill="#3b82f6" />
                  <rect x="9" y="8" width="5" height="17" fill="#3b82f6" />
                  <rect x="16" y="12" width="5" height="13" fill="#3b82f6" />
                  <rect x="23" y="5" width="5" height="20" fill="#3b82f6" />
                  <rect x="30" y="2" width="5" height="23" fill="#10b981" />
                </svg>
              </div>
            </div>

          </div>
        </section>

      </div>

      <!-- 2. Right Detail Sidebar Panel -->
      <aside class="intervention-detail-rail">
        <div v-if="selectedIntervention" class="detail-container">
          <div class="detail-header">
            <h3 class="title font-bold">Intervention Details</h3>
            <button class="close-btn" @click="selectedIntervention = null">&times;</button>
          </div>

          <!-- Main profile card -->
          <div class="profile-card card">
            <div class="card-inner-header">
              <span class="detail-icon" :class="getDomainColor(selectedIntervention.domain)">
                <IconBase 
                  :name="selectedIntervention.domain === 'food' ? 'pin' : selectedIntervention.domain === 'transit' ? 'trend' : selectedIntervention.domain === 'housing' ? 'home' : selectedIntervention.domain === 'environment' ? 'puzzle' : 'heart'" 
                  :size="20" 
                />
              </span>
              <div class="title-col">
                <h4 class="name font-bold">{{ selectedIntervention.title }}</h4>
                <p class="sub font-semibold">{{ selectedIntervention.domainLabel }}</p>
                <div class="badge-row">
                  <span class="status-badge font-bold" :class="selectedIntervention.status.toLowerCase()">
                    {{ selectedIntervention.status }}
                  </span>
                  <span class="priority-badge font-bold" :class="selectedIntervention.priority.toLowerCase()">
                    {{ selectedIntervention.priority }} Priority
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Why Intervention -->
          <section class="section 왜">
            <h4 class="section-title font-bold">Why this intervention?</h4>
            <p class="desc-text">{{ selectedIntervention.whyIntervention }}</p>
          </section>

          <!-- Key Drivers Progress bars -->
          <section class="section key-drivers">
            <h4 class="section-title font-bold">Key Drivers</h4>
            <div class="drivers-list">
              <div v-for="drv in selectedIntervention.keyDrivers" :key="drv.name" class="driver-progress-item">
                <div class="label-row font-semibold">
                  <span class="name">{{ drv.name }}</span>
                  <span class="val">{{ drv.val }}%</span>
                </div>
                <div class="bar-bg">
                  <div class="bar-fill" :class="drv.color" :style="{ width: drv.val + '%' }"></div>
                </div>
              </div>
            </div>
          </section>

          <!-- Target Population and Expected Impact side-by-side -->
          <section class="section stats-cards-row">
            <div class="stat-mini-card card">
              <span class="mini-icon blue"><IconBase name="users" :size="13" /></span>
              <div class="content">
                <h5 class="val font-bold">{{ selectedIntervention.targetPopExact }}</h5>
                <p class="lbl">Low-income members experiencing risks</p>
              </div>
            </div>
            <div class="stat-mini-card card">
              <span class="mini-icon green"><IconBase name="pulse" :size="13" /></span>
              <div class="content">
                <h5 class="val font-bold">{{ selectedIntervention.expectedImpact }}</h5>
                <p class="lbl">Potential overall health outcome boost</p>
              </div>
            </div>
          </section>

          <!-- Intervention Activities -->
          <section class="section activities">
            <h4 class="section-title font-bold">Intervention Activities</h4>
            <ul class="activities-checklist">
              <li v-for="act in selectedIntervention.activities" :key="act">
                <span class="check-bullet font-semibold">&check;</span>
                <span class="act-text font-semibold">{{ act }}</span>
              </li>
            </ul>
          </section>

          <!-- Implementation Details -->
          <section class="section implementation">
            <h4 class="section-title font-bold">Implementation</h4>
            <div class="details-table">
              
              <div class="detail-row-item">
                <span class="key font-semibold">Start Date</span>
                <span class="val font-bold">{{ selectedIntervention.implementation.startDate }}</span>
              </div>

              <div class="detail-row-item">
                <span class="key font-semibold">Owner</span>
                <span class="val font-semibold">{{ selectedIntervention.implementation.owner }}</span>
              </div>

              <div class="detail-row-item">
                <span class="key font-semibold">Partners</span>
                <span class="val font-semibold">{{ selectedIntervention.implementation.partners }}</span>
              </div>

              <div class="detail-row-item">
                <span class="key font-semibold">Budget</span>
                <span class="val font-bold">{{ selectedIntervention.implementation.budget }}</span>
              </div>

              <div class="detail-row-item">
                <span class="key font-semibold">Duration</span>
                <span class="val font-semibold">{{ selectedIntervention.implementation.duration }}</span>
              </div>

            </div>
          </section>

          

        </div>

        <div v-else class="no-selection-state">
          <IconBase name="shield" :size="32" class="placeholder-icon" />
          <p class="placeholder-text font-semibold">Select an intervention recommended in the list to view its AI rationale, driver distribution, active tasks, budget, and implementation owner.</p>
        </div>
      </aside>

    </div>

  </div>
</template>

<style scoped>
.interventions-page {
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

/* Modal Styling */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(15, 23, 42, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  backdrop-filter: blur(4px);
}

.modal-box {
  width: 480px;
  max-width: 90%;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: #ffffff;
  box-shadow: var(--shadow-lg);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.05rem;
  color: var(--text-primary);
  font-weight: 800;
}

.close-modal-btn {
  border: none;
  background: transparent;
  font-size: 1.4rem;
  cursor: pointer;
  color: var(--text-tertiary);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.form-group label {
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-secondary);
}

.form-group input, .form-group select, .form-group textarea {
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 0.8rem;
  color: var(--text-primary);
  background: #ffffff;
  outline: none;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  border-top: 1px solid var(--border);
  padding-top: 14px;
}

/* Grid Layout */
.main-layout {
  display: grid;
  grid-template-columns: 1fr 340px;
  height: 100%;
}

.content-body {
  padding: 24px 32px 32px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
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

.header-actions {
  display: flex;
  gap: 12px;
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

/* Card */
.card {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  padding: 16px;
}

/* Stat Cards Row */
.stat-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.stat-card {
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  position: relative;
  overflow: hidden;
}

.stat-card .header-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-card .bubble {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.bubble.green { background: #ecfdf5; color: #10b981; }
.bubble.purple { background: #f5f3ff; color: #8b5cf6; }
.bubble.blue { background: #eff6ff; color: #3b82f6; }
.bubble.orange { background: #fffbeb; color: #f59e0b; }
.bubble.rose { background: #fff1f2; color: #f43f5e; }

.stat-card .title {
  font-size: 0.64rem;
  font-weight: 700;
  color: var(--text-secondary);
  text-transform: uppercase;
}

.stat-card .value-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-top: 4px;
}

.stat-card h2 {
  margin: 0;
  font-size: 1.35rem;
  font-weight: 800;
  color: var(--text-primary);
}

.stat-card .trend {
  font-size: 0.65rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 2px;
}

.trend.green { color: #10b981; }
.trend.purple { color: #8b5cf6; }
.trend.blue { color: #3b82f6; }
.trend.orange { color: #f59e0b; }
.trend.rose { color: #f43f5e; }

.trend-lbl {
  color: var(--text-tertiary);
  font-weight: 500;
  margin-left: 2px;
}

.sparkline-wrapper {
  height: 20px;
  margin-top: 4px;
}

.sparkline-svg {
  width: 100%;
  height: 100%;
}

/* Recommended Interventions Card section */
.recommended-interventions-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sec-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sec-header-row h3 {
  margin: 0 0 2px;
  font-size: 0.95rem;
  font-weight: 800;
  color: var(--text-primary);
}

.sec-header-row .subtitle {
  margin: 0;
  font-size: 0.78rem;
  color: var(--text-secondary);
}

.filters-btn {
  background: #ffffff;
  border: 1px solid var(--border);
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

/* Filters row dropdowns */
.filters-row {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f8fafc;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
}

.filter-select-col {
  display: flex;
  flex-direction: column;
  gap: 3px;
  flex: 1;
}

.filter-select-col .lbl {
  font-size: 0.58rem;
  color: var(--text-secondary);
  text-transform: uppercase;
}

.filter-select-col select {
  border: 1px solid var(--border);
  background: #ffffff;
  font-size: 0.74rem;
  font-weight: 600;
  padding: 4px 6px;
  border-radius: 6px;
  outline: none;
  cursor: pointer;
  color: var(--text-primary);
}

.reset-btn {
  background: transparent;
  border: none;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  align-self: flex-end;
  padding-bottom: 6px;
}

/* Interventions List Table rows */
.interventions-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.intervention-row {
  display: grid;
  grid-template-columns: 36px minmax(0, 1.8fr) minmax(0, 1.2fr) minmax(0, 1fr) minmax(0, 1fr) minmax(0, 1fr) 80px 24px;
  align-items: center;
  gap: 12px;
  border: 1px solid var(--border);
  background: #ffffff;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.15s ease;
}

.info-cell,
.drivers-cell {
  min-width: 0;
}

.intervention-row:hover {
  border-color: #cbd5e1;
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

.intervention-row.active {
  border-color: var(--brand);
  background: #f0f4ff;
  box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.08);
}

.category-icon {
  width: 26px;
  height: 26px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.category-icon.orange { background: #fff9db; color: #d97706; }
.category-icon.blue { background: #e7f5ff; color: #2563eb; }
.category-icon.pink { background: #fdf2f8; color: #db2777; }
.category-icon.green { background: #e6fcf5; color: #059669; }
.category-icon.rose { background: #fff1f2; color: #e11d48; }

.info-cell .title-badge-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.item-title {
  margin: 0;
  font-size: 0.78rem;
  color: var(--text-primary);
}

.priority-badge-small {
  font-size: 0.54rem;
  padding: 1px 5px;
  border-radius: 4px;
  text-transform: uppercase;
}

.priority-badge-small.high { background: #fee2e2; color: #b91c1c; }
.priority-badge-small.medium { background: #ffedd5; color: #c2410c; }
.priority-badge-small.low { background: #f3f4f6; color: #4b5563; }

.item-desc {
  margin: 2px 0 0;
  font-size: 0.68rem;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-lbl {
  font-size: 0.56rem;
  color: var(--text-tertiary);
  text-transform: uppercase;
  display: block;
  margin-bottom: 2px;
}

.drivers-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.driver-tag {
  font-size: 0.62rem;
  background: #f1f5f9;
  color: var(--text-secondary);
  padding: 1px 5px;
  border-radius: 4px;
  white-space: nowrap;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pop-val, .impact-val, .priority-val {
  margin: 0;
  font-size: 0.68rem;
  color: var(--text-primary);
}

.impact-val {
  color: #16a34a;
}

.priority-val {
  display: flex;
  align-items: center;
  gap: 4px;
}

.priority-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
}
.priority-dot.high { background: #ef4444; }
.priority-dot.medium { background: #f97316; }
.priority-dot.low { background: #6b7280; }

.status-pill {
  font-size: 0.62rem;
  padding: 2px 8px;
  border-radius: 99px;
  display: inline-block;
}
.status-pill.active { background: #d1fae5; color: #065f46; }
.status-pill.planned { background: #dbeafe; color: #1e40af; }
.status-pill.draft { background: #f3e8ff; color: #6b21a8; }

.three-dots-btn {
  border: none;
  background: transparent;
  color: #94a3b8;
  cursor: pointer;
  font-size: 0.8rem;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 30px;
  text-align: center;
}

.empty-icon {
  color: #94a3b8;
  margin-bottom: 8px;
}

.empty-state h4 {
  margin: 0 0 4px;
  font-size: 0.8rem;
  color: var(--text-primary);
}

.empty-state p {
  margin: 0;
  font-size: 0.72rem;
  color: var(--text-secondary);
}

.load-more-row {
  display: flex;
  justify-content: center;
  margin-top: 8px;
}

.load-more-btn {
  background: transparent;
  border: none;
  font-size: 0.72rem;
  color: var(--brand);
  cursor: pointer;
}
.load-more-btn:hover {
  text-decoration: underline;
}

/* Impact Overview Card Section */
.impact-overview-section .sec-title {
  margin: 0 0 12px;
  font-size: 0.86rem;
  font-weight: 800;
  color: var(--text-primary);
}

.impact-overview-section .sub {
  color: var(--text-secondary);
}

.impact-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr) 1.2fr;
  gap: 12px;
}

.impact-card {
  background: #f8fafc;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.impact-card .lbl {
  font-size: 0.58rem;
  color: var(--text-secondary);
  text-transform: uppercase;
}

.impact-card .val-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-top: 6px;
}

.impact-card .val {
  margin: 0;
  font-size: 1.15rem;
  color: var(--text-primary);
}

.impact-card .trend {
  font-size: 0.62rem;
  color: #10b981;
}

.impact-card .trend-sub {
  font-size: 0.62rem;
  color: var(--text-tertiary);
  margin-top: 4px;
}

.impact-card.report-link-card {
  background: #eff6ff;
  border-color: #bfdbfe;
  cursor: pointer;
  flex-direction: row;
  align-items: center;
  transition: all 0.15s ease;
}

.impact-card.report-link-card:hover {
  background: #dbeafe;
}

.report-info {
  display: flex;
  flex-direction: column;
}

.report-info .link-text {
  font-size: 0.72rem;
  color: var(--brand);
}

.report-info .desc {
  margin: 2px 0 0;
  font-size: 0.6rem;
  color: var(--text-secondary);
}

.chart-thumbnail {
  display: flex;
}

/* Right Detail Sidebar Panel */
.intervention-detail-rail {
  background: #ffffff;
  border-left: 1px solid var(--border);
  overflow-y: auto;
}

.detail-container {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-header .title {
  margin: 0;
  font-size: 0.86rem;
  color: var(--text-primary);
}

.close-btn {
  border: none;
  background: transparent;
  font-size: 1.2rem;
  color: var(--text-tertiary);
  cursor: pointer;
  line-height: 1;
}

.profile-card {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 12px;
}

.card-inner-header {
  display: flex;
  gap: 10px;
}

.detail-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.detail-icon.orange { background: #fff9db; color: #f59e0b; }
.detail-icon.blue { background: #e7f5ff; color: #3b82f6; }
.detail-icon.pink { background: #fdf2f8; color: #ec4899; }
.detail-icon.green { background: #e6fcf5; color: #10b981; }
.detail-icon.rose { background: #fff1f2; color: #f43f5e; }

.title-col {
  display: flex;
  flex-direction: column;
}

.title-col .name {
  margin: 0;
  font-size: 0.84rem;
  color: var(--text-primary);
  line-height: 1.25;
}

.title-col .sub {
  margin: 2px 0 0;
  font-size: 0.68rem;
  color: var(--text-secondary);
}

.badge-row {
  display: flex;
  gap: 6px;
  margin-top: 4px;
}

.status-badge, .priority-badge {
  font-size: 0.54rem;
  padding: 1px 5px;
  border-radius: 4px;
}

.status-badge.active { background: #d1fae5; color: #065f46; }
.status-badge.planned { background: #dbeafe; color: #1e40af; }
.status-badge.draft { background: #f3e8ff; color: #6b21a8; }

.priority-badge.high { background: #fee2e2; color: #b91c1c; }
.priority-badge.medium { background: #ffedd5; color: #c2410c; }
.priority-badge.low { background: #f3f4f6; color: #4b5563; }

.section-title {
  margin: 0 0 6px;
  font-size: 0.65rem;
  color: var(--text-tertiary);
  text-transform: uppercase;
}

.desc-text {
  margin: 0;
  font-size: 0.72rem;
  color: var(--text-secondary);
  line-height: 1.4;
}

/* Key Drivers Progress bars */
.drivers-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.driver-progress-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.driver-progress-item .label-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.66rem;
  color: var(--text-primary);
}

.bar-bg {
  height: 4px;
  background: #f1f5f9;
  border-radius: 2px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 2px;
}
.bar-fill.red { background: #ef4444; }
.bar-fill.orange { background: #f97316; }

/* Stats Mini cards */
.stats-cards-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.stat-mini-card {
  padding: 10px;
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.mini-icon {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.mini-icon.blue { background: #eff6ff; color: #3b82f6; }
.mini-icon.green { background: #ecfdf5; color: #10b981; }

.stat-mini-card .content {
  display: flex;
  flex-direction: column;
}

.stat-mini-card .val {
  margin: 0;
  font-size: 0.78rem;
  color: var(--text-primary);
}

.stat-mini-card .lbl {
  margin: 1px 0 0;
  font-size: 0.58rem;
  color: var(--text-secondary);
  line-height: 1.25;
}

/* Activities checklist */
.activities-checklist {
  list-style: none;
  padding: 0;
  margin: 0 0 6px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.activities-checklist li {
  display: flex;
  gap: 8px;
  font-size: 0.7rem;
}

.check-bullet {
  color: #10b981;
}

.act-text {
  color: var(--text-secondary);
}

.view-plan-link {
  font-size: 0.68rem;
  color: var(--brand);
  text-decoration: none;
}
.view-plan-link:hover {
  text-decoration: underline;
}

/* Implementation Table */
.details-table {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.detail-row-item {
  display: flex;
  justify-content: space-between;
  border-bottom: 1px dashed var(--border);
  padding-bottom: 4px;
}

.detail-row-item .key {
  font-size: 0.68rem;
  color: var(--text-tertiary);
}

.detail-row-item .val {
  font-size: 0.68rem;
  color: var(--text-primary);
}

/* CTA Actions */
.cta-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 10px;
}

.cta-actions .btn {
  width: 100%;
  justify-content: center;
}

/* Placeholder details state */
.no-selection-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px;
  text-align: center;
  color: var(--text-tertiary);
}

.placeholder-icon {
  margin-bottom: 12px;
  color: #cbd5e1;
}

.placeholder-text {
  font-size: 0.74rem;
  line-height: 1.4;
  margin: 0;
}
</style>
