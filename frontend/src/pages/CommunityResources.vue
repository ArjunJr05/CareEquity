<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import IconBase from '../components/dashboard/IconBase.vue'
import { patientData, mlPredictionResults, predictionModelResults, isAnalyzed } from '../store/appState'
import { MAIN_BACKEND_URL } from '../config'

// MapLibre Worker Configuration
if (typeof window !== 'undefined' && maplibregl.getWorkerUrl && !maplibregl.getWorkerUrl()) {
  try {
    maplibregl.setWorkerUrl(`https://unpkg.com/maplibre-gl@${maplibregl.getVersion ? maplibregl.getVersion() : '5.1.0'}/dist/maplibre-gl-worker.mjs`)
  } catch (e) {
    console.warn("Could not set worker URL dynamically:", e)
  }
}

// Map Tile Styles (CartoDB Light Voyager & Dark Matter Raster Tiles)
const isDarkMap = ref(false)
const mapStyles = {
  light: {
    version: 8,
    sources: {
      'carto-light': {
        type: 'raster',
        tiles: [
          'https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
          'https://b.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
          'https://c.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png'
        ],
        tileSize: 256,
        attribution: '&copy; OpenStreetMap &copy; CARTO'
      }
    },
    layers: [
      {
        id: 'carto-light-layer',
        type: 'raster',
        source: 'carto-light',
        minzoom: 0,
        maxzoom: 20
      }
    ]
  },
  dark: {
    version: 8,
    sources: {
      'carto-dark': {
        type: 'raster',
        tiles: [
          'https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
          'https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
          'https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
        ],
        tileSize: 256,
        attribution: '&copy; OpenStreetMap &copy; CARTO'
      }
    },
    layers: [
      {
        id: 'carto-dark-layer',
        type: 'raster',
        source: 'carto-dark',
        minzoom: 0,
        maxzoom: 20
      }
    ]
  }
}

// Mobile View Toggle State ('list' or 'map')
const mobileTab = ref('list')

watch(mobileTab, (newTab) => {
  if (newTab === 'map' && mapInstance) {
    nextTick(() => {
      setTimeout(() => {
        mapInstance.resize()
      }, 100)
    })
  }
})

// Page & Filter States
const selectedId = ref('cuyahoga')
const searchQuery = ref('')
const activeCategoryFilter = ref('all')
const radiusFilter = ref('25 miles')
const isRadiusDropdownOpen = ref(false)
const radiusOptionsList = ['5 miles', '10 miles', '25 miles', '50 miles']

const selectRadius = (val) => {
  radiusFilter.value = val
  isRadiusDropdownOpen.value = false
  triggerToast(`Filtered resources within ${val}`)

  nextTick(() => {
    renderMapElements()
    if (mapInstance) {
      const maxMiles = parseFloat(val) || 25
      let targetZoom = 12.5
      if (maxMiles <= 5) targetZoom = 13.0
      else if (maxMiles <= 10) targetZoom = 11.8
      else if (maxMiles <= 25) targetZoom = 10.2
      else targetZoom = 8.8

      mapInstance.flyTo({
        center: [mapCenter.value.lng, mapCenter.value.lat],
        zoom: targetZoom,
        speed: 1.2
      })
    }
  })
}

const isRegionDropdownOpen = ref(false)
const countySearchQuery = ref('')

const regionOptions = [
  // Primary Health Equity Anchors
  { id: 'cuyahoga', name: 'Cuyahoga County, OH', city: 'Cleveland', lat: 41.4993, lon: -81.6944 },
  { id: 'wayne', name: 'Wayne County, MI', city: 'Detroit', lat: 42.3314, lon: -83.0458 },
  { id: 'marion', name: 'Marion County, IN', city: 'Indianapolis', lat: 39.7684, lon: -86.1581 },
  { id: 'franklin', name: 'Franklin County, OH', city: 'Columbus', lat: 39.9612, lon: -82.9988 },

  // Midwest & Regional Counties (as requested by user)
  { id: 'rice', name: 'Rice County, KS', city: 'Lyons', lat: 38.3582, lon: -98.2014 },
  { id: 'riley', name: 'Riley County, KS', city: 'Manhattan', lat: 39.1836, lon: -96.5717 },
  { id: 'rooks', name: 'Rooks County, KS', city: 'Stockton', lat: 39.2635, lon: -99.3082 },
  { id: 'rush', name: 'Rush County, KS', city: 'La Crosse', lat: 38.5303, lon: -99.3079 },
  { id: 'russell', name: 'Russell County, KS', city: 'Russell', lat: 38.8878, lon: -98.8576 },
  { id: 'saline', name: 'Saline County, KS', city: 'Salina', lat: 38.8403, lon: -97.6114 },
  { id: 'scott', name: 'Scott County, KS', city: 'Scott City', lat: 38.4820, lon: -100.9080 },
  { id: 'sedgwick', name: 'Sedgwick County, KS', city: 'Wichita', lat: 37.6872, lon: -97.3301 },
  { id: 'seward', name: 'Seward County, KS', city: 'Liberal', lat: 37.1081, lon: -100.8679 },
  { id: 'shawnee', name: 'Shawnee County, KS', city: 'Topeka', lat: 39.0558, lon: -95.6890 },
  { id: 'sheridan', name: 'Sheridan County, KS', city: 'Hoxie', lat: 39.3562, lon: -100.4435 },
  { id: 'sherman', name: 'Sherman County, KS', city: 'Goodland', lat: 39.3497, lon: -101.7132 },
  { id: 'smith', name: 'Smith County, KS', city: 'Smith Center', lat: 39.7797, lon: -98.7845 },
  { id: 'stafford', name: 'Stafford County, KS', city: 'St. John', lat: 38.0039, lon: -98.7562 },
  { id: 'stanton', name: 'Stanton County, KS', city: 'Johnson City', lat: 37.5683, lon: -101.7850 },
  { id: 'stevens', name: 'Stevens County, KS', city: 'Hugoton', lat: 37.1728, lon: -101.3482 },
  { id: 'sumner', name: 'Sumner County, KS', city: 'Wellington', lat: 37.2661, lon: -97.3975 },
  { id: 'thomas', name: 'Thomas County, KS', city: 'Colby', lat: 39.3908, lon: -100.8524 },
  { id: 'trego', name: 'Trego County, KS', city: 'WaKeeney', lat: 38.9839, lon: -99.8821 },
  { id: 'cook', name: 'Cook County, IL', city: 'Chicago', lat: 41.8781, lon: -87.6298 },
  { id: 'mahoning', name: 'Mahoning County, OH', city: 'Youngstown', lat: 41.1000, lon: -80.6500 },
  { id: 'summit', name: 'Summit County, OH', city: 'Akron', lat: 41.0814, lon: -81.5190 },
  { id: 'lorain', name: 'Lorain County, OH', city: 'Elyria', lat: 41.3684, lon: -82.1076 },
  { id: 'macomb', name: 'Macomb County, MI', city: 'Warren', lat: 42.5028, lon: -83.0288 },
  { id: 'genesee', name: 'Genesee County, MI', city: 'Flint', lat: 43.0125, lon: -83.6875 },
  { id: 'oakland', name: 'Oakland County, MI', city: 'Pontiac', lat: 42.6389, lon: -83.2911 },
  { id: 'hamilton', name: 'Hamilton County, IN', city: 'Carmel', lat: 39.9784, lon: -86.0142 },
  { id: 'hendricks', name: 'Hendricks County, IN', city: 'Danville', lat: 39.8153, lon: -86.5303 },
  { id: 'delaware', name: 'Delaware County, OH', city: 'Delaware', lat: 40.2987, lon: -83.0680 }
]

const filteredRegionOptions = computed(() => {
  if (!countySearchQuery.value.trim()) return regionOptions
  const q = countySearchQuery.value.toLowerCase()
  return regionOptions.filter(r => 
    r.name.toLowerCase().includes(q) || 
    (r.city && r.city.toLowerCase().includes(q))
  )
})

const selectedRegionLabel = computed(() => {
  if (customLat.value && customLng.value) {
    return customLocationName.value || `Custom (${customLat.value.toFixed(2)}, ${customLng.value.toFixed(2)})`
  }
  const match = regionOptions.find(r => r.id === selectedId.value)
  return match ? match.name : 'Select County / Region...'
})

function selectRegion(reg) {
  selectedId.value = reg.id
  customLat.value = null
  customLng.value = null
  isRegionDropdownOpen.value = false
  countySearchQuery.value = ''
  clearRoute()

  const comm = resourcesData[reg.id]
  const cLat = comm ? comm.centerLat : reg.lat
  const cLng = comm ? comm.centerLng : reg.lon

  fetchScrapedResources(cLat, cLng)
  if (mapInstance) {
    mapInstance.flyTo({
      center: [cLng, cLat],
      zoom: 12.5,
      speed: 1.2
    })
  }
}

function openCustomModalFromDropdown() {
  isRegionDropdownOpen.value = false
  isCoordModalOpen.value = true
}

// Custom Coordinates Modal State
const isCoordModalOpen = ref(false)
const inputLat = ref('')
const inputLng = ref('')
const customLocationName = ref('')
const customLat = ref(null)
const customLng = ref(null)

// Selected resource & routing state
const selectedResource = ref(null)
const bookmarkedIds = ref(new Set(['cuyahoga-food-1', 'cuyahoga-health-1']))

// Live Navigation & Route Line State
const activeRouteInfo = ref(null)
const isRoutingLoading = ref(false)

// Toast Notification State
const toastMsg = ref('')
const showToast = ref(false)

function triggerToast(msg) {
  toastMsg.value = msg
  showToast.value = true
  setTimeout(() => {
    showToast.value = false
  }, 3000)
}

function toggleBookmark(id) {
  if (bookmarkedIds.value.has(id)) {
    bookmarkedIds.value.delete(id)
    triggerToast('Resource removed from bookmarks')
  } else {
    bookmarkedIds.value.add(id)
    triggerToast('Resource bookmarked successfully')
  }
}

// Exact Haversine Distance Calculator (Miles)
function getHaversineDistanceMiles(lat1, lon1, lat2, lon2) {
  if (!lat1 || !lon1 || !lat2 || !lon2) return 1.0
  const R = 3958.8 // Earth radius in miles
  const dLat = (lat2 - lat1) * (Math.PI / 180)
  const dLon = (lon2 - lon1) * (Math.PI / 180)
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * (Math.PI / 180)) * Math.cos(lat2 * (Math.PI / 180)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return parseFloat((R * c).toFixed(1))
}

// Multi-Tier Resource Generator across 5mi, 10mi, 25mi, and 50mi zones
function buildTieredCommunityResources(cityName, centerLat, centerLng, prefix = 'res') {
  const rad = centerLat * (Math.PI / 180)
  const cosLat = Math.cos(rad) || 0.75

  const offsetCoord = (distMiles, angleDeg) => {
    const angleRad = angleDeg * (Math.PI / 180)
    const dLat = (distMiles / 69.0) * Math.cos(angleRad)
    const dLon = (distMiles / (69.0 * cosLat)) * Math.sin(angleRad)
    return {
      lat: parseFloat((centerLat + dLat).toFixed(4)),
      lon: parseFloat((centerLng + dLon).toFixed(4))
    }
  }

  const list = [
    // ── ZONE 1: Within 5 Miles (Downtown & Immediate Neighborhoods) ──
    {
      id: `${prefix}-camp-1`,
      name: `Free Mobile Health & SDOH Screening Truck`,
      category: 'campaign',
      categoryLabel: 'Live Campaign',
      verified: true,
      isCampaign: true,
      rating: 5.0,
      reviewsCount: 48,
      services: ['Blood pressure check', 'Glucose screening', 'SDOH Navigation', 'SNAP Signup'],
      hoursText: 'Today: 9:00 AM - 4:00 PM',
      eligibility: `Open to all ${cityName} residents. No insurance needed.`,
      address: `Downtown Civic Plaza, ${cityName}`,
      phone: '(555) 019-2831',
      website: 'careequity.org/mobile',
      ...offsetCoord(1.2, 45),
      about: 'Urgent mobile healthcare screening truck offering free vitals check, diabetes risk evaluation, and direct referral to social services.'
    },
    {
      id: `${prefix}-food-1`,
      name: `Greater Community Food Bank & Nutrition Hub`,
      category: 'food',
      categoryLabel: 'Food Assistance',
      verified: true,
      rating: 4.8,
      reviewsCount: 124,
      services: ['Emergency food pantry', 'SNAP assistance', 'Senior grocery boxes', 'Produce market'],
      hoursText: 'Mon - Fri: 8:30 AM - 4:30 PM',
      eligibility: 'All families in need. No proof of income required.',
      address: `1200 Center St, ${cityName}`,
      phone: '(555) 738-2067',
      website: 'communityfoodbank.org',
      ...offsetCoord(2.3, 110),
      about: 'Provides emergency food boxes, fresh vegetables, and SNAP enrollment support to eliminate food insecurity.'
    },
    {
      id: `${prefix}-health-1`,
      name: `${cityName} Primary Health Center`,
      category: 'health',
      categoryLabel: 'Healthcare Clinic',
      verified: true,
      rating: 4.6,
      reviewsCount: 92,
      services: ['Primary care', 'Chronic disease mgmt', 'Sliding-scale pharmacy', 'Pediatrics'],
      hoursText: 'Mon - Fri: 8:00 AM - 5:00 PM',
      eligibility: 'Uninsured & Medicaid accepted. Sliding fee scale.',
      address: `2500 Main Ave, ${cityName}`,
      phone: '(555) 778-7800',
      website: 'healthcenter.org',
      ...offsetCoord(3.1, 200),
      about: 'Comprehensive community health clinic offering primary medicine, preventive exams, and sliding-scale pharmacy aid.'
    },
    {
      id: `${prefix}-mental-1`,
      name: `Neighborhood Family Behavioral & Mental Health`,
      category: 'mental',
      categoryLabel: 'Mental Health',
      verified: true,
      rating: 4.5,
      reviewsCount: 76,
      services: ['Counseling', 'Psychiatry', 'Substance recovery support', 'Youth therapy'],
      hoursText: 'Mon - Fri: 9:00 AM - 6:00 PM',
      eligibility: 'All residents. Medicaid, Medicare & self-pay.',
      address: `1160 Clifton Blvd, ${cityName}`,
      phone: '(555) 281-2400',
      website: 'familybehavioral.org',
      ...offsetCoord(3.4, 280),
      about: 'Compassionate behavioral health agency providing individual counseling, substance treatment, and crisis intervention.'
    },
    {
      id: `${prefix}-transit-1`,
      name: `City Transit Mobility & Medical Transit Center`,
      category: 'transit',
      categoryLabel: 'Transportation',
      verified: true,
      rating: 4.2,
      reviewsCount: 64,
      services: ['Free medical transit passes', 'Paratransit service', 'Subsidized bus cards'],
      hoursText: 'Mon - Sun: 6:00 AM - 8:00 PM',
      eligibility: 'Low-income individuals, disabled & seniors qualify for free transit.',
      address: `400 Transit Way, ${cityName}`,
      phone: '(555) 621-9500',
      website: 'citytransit.gov',
      ...offsetCoord(1.8, 330),
      about: 'Subsidized transportation center ensuring patients never miss essential healthcare appointments due to transit barriers.'
    },
    {
      id: `${prefix}-housing-1`,
      name: `Community Housing Action & Utility Relief`,
      category: 'housing',
      categoryLabel: 'Housing & Utilities',
      verified: false,
      rating: 4.3,
      reviewsCount: 88,
      services: ['Utility bill assistance', 'Emergency rent relief', 'Tenant rights advocacy'],
      hoursText: 'Mon - Fri: 8:30 AM - 5:00 PM',
      eligibility: 'Low-to-moderate income households.',
      address: `850 Commerce Ave, ${cityName}`,
      phone: '(555) 574-7100',
      website: 'housingaction.org',
      ...offsetCoord(4.2, 85),
      about: 'Helps families maintain safe, affordable housing and provides emergency utility grant assistance.'
    },
    {
      id: `${prefix}-social-1`,
      name: `Step Forward Family & Social Empowerment Services`,
      category: 'social',
      categoryLabel: 'Social Services',
      verified: true,
      rating: 4.7,
      reviewsCount: 51,
      services: ['Cash assistance', 'Job training', 'Childcare vouchers', 'Emergency aid'],
      hoursText: 'Mon - Fri: 8:00 AM - 5:00 PM',
      eligibility: 'Income-eligible families.',
      address: `1800 Superior Ave, ${cityName}`,
      phone: '(555) 696-9077',
      website: 'stepforward.org',
      ...offsetCoord(2.9, 60),
      about: 'Community Action Agency fighting poverty by providing family support services and career development.'
    },
    {
      id: `${prefix}-gym-1`,
      name: `YMCA Community Wellness & Fitness Center`,
      category: 'gym',
      categoryLabel: 'Fitness & Wellness',
      verified: true,
      rating: 4.7,
      reviewsCount: 110,
      services: ['Subsidized fitness memberships', 'Diabetes prevention classes', 'Youth sports'],
      hoursText: 'Mon - Fri: 5:30 AM - 9:00 PM',
      eligibility: 'Financial aid available based on income.',
      address: `2200 Prospect Ave, ${cityName}`,
      phone: '(555) 344-7700',
      website: 'communityymca.org',
      ...offsetCoord(1.5, 160),
      about: 'Promotes cardiovascular wellness and chronic disease prevention through guided fitness and youth wellness.'
    },
    {
      id: `${prefix}-park-1`,
      name: `Lakeview Memorial Community Green Park`,
      category: 'park',
      categoryLabel: 'Parks & Open Space',
      verified: true,
      rating: 4.9,
      reviewsCount: 340,
      services: ['Paved walking trails', 'Outdoor exercise stations', 'Children playground'],
      hoursText: 'Daily: 6:00 AM - 10:00 PM',
      eligibility: 'Free public park.',
      address: `6500 Shoreway Blvd, ${cityName}`,
      phone: '(555) 635-3200',
      website: 'cityparks.gov',
      ...offsetCoord(3.8, 305),
      about: 'Expansive public park with green walking loops and fitness installations to foster active, healthy living.'
    },

    // ── ZONE 2: 5.1 to 10 Miles (Suburban & District Resources) ──
    {
      id: `${prefix}-food-zone2`,
      name: `Suburban Hope Pantry & Mobile Fresh Market`,
      category: 'food',
      categoryLabel: 'Food Assistance',
      verified: true,
      rating: 4.7,
      reviewsCount: 89,
      services: ['Drive-through pantry', 'Diaper bank', 'Produce distributions'],
      hoursText: 'Tue & Thu: 9:00 AM - 3:00 PM',
      eligibility: 'Open to all district residents.',
      address: `4410 Westway Pkwy, ${cityName} Suburbs`,
      phone: '(555) 882-1414',
      website: 'hopepantry.org',
      ...offsetCoord(6.8, 250),
      about: 'High-capacity suburban pantry distributing farm-fresh dairy, produce, and baby formula.'
    },
    {
      id: `${prefix}-health-zone2`,
      name: `MetroHealth Suburban Ambulatory Pavilion`,
      category: 'health',
      categoryLabel: 'Healthcare Clinic',
      verified: true,
      rating: 4.6,
      reviewsCount: 145,
      services: ['Specialist referrals', 'Dental clinic', 'Vision exams', 'Walk-in urgent care'],
      hoursText: 'Mon - Sat: 8:00 AM - 7:00 PM',
      eligibility: 'Sliding fee scale available for uninsured.',
      address: `7820 Ridge Rd, ${cityName} South`,
      phone: '(555) 910-3300',
      website: 'metrohealth.org/pavilion',
      ...offsetCoord(7.5, 185),
      about: 'Modern multi-specialty healthcare campus providing dental, optometry, and chronic care management.'
    },
    {
      id: `${prefix}-mental-zone2`,
      name: `Pathways Recovery & Adolescent Counseling Center`,
      category: 'mental',
      categoryLabel: 'Mental Health',
      verified: true,
      rating: 4.8,
      reviewsCount: 62,
      services: ['Intensive outpatient', 'Youth depression support', 'Family mediation'],
      hoursText: 'Mon - Fri: 8:00 AM - 6:00 PM',
      eligibility: 'Accepts Medicaid, Medicare & private insurance.',
      address: `3310 Eastland Blvd, ${cityName} East`,
      phone: '(555) 441-9922',
      website: 'pathwaysrecovery.org',
      ...offsetCoord(8.2, 70),
      about: 'Specialized youth and adult outpatient clinic focused on mental resiliency and holistic recovery.'
    },
    {
      id: `${prefix}-housing-zone2`,
      name: `Regional Homelessness Prevention & Rapid Rehousing`,
      category: 'housing',
      categoryLabel: 'Housing & Utilities',
      verified: true,
      rating: 4.4,
      reviewsCount: 57,
      services: ['Bridge housing', 'Security deposit grants', 'Eviction defense'],
      hoursText: 'Mon - Fri: 9:00 AM - 5:00 PM',
      eligibility: 'Individuals at immediate risk of homelessness.',
      address: `5120 Northway Dr, ${cityName}`,
      phone: '(555) 773-4001',
      website: 'rehousingnetwork.org',
      ...offsetCoord(9.1, 350),
      about: 'Coordinates transitional shelter and rental deposit grants to stabilize families in permanent homes.'
    },
    {
      id: `${prefix}-social-zone2`,
      name: `County Job & Family Services Suburban Branch`,
      category: 'social',
      categoryLabel: 'Social Services',
      verified: true,
      rating: 4.3,
      reviewsCount: 118,
      services: ['Medicaid enrollment', 'Cash assistance', 'WIC certification', 'Job matching'],
      hoursText: 'Mon - Fri: 8:00 AM - 4:30 PM',
      eligibility: 'County residents qualifying under state thresholds.',
      address: `6200 Brookpark Rd, ${cityName}`,
      phone: '(555) 398-8400',
      website: 'countyjfs.gov',
      ...offsetCoord(8.7, 215),
      about: 'County government service branch assisting with Medicaid, food stamps, and employment assistance.'
    },
    {
      id: `${prefix}-gym-zone2`,
      name: `Premier Community Rec Center & Aquatic Therapy`,
      category: 'gym',
      categoryLabel: 'Fitness & Wellness',
      verified: true,
      rating: 4.9,
      reviewsCount: 210,
      services: ['Low-impact water aerobics', 'Senior track', 'Nutrition counseling'],
      hoursText: 'Mon - Sat: 6:00 AM - 9:00 PM',
      eligibility: 'Community memberships with income discounts.',
      address: `8900 Broadview Rd, ${cityName}`,
      phone: '(555) 526-9000',
      website: 'communityreccenter.org',
      ...offsetCoord(7.8, 140),
      about: 'State-of-the-art recreation center featuring therapy pools and cardio rehabilitation facilities.'
    },
    {
      id: `${prefix}-park-zone2`,
      name: `Valley Reservation Nature Trails & Fitness Loop`,
      category: 'park',
      categoryLabel: 'Parks & Open Space',
      verified: true,
      rating: 4.9,
      reviewsCount: 420,
      services: ['Paved bike trail', 'Nature education center', 'Shaded fitness stations'],
      hoursText: 'Daily: 6:00 AM - 11:00 PM',
      eligibility: 'Free public reservation.',
      address: `10100 Valley Pkwy, ${cityName}`,
      phone: '(555) 351-6300',
      website: 'metroparks.org/valley',
      ...offsetCoord(9.4, 275),
      about: 'Scenic wooded park system offering miles of accessible trails for physical and mental relaxation.'
    },

    // ── ZONE 3: 10.1 to 25 Miles (Metropolitan & Tri-County Network) ──
    {
      id: `${prefix}-health-zone3`,
      name: `University Health Medical Center & Trauma Hub`,
      category: 'health',
      categoryLabel: 'Healthcare Clinic',
      verified: true,
      rating: 4.9,
      reviewsCount: 512,
      services: ['Cardiovascular center', 'Comprehensive oncology', '24/7 Emergency trauma', 'Charity care'],
      hoursText: 'Open 24 Hours / 7 Days',
      eligibility: 'All patients. Financial assistance program available.',
      address: `11100 Euclid Ave, Metro Campus`,
      phone: '(555) 844-1000',
      website: 'universityhealth.org',
      ...offsetCoord(14.5, 55),
      about: 'Major tertiary academic medical hospital providing advanced specialist care and indigent healthcare coverage.'
    },
    {
      id: `${prefix}-food-zone3`,
      name: `Regional Food Bank Logistics & Warehouse Distribution`,
      category: 'food',
      categoryLabel: 'Food Assistance',
      verified: true,
      rating: 4.9,
      reviewsCount: 310,
      services: ['Bulk pantry distribution', 'School backpack meals', 'Mobile pantry fleets'],
      hoursText: 'Mon - Fri: 7:30 AM - 4:30 PM',
      eligibility: 'Non-profit food distributors and regional families.',
      address: `15500 Waterloo Rd, Metro East`,
      phone: '(555) 738-2000',
      website: 'regionalfoodbank.org',
      ...offsetCoord(16.8, 80),
      about: 'Logistics distribution hub providing over 50 million pounds of food annually across 6 counties.'
    },
    {
      id: `${prefix}-mental-zone3`,
      name: `Metro Comprehensive Behavioral Health Institute`,
      category: 'mental',
      categoryLabel: 'Mental Health',
      verified: true,
      rating: 4.7,
      reviewsCount: 160,
      services: ['24/7 Crisis triage', 'Inpatient psychiatric care', 'Dual-diagnosis recovery'],
      hoursText: 'Open 24/7 Crisis Line',
      eligibility: 'Immediate admission for psychiatric crises regardless of insurance.',
      address: `4500 Metro Dr, North Metro`,
      phone: '(555) 961-4700',
      website: 'behavioralhealthinstitute.org',
      ...offsetCoord(18.2, 310),
      about: 'Round-the-clock emergency mental health hospital stabilizing acute mental and emotional distress.'
    },
    {
      id: `${prefix}-housing-zone3`,
      name: `Metropolitan Area Housing Authority Central`,
      category: 'housing',
      categoryLabel: 'Housing & Utilities',
      verified: true,
      rating: 4.2,
      reviewsCount: 195,
      services: ['Section 8 voucher administration', 'Public housing applications', 'Senior subsidized towers'],
      hoursText: 'Mon - Fri: 8:00 AM - 4:00 PM',
      eligibility: 'HUD income-qualifying applicants.',
      address: `1441 W 25th St, Central Metro`,
      phone: '(555) 344-1300',
      website: 'metrohousing.org',
      ...offsetCoord(13.2, 190),
      about: 'Manages affordable subsidized public housing and vouchers for low-income seniors and families.'
    },
    {
      id: `${prefix}-transit-zone3`,
      name: `Regional Transit Authority Multi-County Terminal`,
      category: 'transit',
      categoryLabel: 'Transportation',
      verified: true,
      rating: 4.4,
      reviewsCount: 88,
      services: ['Intercity express routes', 'Vanpool matching', 'Medical transit subsidy'],
      hoursText: 'Daily: 5:00 AM - 11:30 PM',
      eligibility: 'General public & subsidized commuters.',
      address: `700 Intercity Blvd, Metro Transit Hub`,
      phone: '(555) 566-0100',
      website: 'regionaltransit.gov',
      ...offsetCoord(21.0, 160),
      about: 'Connects outlying rural and suburban communities to central medical complexes and employment sectors.'
    },
    {
      id: `${prefix}-social-zone3`,
      name: `Salvation Army Regional Social Services Center`,
      category: 'social',
      categoryLabel: 'Social Services',
      verified: true,
      rating: 4.8,
      reviewsCount: 140,
      services: ['Emergency disaster assistance', 'Family financial coaching', 'Clothing boutique'],
      hoursText: 'Mon - Fri: 9:00 AM - 4:30 PM',
      eligibility: 'Open to all individuals in need.',
      address: `2507 E 22nd St, Metro Central`,
      phone: '(555) 619-9111',
      website: 'salvationarmy.org',
      ...offsetCoord(15.4, 120),
      about: 'Emergency social service center offering food, winter coats, utility support, and case management.'
    },
    {
      id: `${prefix}-park-zone3`,
      name: `Metropolitan Lakefront State Nature Preserve`,
      category: 'park',
      categoryLabel: 'Parks & Open Space',
      verified: true,
      rating: 4.9,
      reviewsCount: 680,
      services: ['Lakefront walking trail', 'Public fishing pier', 'Kayaking & outdoor fitness'],
      hoursText: 'Daily: 6:00 AM - Dusk',
      eligibility: 'Free public nature preserve.',
      address: `8700 Lakefront Pkwy, East Coast`,
      phone: '(555) 881-4600',
      website: 'stateparks.gov/lakefront',
      ...offsetCoord(22.8, 35),
      about: 'Pristine coastal park offering waterfront recreation and ecological walking paths for public wellness.'
    },

    // ── ZONE 4: 25.1 to 50 Miles (Regional / Multi-County Health Network) ──
    {
      id: `${prefix}-health-zone4`,
      name: `Regional Memorial Health System & Rural Outpatient Clinic`,
      category: 'health',
      categoryLabel: 'Healthcare Clinic',
      verified: true,
      rating: 4.8,
      reviewsCount: 230,
      services: ['Rural primary care', 'Telehealth consultations', 'Preventive screenings', 'Mobile clinic'],
      hoursText: 'Mon - Fri: 8:00 AM - 5:00 PM',
      eligibility: 'Serving rural and regional county residents.',
      address: `14200 State Route 42, Regional North`,
      phone: '(555) 832-7700',
      website: 'regionalmemorial.org',
      ...offsetCoord(34.5, 15),
      about: 'Extends medical services into underserved rural and semi-rural areas across adjoining counties.'
    },
    {
      id: `${prefix}-food-zone4`,
      name: `Agricultural Harvest Network & Tri-County Food Consortium`,
      category: 'food',
      categoryLabel: 'Food Assistance',
      verified: true,
      rating: 4.9,
      reviewsCount: 175,
      services: ['Farm-to-family produce boxes', 'Rural pantry delivery', 'Nutritional support'],
      hoursText: 'Mon - Thu: 8:00 AM - 4:00 PM',
      eligibility: 'All rural and county families facing food insecurity.',
      address: `890 Harvest Way, County West`,
      phone: '(555) 644-2200',
      website: 'harvestnetwork.org',
      ...offsetCoord(38.2, 260),
      about: 'Connects regional farming cooperatives directly with local food pantries to eliminate food deserts.'
    },
    {
      id: `${prefix}-mental-zone4`,
      name: `Tri-County Behavioral Health & Substance Crisis Campus`,
      category: 'mental',
      categoryLabel: 'Mental Health',
      verified: true,
      rating: 4.6,
      reviewsCount: 115,
      services: ['Residential rehabilitation', 'Medication-assisted treatment', 'Family recovery programs'],
      hoursText: '24/7 Intake Available',
      eligibility: 'Open to all tri-county residents. Sliding scale available.',
      address: `3300 County Line Rd, South Regional`,
      phone: '(555) 723-9000',
      website: 'tricountymental.org',
      ...offsetCoord(42.0, 175),
      about: 'Regional inpatient and outpatient recovery center serving a three-county area with evidence-based mental care.'
    },
    {
      id: `${prefix}-housing-zone4`,
      name: `Regional Rural Housing Development Corporation`,
      category: 'housing',
      categoryLabel: 'Housing & Utilities',
      verified: true,
      rating: 4.5,
      reviewsCount: 68,
      services: ['Rural home weatherization', 'USDA housing assistance', 'Emergency roof & furnace repair'],
      hoursText: 'Mon - Fri: 8:30 AM - 4:30 PM',
      eligibility: 'Rural low-income homeowners and renters.',
      address: `505 Rural Development Rd, County South`,
      phone: '(555) 438-1120',
      website: 'ruralhousingdev.org',
      ...offsetCoord(45.5, 130),
      about: 'Assists rural families with home rehabilitation grants, energy efficiency, and affordable home ownership.'
    },
    {
      id: `${prefix}-social-zone4`,
      name: `Community Action Partnership Multi-County Headquarters`,
      category: 'social',
      categoryLabel: 'Social Services',
      verified: true,
      rating: 4.7,
      reviewsCount: 94,
      services: ['Low-income energy assistance (LIHEAP)', 'Early childhood education', 'Financial literacy'],
      hoursText: 'Mon - Fri: 8:00 AM - 5:00 PM',
      eligibility: 'Low-income households across 4 contiguous counties.',
      address: `1220 County Seat Blvd, Regional Hub`,
      phone: '(555) 321-7890',
      website: 'communityactionpartner.org',
      ...offsetCoord(31.8, 290),
      about: 'Multi-county non-profit administering critical energy assistance, weatherization, and family stabilization.'
    },
    {
      id: `${prefix}-park-zone4`,
      name: `State Forest & Wildlife Environmental Wellness Sanctuary`,
      category: 'park',
      categoryLabel: 'Parks & Open Space',
      verified: true,
      rating: 4.9,
      reviewsCount: 890,
      services: ['Hiking & mountain biking trails', 'Campgrounds', 'Forest therapy walking circuits'],
      hoursText: 'Daily: Sunrise to Sunset',
      eligibility: 'Free state forest admission.',
      address: `22000 Forest Sanctuary Rd, State Reserve`,
      phone: '(555) 987-6543',
      website: 'stateforests.gov',
      ...offsetCoord(47.2, 40),
      about: 'Vast protected state forest providing clean air, wilderness immersion, and restorative outdoor fitness.'
    }
  ]

  return list
}

// Preset Communities Data
const resourcesData = {
  cuyahoga: {
    cityName: 'Cleveland, OH',
    centerLat: 41.4993,
    centerLng: -81.6944,
    resources: buildTieredCommunityResources('Cleveland, OH', 41.4993, -81.6944, 'cuyahoga')
  },
  wayne: {
    cityName: 'Detroit, MI',
    centerLat: 42.3314,
    centerLng: -83.0458,
    resources: buildTieredCommunityResources('Detroit, MI', 42.3314, -83.0458, 'wayne')
  },
  marion: {
    cityName: 'Indianapolis, IN',
    centerLat: 39.7684,
    centerLng: -86.1581,
    resources: buildTieredCommunityResources('Indianapolis, IN', 39.7684, -86.1581, 'marion')
  },
  franklin: {
    cityName: 'Columbus, OH',
    centerLat: 39.9612,
    centerLng: -82.9988,
    resources: buildTieredCommunityResources('Columbus, OH', 39.9612, -82.9988, 'franklin')
  }
}

// Active Community Generator (supports all preset and midwest counties dynamically)
const activeCommunity = computed(() => {
  const selectedKey = selectedId.value
  if (resourcesData[selectedKey]) {
    return resourcesData[selectedKey]
  }
  const match = regionOptions.find(r => r.id === selectedKey)
  if (match) {
    return {
      cityName: match.city ? `${match.city}, ${match.name}` : match.name,
      centerLat: match.lat,
      centerLng: match.lon,
      resources: buildTieredCommunityResources(match.city || match.name, match.lat, match.lon, match.id)
    }
  }
  return resourcesData.cuyahoga
})

// Backend API Scraped Resources
const scrapedResources = ref([])
const isLoadingScrape = ref(false)

// Dynamically Calculate Distances from Active Center Point
const currentResources = computed(() => {
  let baseList = []
  if (isAnalyzed.value && scrapedResources.value.length > 0) {
    baseList = scrapedResources.value
  } else {
    baseList = activeCommunity.value.resources
  }

  const { lat: cLat, lng: cLng } = mapCenter.value

  // Attach live calculated distance to each resource
  return baseList.map(r => {
    const dist = getHaversineDistanceMiles(cLat, cLng, r.lat, r.lon)
    return {
      ...r,
      distance: dist
    }
  })
})

// Categories Chip List
const categories = [
  { id: 'all', label: 'All Resources', icon: 'map', colorClass: 'grey' },
  { id: 'campaign', label: 'Live Campaigns', icon: 'sparkle', colorClass: 'blue', isSpecial: true },
  { id: 'health', label: 'Healthcare', icon: 'pulse', colorClass: 'green' },
  { id: 'food', label: 'Food Access', icon: 'pin', colorClass: 'orange' },
  { id: 'mental', label: 'Mental Health', icon: 'heart', colorClass: 'purple' },
  { id: 'transit', label: 'Transportation', icon: 'trend', colorClass: 'blue' },
  { id: 'housing', label: 'Housing & Utilities', icon: 'home', colorClass: 'pink' },
  { id: 'social', label: 'Social Services', icon: 'users', colorClass: 'rose' },
  { id: 'gym', label: 'Fitness & Wellness', icon: 'target', colorClass: 'purple' },
  { id: 'park', label: 'Parks & Open Space', icon: 'bulb', colorClass: 'green' }
]

function getCategoryCount(catId) {
  let list = currentResources.value
  
  if (radiusFilter.value) {
    const maxMiles = parseFloat(radiusFilter.value)
    if (!isNaN(maxMiles)) {
      list = list.filter(r => (r.distance || 0) <= maxMiles)
    }
  }

  if (searchQuery.value.trim() !== '') {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(r => 
      r.name.toLowerCase().includes(q) ||
      (r.services && r.services.some(s => s.toLowerCase().includes(q))) ||
      (r.about && r.about.toLowerCase().includes(q))
    )
  }

  if (catId === 'all') return list.length
  return list.filter(r => r.category === catId).length
}

// Filtered Resources List (with accurate radius filter & distance sort)
const filteredResources = computed(() => {
  let list = currentResources.value

  if (activeCategoryFilter.value !== 'all') {
    list = list.filter(r => r.category === activeCategoryFilter.value)
  }

  if (searchQuery.value.trim() !== '') {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(r => 
      r.name.toLowerCase().includes(q) ||
      (r.services && r.services.some(s => s.toLowerCase().includes(q))) ||
      (r.about && r.about.toLowerCase().includes(q)) ||
      (r.address && r.address.toLowerCase().includes(q))
    )
  }

  if (radiusFilter.value) {
    const maxMiles = parseFloat(radiusFilter.value)
    if (!isNaN(maxMiles)) {
      list = list.filter(r => (r.distance || 0) <= maxMiles)
    }
  }

  // Sort resources by distance (closest first)
  return list.slice().sort((a, b) => (a.distance || 0) - (b.distance || 0))
})

// Latitude / Longitude Center
const mapCenter = computed(() => {
  if (customLat.value && customLng.value) {
    return { lat: parseFloat(customLat.value), lng: parseFloat(customLng.value) }
  }
  if (isAnalyzed.value && patientData.value.lat && patientData.value.long) {
    return { lat: patientData.value.lat, lng: patientData.value.long }
  }
  return { lat: activeCommunity.value.centerLat, lng: activeCommunity.value.centerLng }
})

// MapLibre Map Logic
let mapInstance = null
let mapMarkers = []
let homeMarker = null

function initMapLibre() {
  const container = document.getElementById('maplibre-resources-map')
  if (!container) return

  if (mapInstance) {
    mapInstance.remove()
    mapInstance = null
  }

  const { lat, lng } = mapCenter.value

  try {
    mapInstance = new maplibregl.Map({
      container: 'maplibre-resources-map',
      style: isDarkMap.value ? mapStyles.dark : mapStyles.light,
      center: [lng, lat],
      zoom: 12.5,
      pitch: 0,
      attributionControl: false
    })

    mapInstance.on('load', () => {
      mapInstance.resize()
      renderMapElements()
    })

    window.addEventListener('resize', handleMapResize)
  } catch (err) {
    console.error("MapLibre Initialization Error:", err)
  }
}

function handleMapResize() {
  if (mapInstance) {
    mapInstance.resize()
  }
}

function toggleMapTheme() {
  isDarkMap.value = !isDarkMap.value
  if (mapInstance) {
    mapInstance.setStyle(isDarkMap.value ? mapStyles.dark : mapStyles.light)
    mapInstance.once('style.load', () => {
      mapInstance.resize()
      renderMapElements()
      if (activeRouteInfo.value) {
        showDirections(activeRouteInfo.value.res)
      }
    })
  }
}

function renderMapElements() {
  if (!mapInstance) return

  // Clear existing markers
  mapMarkers.forEach(m => m.remove())
  mapMarkers = []
  if (homeMarker) {
    homeMarker.remove()
    homeMarker = null
  }

  const { lat, lng } = mapCenter.value

  // Create Patient/User Residence Pulse Marker
  const homeEl = document.createElement('div')
  homeEl.className = 'caremap-patient-marker'
  homeEl.innerHTML = `
    <div class="radar-ping"></div>
    <div class="core-dot"></div>
  `

  const homePopup = new maplibregl.Popup({ offset: 25, closeButton: false }).setHTML(`
    <div class="caremap-popup-card patient-popup">
      <div class="popup-badge blue">Search Epicenter</div>
      <h4 class="popup-title">${isAnalyzed.value ? patientData.value.name + ' (Patient Residence)' : (customLocationName.value || activeCommunity.value.cityName)}</h4>
      <p class="popup-coord">${lat.toFixed(4)}, ${lng.toFixed(4)}</p>
    </div>
  `)

  homeMarker = new maplibregl.Marker({ element: homeEl })
    .setLngLat([lng, lat])
    .setPopup(homePopup)
    .addTo(mapInstance)

  // Render Resource Pins
  filteredResources.value.forEach(res => {
    let rLat = res.lat
    let rLon = res.lon

    if (!rLat || !rLon) {
      rLat = lat + (Math.random() - 0.5) * 0.04
      rLon = lng + (Math.random() - 0.5) * 0.04
    }

    const pinEl = document.createElement('div')
    const isSelected = selectedResource.value && selectedResource.value.id === res.id
    const isCampaign = res.isCampaign || res.category === 'campaign'

    pinEl.className = `caremap-resource-pin ${res.category} ${isSelected ? 'selected' : ''} ${isCampaign ? 'campaign-pulse' : ''}`
    
    pinEl.innerHTML = `
      <div class="pin-inner">
        <span class="pin-dot"></span>
      </div>
    `

    const colorHex = res.category === 'campaign' ? '#2563eb' : res.category === 'food' ? '#d97706' : res.category === 'health' ? '#059669' : res.category === 'mental' ? '#7c3aed' : res.category === 'transit' ? '#2563eb' : '#db2777'
    
    const popupContent = `
      <div class="caremap-popup-card">
        <div class="popup-header" style="border-top: 3px solid ${colorHex};">
          <span class="category-badge ${res.category}">${res.categoryLabel || res.category}</span>
          <span class="distance-badge">${res.distance ? res.distance + ' mi' : 'Near'}</span>
        </div>
        <h4 class="popup-title">${res.name}</h4>
        <p class="popup-address">📍 ${res.address || 'Address on file'}</p>
        <p class="popup-hours">⏰ ${res.hoursText || 'Call for hours'}</p>
        <div class="popup-actions">
          <a href="${res.website ? (res.website.startsWith('http') ? res.website : 'https://' + res.website) : ('https://www.google.com/search?q=' + encodeURIComponent(res.name + ' ' + (res.address || '')))}" target="_blank" class="popup-btn call-btn">🌐 Website</a>
          <button class="popup-btn maps-btn" onclick="window.careMapDirectRoute('${res.id}')">🛣️ Directions</button>
        </div>
      </div>
    `

    const popup = new maplibregl.Popup({ offset: 20, closeButton: true }).setHTML(popupContent)

    const marker = new maplibregl.Marker({ element: pinEl })
      .setLngLat([rLon, rLat])
      .setPopup(popup)
      .addTo(mapInstance)

    pinEl.addEventListener('click', () => {
      selectedResource.value = res
      if (window.innerWidth <= 768) {
        mobileTab.value = 'map'
      }
      mapInstance.flyTo({
        center: [rLon, rLat],
        zoom: 14.5,
        speed: 1.2
      })
    })

    mapMarkers.push(marker)
  })
}

// Draw Directions & Route Line directly ON THE MAP
async function showDirections(res) {
  if (!mapInstance) return
  selectedResource.value = res

  if (window.innerWidth <= 768) {
    mobileTab.value = 'map'
    nextTick(() => {
      if (mapInstance) mapInstance.resize()
    })
  }

  const { lat: oLat, lng: oLng } = mapCenter.value
  let dLat = res.lat
  let dLng = res.lon

  if (!dLat || !dLng) {
    dLat = oLat + (Math.random() - 0.5) * 0.04
    dLng = oLng + (Math.random() - 0.5) * 0.04
  }

  isRoutingLoading.value = true

  try {
    const osrmUrl = `https://router.project-osrm.org/route/v1/driving/${oLng},${oLat};${dLng},${dLat}?overview=full&geometries=geojson`
    const resp = await fetch(osrmUrl)
    let routeGeoJSON = null
    let distMiles = res.distance || 0
    let durationMins = Math.round(distMiles * 2.2) || 5

    if (resp.ok) {
      const routeData = await resp.json()
      if (routeData.routes && routeData.routes.length > 0) {
        const route = routeData.routes[0]
        routeGeoJSON = route.geometry
        distMiles = (route.distance / 1609.34).toFixed(1)
        durationMins = Math.round(route.duration / 60)
      }
    }

    if (!routeGeoJSON) {
      const midLng = (oLng + dLng) / 2 + 0.003
      const midLat = (oLat + dLat) / 2 - 0.003
      routeGeoJSON = {
        type: 'LineString',
        coordinates: [
          [oLng, oLat],
          [midLng, midLat],
          [dLng, dLat]
        ]
      }
    }

    activeRouteInfo.value = {
      resourceName: res.name,
      distanceText: `${distMiles} mi`,
      durationText: `~${durationMins} mins drive`,
      res: res
    }

    drawRouteLayer(routeGeoJSON)

    const bounds = new maplibregl.LngLatBounds()
      .extend([oLng, oLat])
      .extend([dLng, dLat])

    mapInstance.fitBounds(bounds, {
      padding: { top: 120, bottom: 100, left: 100, right: 100 },
      maxZoom: 15,
      speed: 1.2
    })

    triggerToast(`Drawing navigation route to ${res.name}`)
  } catch (err) {
    console.error("Routing error:", err)
    const fallbackGeoJSON = {
      type: 'LineString',
      coordinates: [[oLng, oLat], [dLng, dLat]]
    }
    drawRouteLayer(fallbackGeoJSON)
    activeRouteInfo.value = {
      resourceName: res.name,
      distanceText: `${res.distance || 'Direct'} mi`,
      durationText: 'Estimated route',
      res: res
    }
    triggerToast(`Route displayed to ${res.name}`)
  } finally {
    isRoutingLoading.value = false
  }
}

function drawRouteLayer(geojson) {
  if (!mapInstance) return

  if (mapInstance.getLayer('route-line-core')) mapInstance.removeLayer('route-line-core')
  if (mapInstance.getLayer('route-line-casing')) mapInstance.removeLayer('route-line-casing')
  if (mapInstance.getSource('route-source')) mapInstance.removeSource('route-source')

  mapInstance.addSource('route-source', {
    type: 'geojson',
    data: {
      type: 'Feature',
      properties: {},
      geometry: geojson
    }
  })

  mapInstance.addLayer({
    id: 'route-line-casing',
    type: 'line',
    source: 'route-source',
    layout: {
      'line-join': 'round',
      'line-cap': 'round'
    },
    paint: {
      'line-color': '#1d4ed8',
      'line-width': 8,
      'line-opacity': 0.7
    }
  })

  mapInstance.addLayer({
    id: 'route-line-core',
    type: 'line',
    source: 'route-source',
    layout: {
      'line-join': 'round',
      'line-cap': 'round'
    },
    paint: {
      'line-color': '#3b82f6',
      'line-width': 5
    }
  })
}

function clearRoute() {
  activeRouteInfo.value = null
  if (mapInstance) {
    if (mapInstance.getLayer('route-line-core')) mapInstance.removeLayer('route-line-core')
    if (mapInstance.getLayer('route-line-casing')) mapInstance.removeLayer('route-line-casing')
    if (mapInstance.getSource('route-source')) mapInstance.removeSource('route-source')
    flyToEpicenter()
  }
}

function handleResourceClick(res) {
  selectedResource.value = res
  if (window.innerWidth <= 768) {
    mobileTab.value = 'map'
    nextTick(() => {
      if (mapInstance) mapInstance.resize()
    })
  }
  if (mapInstance && res.lat && res.lon) {
    mapInstance.flyTo({
      center: [res.lon, res.lat],
      zoom: 14.5,
      speed: 1.2
    })
  }
}

function flyToEpicenter() {
  if (mapInstance) {
    const { lat, lng } = mapCenter.value
    mapInstance.flyTo({
      center: [lng, lat],
      zoom: 13,
      speed: 1.2
    })
  }
}

function zoomIn() {
  if (mapInstance) mapInstance.zoomIn()
}

function zoomOut() {
  if (mapInstance) mapInstance.zoomOut()
}

const is3DView = ref(false)

function toggle3DView() {
  is3DView.value = !is3DView.value
  if (!mapInstance) return

  if (is3DView.value) {
    mapInstance.easeTo({
      pitch: 60,
      bearing: -25,
      duration: 1000
    })
    triggerToast('3D Perspective View Enabled')
  } else {
    mapInstance.easeTo({
      pitch: 0,
      bearing: 0,
      duration: 1000
    })
    triggerToast('2D Flat View Enabled')
  }
}

function resetCompass() {
  if (mapInstance) {
    mapInstance.resetNorthPitch()
    is3DView.value = false
  }
}

// Custom Coordinate Launcher
function applyCustomCoordinates() {
  if (inputLat.value && inputLng.value) {
    customLat.value = parseFloat(inputLat.value)
    customLng.value = parseFloat(inputLng.value)
    customLocationName.value = `Custom Location (${customLat.value.toFixed(2)}, ${customLng.value.toFixed(2)})`
    isCoordModalOpen.value = false
    clearRoute()
    triggerToast('Updated map center coordinates')
    
    if (mapInstance) {
      mapInstance.flyTo({
        center: [customLng.value, customLat.value],
        zoom: 13
      })
      renderMapElements()
    }
  }
}

// Fetch resources using the python backend scraping endpoint
async function fetchScrapedResources(lat, lon) {
  isLoadingScrape.value = true
  try {
    const res = await fetch(`${MAIN_BACKEND_URL}/api/patients/scrape-resources?lat=${lat}&lon=${lon}`)
    if (res.ok) {
      const data = await res.json()
      scrapedResources.value = data.resources || []
      if (filteredResources.value.length > 0) {
        selectedResource.value = filteredResources.value[0]
      }
      renderMapElements()
    }
  } catch (err) {
    console.error("Error fetching scraped resources:", err)
  } finally {
    isLoadingScrape.value = false
  }
}

function selectCommunity(id) {
  selectedId.value = id
  customLat.value = null
  customLng.value = null
  clearRoute()
  const comm = resourcesData[id]
  if (comm) {
    fetchScrapedResources(comm.centerLat, comm.centerLng)
    if (mapInstance) {
      mapInstance.flyTo({
        center: [comm.centerLng, comm.centerLat],
        zoom: 12.5
      })
    }
  }
}

// Watchers
watch(filteredResources, () => {
  renderMapElements()
})

watch(selectedId, () => {
  renderMapElements()
})

onMounted(() => {
  window.careMapDirectRoute = (resId) => {
    const matched = filteredResources.value.find(r => r.id === resId)
    if (matched) {
      showDirections(matched)
    }
  }

  const { lat, lng } = mapCenter.value
  fetchScrapedResources(lat, lng)

  nextTick(() => {
    setTimeout(() => {
      initMapLibre()
    }, 150)
  })
})

onUnmounted(() => {
  delete window.careMapDirectRoute
  window.removeEventListener('resize', handleMapResize)
  if (mapInstance) {
    mapInstance.remove()
  }
})
</script>

<template>
  <div class="caremap-resources-page light-theme">
    
    <!-- Toast Popup Notification -->
    <Transition name="fade">
      <div v-if="showToast" class="toast-popup">
        <IconBase name="shield" :size="16" />
        <span>{{ toastMsg }}</span>
      </div>
    </Transition>

    <!-- Custom Coordinates Modal -->
    <div v-if="isCoordModalOpen" class="modal-overlay" @click.self="isCoordModalOpen = false">
      <div class="modal-card">
        <div class="modal-header">
          <h3>Set Custom Map Location</h3>
          <button class="close-btn" @click="isCoordModalOpen = false">&times;</button>
        </div>
        <div class="modal-body">
          <p class="modal-desc">Enter latitude and longitude coordinates to center CareMap anywhere in the world.</p>
          <div class="input-group">
            <label>Latitude</label>
            <input v-model="inputLat" type="number" step="0.0001" placeholder="e.g. 41.4993" />
          </div>
          <div class="input-group">
            <label>Longitude</label>
            <input v-model="inputLng" type="number" step="0.0001" placeholder="e.g. -81.6944" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="isCoordModalOpen = false">Cancel</button>
          <button class="btn-primary" @click="applyCustomCoordinates">Apply Location</button>
        </div>
      </div>
    </div>

    <!-- Mobile View Tab Switcher Bar (< 768px) -->
    <div class="mobile-view-toggle">
      <button 
        class="mobile-tab" 
        :class="{ active: mobileTab === 'list' }" 
        @click="mobileTab = 'list'"
      >
        📋 List View ({{ filteredResources.length }})
      </button>
      <button 
        class="mobile-tab" 
        :class="{ active: mobileTab === 'map' }" 
        @click="mobileTab = 'map'"
      >
        🗺️ Map View
      </button>
    </div>

    <!-- Main Container -->
    <div class="main-layout">
      
      <!-- Left Panel: Controls, Categories & Resource List -->
      <div class="sidebar-panel" :class="{ 'mobile-hidden': mobileTab !== 'list' }">
        
        <!-- Header -->
        <div class="header-section">
          <div class="title-row">
            <div class="brand-badge">
              <span class="pulse-dot"></span>
              CareMap Live
            </div>
            <h1>Community Resources</h1>
          </div>
          <p class="subtitle">Geospatial discovery of health clinics, food access, transit, and live interventions.</p>
        </div>

        <!-- Location & Preset Region Selector Dropdown -->
        <div class="region-selector-bar">
          <span class="region-label">Region:</span>
          <div class="region-dropdown-wrapper">
            <button class="region-trigger" @click="isRegionDropdownOpen = !isRegionDropdownOpen">
              <span class="region-trigger-text">
                📍 <strong>{{ selectedRegionLabel }}</strong>
              </span>
              <IconBase name="chevron-down" :size="14" />
            </button>
            <ul v-if="isRegionDropdownOpen" class="region-menu">
              <!-- County Search Box inside Dropdown -->
              <div class="county-search-box">
                <IconBase name="search" :size="13" class="c-search-icon" />
                <input 
                  v-model="countySearchQuery" 
                  type="text" 
                  placeholder="Search county name..." 
                  @click.stop
                />
              </div>

              <!-- Scrollable County List -->
              <div class="county-scroll-list">
                <li 
                  v-for="reg in filteredRegionOptions" 
                  :key="reg.id"
                  :class="{ active: selectedId === reg.id && !customLat }"
                  @click="selectRegion(reg)"
                >
                  <div class="region-item-row">
                    <span class="region-item-name">{{ reg.name }}</span>
                    <span class="region-item-county" v-if="reg.city">{{ reg.city }}</span>
                  </div>
                </li>
                <li v-if="filteredRegionOptions.length === 0" class="no-county-found">
                  No county found matching "{{ countySearchQuery }}"
                </li>
              </div>

              <!-- Custom Coordinates Launcher Option -->
              <li class="custom-coord-option" @click="openCustomModalFromDropdown">
                <IconBase name="locate" :size="13" />
                <span>Custom Lat / Lng Coordinates...</span>
              </li>
            </ul>
          </div>
        </div>

        <!-- Search Bar & Radius Filter -->
        <div class="search-filter-card">
          <div class="search-input-box">
            <IconBase name="search" :size="16" class="search-icon" />
            <input 
              v-model="searchQuery" 
              type="text" 
              placeholder="Search resources, services, or locations..." 
            />
            <button v-if="searchQuery" class="clear-search" @click="searchQuery = ''">&times;</button>
          </div>

          <div class="radius-dropdown-wrapper">
            <button class="radius-trigger" @click="isRadiusDropdownOpen = !isRadiusDropdownOpen">
              <span>Radius: <strong>{{ radiusFilter }}</strong></span>
              <IconBase name="chevron-down" :size="14" />
            </button>
            <ul v-if="isRadiusDropdownOpen" class="radius-menu">
              <li 
                v-for="opt in radiusOptionsList" 
                :key="opt"
                :class="{ active: radiusFilter === opt }"
                @click="selectRadius(opt)"
              >
                {{ opt }}
              </li>
            </ul>
          </div>
        </div>

        <!-- Category Filter Pills -->
        <div class="categories-scroll-wrapper">
          <div 
            v-for="cat in categories" 
            :key="cat.id"
            class="category-pill"
            :class="[cat.id, { active: activeCategoryFilter === cat.id }, { special: cat.isSpecial }]"
            @click="activeCategoryFilter = cat.id"
          >
            <IconBase :name="cat.icon" :size="14" />
            <span>{{ cat.label }}</span>
            <span class="count-badge">{{ getCategoryCount(cat.id) }}</span>
          </div>
        </div>

        <!-- Resources List Section -->
        <div class="resources-list-container">
          <div class="list-header">
            <h3>Matching Resources ({{ filteredResources.length }})</h3>
            <span v-if="isLoadingScrape" class="loading-tag">Updating live data...</span>
          </div>

          <div v-if="filteredResources.length === 0" class="empty-state">
            <IconBase name="search" :size="32" />
            <p>No community resources found matching your search or radius criteria.</p>
          </div>

          <div 
            v-for="res in filteredResources" 
            :key="res.id"
            class="resource-card"
            :class="{ active: selectedResource && selectedResource.id === res.id, campaign: res.isCampaign || res.category === 'campaign' }"
            @click="handleResourceClick(res)"
          >
            <div class="card-top">
              <span class="category-tag" :class="res.category">
                {{ res.categoryLabel || res.category }}
              </span>
              <div class="card-actions">
                <button 
                  class="bookmark-btn" 
                  :class="{ bookmarked: bookmarkedIds.has(res.id) }" 
                  @click.stop="toggleBookmark(res.id)"
                  title="Bookmark Resource"
                >
                  <IconBase name="heart" :size="14" />
                </button>
                <span class="distance-tag">{{ res.distance ? res.distance + ' mi' : 'Near' }}</span>
              </div>
            </div>

            <h4 class="resource-name">{{ res.name }}</h4>

            <p class="resource-address">
              <IconBase name="pin" :size="13" />
              <span>{{ res.address }}</span>
            </p>

            <p class="resource-hours">
              <IconBase name="calendar" :size="13" />
              <span>{{ res.hoursText || 'Contact for operating hours' }}</span>
            </p>

            <div v-if="res.services && res.services.length > 0" class="service-tags">
              <span v-for="(svc, idx) in res.services.slice(0, 3)" :key="idx" class="svc-tag">
                {{ svc }}
              </span>
              <span v-if="res.services.length > 3" class="svc-more">+{{ res.services.length - 3 }} more</span>
            </div>

            <div class="card-footer">
              <a 
                :href="res.website ? (res.website.startsWith('http') ? res.website : 'https://' + res.website) : ('https://www.google.com/search?q=' + encodeURIComponent(res.name + ' ' + (res.address || '')))" 
                target="_blank"
                class="card-btn call"
                @click.stop
              >
                Website ↗
              </a>
              <button 
                class="card-btn nav"
                @click.stop="showDirections(res)"
              >
                Directions
              </button>
            </div>
          </div>
        </div>

      </div>

      <!-- Right Panel: MapLibre Canvas with Floating Map Controls & Navigation Overlay -->
      <div class="map-panel" :class="{ 'mobile-hidden': mobileTab !== 'map' }">
        
        <!-- On-Map Navigation Directions Banner Overlay -->
        <Transition name="fade">
          <div v-if="activeRouteInfo" class="caremap-route-banner">
            <div class="route-info-col">
              <div class="route-badge">🚘 Route Navigation Active</div>
              <div class="route-dest-name">{{ activeRouteInfo.resourceName }}</div>
              <div class="route-metrics">
                <span>📍 {{ activeRouteInfo.distanceText }}</span>
                <span>⏱️ {{ activeRouteInfo.durationText }}</span>
              </div>
            </div>
            <div class="route-action-col">
              <a 
                :href="'https://www.google.com/maps/search/?api=1&query=' + (activeRouteInfo.res.lat || mapCenter.lat) + ',' + (activeRouteInfo.res.lon || mapCenter.lng)" 
                target="_blank" 
                class="route-btn gmaps"
              >
                Google Maps ↗
              </a>
              <button class="route-btn clear" @click="clearRoute">
                Clear Route &times;
              </button>
            </div>
          </div>
        </Transition>

        <!-- Map Canvas -->
        <div id="maplibre-resources-map" class="map-container"></div>

        <!-- Floating CareMap Controls Bar (Top Left Horizontal) -->
        <div class="caremap-controls-bar">
          <button class="map-control-btn" @click="zoomIn" title="Zoom In">+</button>
          <button class="map-control-btn" @click="zoomOut" title="Zoom Out">&minus;</button>
          <button class="map-control-btn" @click="resetCompass" title="Reset North">N</button>
          <button 
            class="map-control-btn view-3d-btn" 
            :class="{ active: is3DView }" 
            @click="toggle3DView" 
            :title="is3DView ? 'Switch to 2D Flat View' : 'Switch to 3D Perspective View'"
          >
            <span v-if="is3DView" class="badge-3d active">2D</span>
            <span v-else class="badge-3d">3D</span>
          </button>
          <button class="map-control-btn" @click="flyToEpicenter" title="Locate Center">
            <IconBase name="locate" :size="16" />
          </button>
          <button class="map-control-btn theme-toggle" @click="toggleMapTheme" :title="isDarkMap ? 'Switch to Light Map Tiles' : 'Switch to Dark Map Tiles'">
            <span v-if="isDarkMap">☀️</span>
            <span v-else>🌙</span>
          </button>
        </div>

        <!-- Floating Legend Pill (Top Right) -->
        <div class="caremap-legend-pill">
          <span class="legend-item"><span class="dot patient"></span> Residence Center</span>
          <span class="legend-item"><span class="dot campaign"></span> Live Campaign</span>
          <span class="legend-item"><span class="dot health"></span> Clinic</span>
          <span class="legend-item"><span class="dot food"></span> Food</span>
        </div>

      </div>

    </div>

  </div>
</template>

<style scoped>
/* White / Light Theme Base */
.caremap-resources-page.light-theme {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: calc(100vh - 64px);
  min-height: 0;
  background-color: #f8fafc;
  color: #0f172a;
  overflow: hidden;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  position: relative;
}

/* Mobile View Toggle Bar (< 768px) */
.mobile-view-toggle {
  display: none;
  width: 100%;
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  padding: 6px 12px;
  gap: 8px;
  z-index: 50;
}
.mobile-tab {
  flex: 1;
  padding: 8px 0;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 700;
  background: #f1f5f9;
  color: #475569;
  border: 1px solid #e2e8f0;
  text-align: center;
  transition: all 0.2s;
}
.mobile-tab.active {
  background: #2563eb;
  color: #ffffff;
  border-color: #2563eb;
}

/* On-Map Navigation Banner */
.caremap-route-banner {
  position: absolute;
  top: 72px;
  left: 20px;
  z-index: 40;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 12px 18px;
  background: rgba(255, 255, 255, 0.95);
  border: 2px solid #2563eb;
  backdrop-filter: blur(12px);
  border-radius: 16px;
  box-shadow: 0 12px 30px rgba(37, 99, 235, 0.2);
  max-width: calc(100% - 40px);
  animation: slideDown 0.3s ease;
}
@keyframes slideDown {
  from { transform: translateY(-20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
.route-badge {
  font-size: 11px;
  font-weight: 800;
  color: #2563eb;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.route-dest-name {
  font-size: 13px;
  font-weight: 800;
  color: #0f172a;
  margin: 2px 0;
}
.route-metrics {
  display: flex;
  gap: 12px;
  font-size: 11px;
  font-weight: 700;
  color: #334155;
}
.route-action-col {
  display: flex;
  align-items: center;
  gap: 8px;
}
.route-btn {
  padding: 6px 10px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.route-btn.gmaps {
  background: #eff6ff;
  color: #2563eb;
  border: 1px solid #bfdbfe;
}
.route-btn.clear {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecdd3;
}
.route-btn.clear:hover {
  background: #dc2626;
  color: white;
}

/* Toast Popup */
.toast-popup {
  position: fixed;
  top: 80px;
  right: 24px;
  z-index: 9999;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #bfdbfe;
  backdrop-filter: blur(12px);
  color: #1d4ed8;
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(37, 99, 235, 0.15);
  font-weight: 600;
  font-size: 13px;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 999;
  background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal-card {
  width: 420px;
  max-width: 90vw;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.15);
  color: #0f172a;
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.modal-header h3 {
  font-size: 16px;
  font-weight: 700;
  margin: 0;
  color: #0f172a;
}
.close-btn {
  font-size: 24px;
  color: #64748b;
}
.modal-desc {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 16px;
}
.input-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 14px;
}
.input-group label {
  font-size: 12px;
  font-weight: 600;
  color: #334155;
}
.input-group input {
  padding: 10px 14px;
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  color: #0f172a;
  font-size: 14px;
}
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}
.btn-secondary {
  padding: 8px 16px;
  background: #f1f5f9;
  color: #334155;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-weight: 600;
}
.btn-primary {
  padding: 8px 16px;
  background: #2563eb;
  color: white;
  border-radius: 8px;
  font-weight: 600;
}

/* Layout */
.main-layout {
  display: flex;
  flex: 1;
  height: 100%;
  width: 100%;
  overflow: hidden;
}

/* Sidebar Panel */
.sidebar-panel {
  width: 400px;
  min-width: 320px;
  max-width: 450px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  overflow: hidden;
  transition: width 0.3s ease;
}

.header-section {
  padding: 18px 20px 12px 20px;
}
.brand-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: rgba(37, 99, 235, 0.08);
  border: 1px solid rgba(37, 99, 235, 0.2);
  border-radius: 20px;
  font-size: 11px;
  font-weight: 700;
  color: #2563eb;
  margin-bottom: 8px;
}
.pulse-dot {
  width: 6px;
  height: 6px;
  background: #2563eb;
  border-radius: 50%;
  box-shadow: 0 0 8px #2563eb;
}
.header-section h1 {
  font-size: 20px;
  font-weight: 800;
  margin: 0;
  color: #0f172a;
}
.subtitle {
  font-size: 12px;
  color: #64748b;
  margin-top: 4px;
  margin-bottom: 0;
  line-height: 1.4;
}

/* Region Selector Bar & Dropdown */
.region-selector-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 20px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
  border-bottom: 1px solid #e2e8f0;
}
.region-label {
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
}
.region-dropdown-wrapper {
  position: relative;
  flex: 1;
}
.region-trigger {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 7px 12px;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  color: #0f172a;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
}
.region-trigger:hover {
  background: #f8fafc;
  border-color: #2563eb;
}
.region-trigger-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 12px;
}
.region-menu {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 6px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.15);
  z-index: 60;
  padding: 6px;
  list-style: none;
  width: 260px;
  max-width: 90vw;
}
.county-search-box {
  position: relative;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
}
.c-search-icon {
  position: absolute;
  left: 8px;
  color: #94a3b8;
}
.county-search-box input {
  width: 100%;
  padding: 6px 10px 6px 26px;
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 11px;
  color: #0f172a;
}
.county-search-box input:focus {
  outline: none;
  border-color: #2563eb;
  background: #ffffff;
}
.county-scroll-list {
  max-height: 240px;
  overflow-y: auto;
  scrollbar-width: thin;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.no-county-found {
  padding: 12px;
  font-size: 11px;
  color: #64748b;
  text-align: center;
  font-style: italic;
}
.region-menu li {
  padding: 7px 10px;
  border-radius: 6px;
  font-size: 12px;
  color: #334155;
  cursor: pointer;
  transition: all 0.15s;
}
.region-menu li:hover {
  background: #f1f5f9;
  color: #0f172a;
}
.region-menu li.active {
  background: #eff6ff;
  color: #2563eb;
  font-weight: 700;
}
.region-item-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
.region-item-name {
  font-weight: 600;
}
.region-item-county {
  font-size: 10px;
  color: #64748b;
}
.region-menu li.active .region-item-county {
  color: #3b82f6;
}
.custom-coord-option {
  display: flex;
  align-items: center;
  gap: 8px;
  border-top: 1px solid #f1f5f9;
  margin-top: 4px;
  padding-top: 8px !important;
  color: #2563eb !important;
  font-weight: 600;
}
.custom-coord-option:hover {
  background: #eff6ff !important;
}
.custom-btn {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* Search & Filters */
.search-filter-card {
  display: flex;
  gap: 8px;
  padding: 12px 20px;
}
.search-input-box {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
}
.search-icon {
  position: absolute;
  left: 12px;
  color: #64748b;
}
.search-input-box input {
  width: 100%;
  padding: 8px 30px 8px 34px;
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  color: #0f172a;
  font-size: 12px;
}
.search-input-box input:focus {
  outline: none;
  border-color: #2563eb;
  background: #ffffff;
}
.clear-search {
  position: absolute;
  right: 10px;
  color: #64748b;
  font-size: 16px;
}

.radius-dropdown-wrapper {
  position: relative;
}
.radius-trigger {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  color: #334155;
  font-size: 11px;
  white-space: nowrap;
}
.radius-trigger:hover {
  background: #f8fafc;
}
.radius-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 6px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(15, 23, 42, 0.1);
  z-index: 50;
  min-width: 110px;
}
.radius-menu li {
  padding: 8px 14px;
  font-size: 12px;
  color: #334155;
  cursor: pointer;
}
.radius-menu li:hover, .radius-menu li.active {
  background: #2563eb;
  color: white;
}

/* Category Pills */
.categories-scroll-wrapper {
  display: flex;
  gap: 6px;
  padding: 4px 20px 12px 20px;
  overflow-x: auto;
  scrollbar-width: thin;
}
.category-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
  color: #475569;
  white-space: nowrap;
  cursor: pointer;
  transition: all 0.2s;
}
.category-pill:hover {
  background: #e2e8f0;
  color: #0f172a;
}
.category-pill.active {
  background: #2563eb;
  border-color: #2563eb;
  color: white;
}
.category-pill.special {
  background: rgba(37, 99, 235, 0.08);
  border-color: rgba(37, 99, 235, 0.2);
  color: #2563eb;
}
.category-pill.special.active {
  background: #2563eb;
  color: white;
}
.count-badge {
  padding: 1px 6px;
  background: rgba(0, 0, 0, 0.06);
  border-radius: 10px;
  font-size: 10px;
}
.category-pill.active .count-badge {
  background: rgba(255, 255, 255, 0.2);
}

/* Resources List Container */
.resources-list-container {
  flex: 1;
  padding: 14px 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #f8fafc;
}
.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.list-header h3 {
  font-size: 12px;
  font-weight: 700;
  color: #334155;
  margin: 0;
}
.loading-tag {
  font-size: 11px;
  color: #2563eb;
}
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
  color: #64748b;
  gap: 12px;
}

/* Resource Cards */
.resource-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 14px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  gap: 8px;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
}
.resource-card:hover {
  border-color: #3b82f6;
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(37, 99, 235, 0.1);
}
.resource-card.active {
  border-color: #2563eb;
  background: #f0f7ff;
  box-shadow: 0 0 15px rgba(37, 99, 235, 0.15);
}
.resource-card.campaign {
  border-color: #bfdbfe;
  background: linear-gradient(135deg, #ffffff, #eff6ff);
}
.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.category-tag {
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  padding: 3px 10px;
  border-radius: 20px;
  letter-spacing: 0.5px;
  display: inline-flex;
  align-items: center;
  background: #f1f5f9;
  color: #334155;
  border: 1px solid #cbd5e1;
}
.category-tag.campaign { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }
.category-tag.food { background: #fef3c7; color: #b45309; border: 1px solid #fde68a; }
.category-tag.health, .category-tag.clinic { background: #d1fae5; color: #047857; border: 1px solid #a7f3d0; }
.category-tag.mental { background: #f3e8ff; color: #6b21a8; border: 1px solid #e9d5ff; }
.category-tag.transit { background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
.category-tag.housing { background: #fce7f3; color: #be185d; border: 1px solid #fbcfe8; }
.category-tag.social { background: #ffe4e6; color: #be123c; border: 1px solid #fecdd3; }
.category-tag.gym { background: #f3e8ff; color: #6b21a8; border: 1px solid #e9d5ff; }
.category-tag.park { background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }
.category-tag.pharmacy { background: #ccfbf1; color: #0f766e; border: 1px solid #99f6e4; }
.category-tag.other { background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; }

.card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.bookmark-btn {
  color: #94a3b8;
  transition: color 0.2s;
}
.bookmark-btn.bookmarked {
  color: #ec4899;
}
.distance-tag {
  font-size: 11px;
  font-weight: 700;
  color: #2563eb;
  background: #eff6ff;
  padding: 2px 8px;
  border-radius: 6px;
  border: 1px solid #dbeafe;
}
.resource-name {
  font-size: 13.5px;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
  line-height: 1.3;
}
.resource-address, .resource-hours {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #64748b;
  margin: 0;
}
.service-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}
.svc-tag {
  font-size: 10px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  padding: 2px 6px;
  border-radius: 4px;
  color: #334155;
}
.svc-more {
  font-size: 10px;
  color: #64748b;
}
.card-footer {
  display: flex;
  gap: 8px;
  margin-top: 6px;
  padding-top: 8px;
  border-top: 1px solid #f1f5f9;
}
.card-btn {
  flex: 1;
  text-align: center;
  padding: 6px 0;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  transition: all 0.2s;
  cursor: pointer;
}
.card-btn.call {
  background: #eff6ff;
  color: #2563eb;
  border: 1px solid #bfdbfe;
  text-decoration: none;
}
.card-btn.call:hover {
  background: #2563eb;
  color: white;
  border-color: #2563eb;
}
.card-btn.nav {
  background: #2563eb;
  color: white;
  border: 1px solid #2563eb;
}
.card-btn.nav:hover {
  background: #1d4ed8;
}

/* Map Panel */
.map-panel {
  flex: 1;
  height: 100%;
  min-width: 0;
  position: relative;
  background: #e2e8f0;
}
.map-container {
  width: 100%;
  height: 100%;
  min-height: 300px;
}

/* CareMap Map Controls Bar (Top Left Horizontal) */
.caremap-controls-bar {
  position: absolute;
  top: 16px;
  left: 16px;
  z-index: 35;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 4px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid #cbd5e1;
  backdrop-filter: blur(12px);
  padding: 4px;
  border-radius: 10px;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.1);
}
.map-control-btn {
  width: 32px;
  height: 32px;
  border-radius: 7px;
  background: #ffffff;
  color: #0f172a;
  border: 1px solid #e2e8f0;
  font-weight: 700;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  cursor: pointer;
}
.map-control-btn.view-3d-btn {
  font-size: 11px;
  font-weight: 800;
}
.map-control-btn.view-3d-btn.active {
  background: #2563eb;
  color: #ffffff;
  border-color: #2563eb;
}
.badge-3d {
  font-family: monospace, sans-serif;
  font-weight: 800;
  font-size: 11px;
}
.map-control-btn:hover {
  background: #2563eb;
  color: white;
  border-color: #2563eb;
}

/* Legend Pill */
.caremap-legend-pill {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 30;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 14px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid #cbd5e1;
  backdrop-filter: blur(12px);
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
  box-shadow: 0 8px 16px rgba(15, 23, 42, 0.08);
  color: #334155;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #334155;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.dot.patient { background: #2563eb; box-shadow: 0 0 8px #2563eb; }
.dot.campaign { background: #2563eb; }
.dot.health { background: #059669; }
.dot.food { background: #d97706; }

/* Responsive Media Queries */

/* Tablet & Laptop (769px - 1100px) */
@media (max-width: 1100px) {
  .sidebar-panel {
    width: 350px;
    min-width: 310px;
  }
  .search-filter-card {
    flex-direction: column;
  }
  .radius-trigger {
    width: 100%;
    justify-content: space-between;
  }
  .caremap-legend-pill {
    top: 12px;
    right: 12px;
    padding: 5px 10px;
    font-size: 10px;
    gap: 8px;
  }
  .caremap-route-banner {
    top: 60px;
    left: 12px;
    max-width: calc(100% - 24px);
    flex-wrap: wrap;
    padding: 10px 14px;
  }
}

/* Mobile Screens (<= 768px) */
@media (max-width: 768px) {
  .caremap-resources-page.light-theme {
    height: calc(100vh - 56px);
  }

  .mobile-view-toggle {
    display: flex !important;
  }

  .main-layout {
    flex-direction: column;
  }

  .sidebar-panel {
    width: 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;
    height: 100%;
    border-right: none;
  }

  .sidebar-panel.mobile-hidden {
    display: none !important;
  }

  .map-panel.mobile-hidden {
    display: none !important;
  }

  .map-panel {
    width: 100% !important;
    height: 100%;
  }

  .caremap-legend-pill {
    display: none; /* Hide legend pill on mobile to prevent clutter */
  }

  .caremap-controls-bar {
    top: 10px;
    left: 10px;
  }

  .caremap-route-banner {
    top: 54px;
    left: 10px;
    right: 10px;
    max-width: calc(100% - 20px);
  }
}
</style>

<style>
/* Global MapLibre Custom Markers & Popups */
.caremap-patient-marker {
  position: relative;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.caremap-patient-marker .radar-ping {
  position: absolute;
  inset: -6px;
  border-radius: 50%;
  background: rgba(37, 99, 235, 0.3);
  animation: ping 1.8s cubic-bezier(0, 0, 0.2, 1) infinite;
}
.caremap-patient-marker .core-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #2563eb;
  border: 2px solid #ffffff;
  box-shadow: 0 0 12px rgba(37, 99, 235, 0.6);
}

@keyframes ping {
  75%, 100% {
    transform: scale(2.2);
    opacity: 0;
  }
}

.caremap-resource-pin {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid white;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.3);
  cursor: pointer;
  transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
  display: flex;
  align-items: center;
  justify-content: center;
}
.caremap-resource-pin:hover {
  transform: scale(1.35);
  z-index: 99;
}
.caremap-resource-pin.selected {
  transform: scale(1.4);
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.5);
  z-index: 100;
}
.caremap-resource-pin.campaign-pulse {
  animation: pulse-border 1.5s infinite;
}

@keyframes pulse-border {
  0% { box-shadow: 0 0 0 0 rgba(37, 99, 235, 0.7); }
  70% { box-shadow: 0 0 0 10px rgba(37, 99, 235, 0); }
  100% { box-shadow: 0 0 0 0 rgba(37, 99, 235, 0); }
}

.caremap-resource-pin.campaign { background: #2563eb; }
.caremap-resource-pin.food { background: #d97706; }
.caremap-resource-pin.health { background: #059669; }
.caremap-resource-pin.mental { background: #7c3aed; }
.caremap-resource-pin.transit { background: #2563eb; }
.caremap-resource-pin.housing { background: #db2777; }
.caremap-resource-pin.social { background: #e11d48; }
.caremap-resource-pin.gym { background: #9333ea; }
.caremap-resource-pin.park { background: #059669; }

/* Light Theme MapLibre Popups */
.maplibregl-popup-content {
  background: #ffffff !important;
  color: #0f172a !important;
  border-radius: 14px !important;
  padding: 0 !important;
  border: 1px solid #cbd5e1 !important;
  box-shadow: 0 15px 35px rgba(15, 23, 42, 0.15) !important;
}
.maplibregl-popup-close-button {
  color: #64748b !important;
  font-size: 16px !important;
  padding: 6px 10px !important;
}

.caremap-popup-card {
  padding: 14px 16px;
  min-width: 220px;
  max-width: 260px;
}
.caremap-popup-card .popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.caremap-popup-card .category-badge {
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  padding: 3px 10px;
  border-radius: 20px;
  display: inline-block;
  background: #f1f5f9;
  color: #334155;
  border: 1px solid #cbd5e1;
}
.caremap-popup-card .category-badge.campaign { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }
.caremap-popup-card .category-badge.food { background: #fef3c7; color: #b45309; border: 1px solid #fde68a; }
.caremap-popup-card .category-badge.health, .caremap-popup-card .category-badge.clinic { background: #d1fae5; color: #047857; border: 1px solid #a7f3d0; }
.caremap-popup-card .category-badge.mental { background: #f3e8ff; color: #6b21a8; border: 1px solid #e9d5ff; }
.caremap-popup-card .category-badge.transit { background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
.caremap-popup-card .category-badge.housing { background: #fce7f3; color: #be185d; border: 1px solid #fbcfe8; }
.caremap-popup-card .category-badge.social { background: #ffe4e6; color: #be123c; border: 1px solid #fecdd3; }
.caremap-popup-card .category-badge.gym { background: #f3e8ff; color: #6b21a8; border: 1px solid #e9d5ff; }
.caremap-popup-card .category-badge.park { background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }
.caremap-popup-card .category-badge.pharmacy { background: #ccfbf1; color: #0f766e; border: 1px solid #99f6e4; }
.caremap-popup-card .category-badge.other { background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; }
.caremap-popup-card .distance-badge {
  font-size: 11px;
  font-weight: 700;
  color: #2563eb;
}
.caremap-popup-card .popup-title {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 6px 0;
}
.caremap-popup-card .popup-address, .caremap-popup-card .popup-hours {
  font-size: 11px;
  color: #475569;
  margin: 2px 0;
}
.caremap-popup-card .popup-actions {
  display: flex;
  gap: 6px;
  margin-top: 10px;
}
.caremap-popup-card .popup-btn {
  flex: 1;
  text-align: center;
  padding: 6px 0;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  text-decoration: none;
  border: none;
  cursor: pointer;
}
.caremap-popup-card .call-btn { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }
.caremap-popup-card .maps-btn { background: #2563eb; color: #ffffff; }
</style>
