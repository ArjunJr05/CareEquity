<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import IconBase from '../components/dashboard/IconBase.vue'
import { patientData, mlPredictionResults, predictionModelResults, isAnalyzed } from '../store/appState'
import { MAIN_BACKEND_URL } from '../config'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Page States
const selectedId = ref('cuyahoga')
const searchQuery = ref('')
const activeCategoryFilter = ref('all') // 'all', 'food', 'health', 'mental', 'transit', 'housing', 'social', 'pharmacy', 'other'
const viewMode = ref('map') // 'map' or 'list'
const radiusFilter = ref('25 miles')
const isRadiusDropdownOpen = ref(false)
const radiusOptionsList = ['10 miles', '25 miles', '50 miles']
const selectRadius = (val) => {
  radiusFilter.value = val
  isRadiusDropdownOpen.value = false
}

// Selected resource for the detail rail
const selectedResource = ref(null)

const isCategoryDropdownOpen = ref(false)
const activeCategoryLabel = computed(() => {
  const matched = chips.value.find(c => c.id === activeCategoryFilter.value)
  return matched ? matched.label : 'All'
})
const closeCategoryDropdown = (e) => {
  if (!e.target.closest('.category-dropdown-wrapper')) {
    isCategoryDropdownOpen.value = false
  }
}

// Toast notification state
const toastMsg = ref('')
const showToast = ref(false)

function triggerToast(msg) {
  toastMsg.value = msg
  showToast.value = true
  setTimeout(() => {
    showToast.value = false
  }, 3000)
}

// Bookmark storage
const bookmarkedIds = ref(new Set(['cuyahoga-food-1', 'cuyahoga-health-1']))

function toggleBookmark(id) {
  if (bookmarkedIds.value.has(id)) {
    bookmarkedIds.value.delete(id)
    triggerToast('Resource removed from bookmarks')
  } else {
    bookmarkedIds.value.add(id)
    triggerToast('Resource bookmarked successfully')
  }
}

// Mock Data for each county
const resourcesData = {
  cuyahoga: {
    cityName: 'Cleveland',
    mapCenterLabel: 'Cleveland',
    mapSubLabels: ['Lakewood', 'Cleveland Heights', 'Brooklyn', 'Garfield Heights'],
    categoriesCount: { food: 52, health: 78, mental: 36, transit: 24, housing: 31, social: 42, pharmacy: 28, other: 18 },
    resources: [
      {
        id: 'cuyahoga-food-1',
        name: 'Cleveland Food Bank',
        category: 'food',
        categoryLabel: 'Food Assistance',
        verified: true,
        distance: 2.3,
        rating: 4.8,
        reviewsCount: 124,
        services: ['Food pantry', 'SNAP support', 'Nutrition programs', 'Senior food programs', 'Kid\'s programs'],
        hoursText: 'Mon - Fri: 8:30 AM - 4:30 PM',
        eligibility: 'All residents welcome. No proof of income required.',
        address: '15500 S Waterloo Rd, Cleveland, OH 44110',
        phone: '(216) 738-2067',
        website: 'clevelandfoodbank.org',
        hoursList: [
          { days: 'Mon - Fri', time: '8:30 AM - 4:30 PM' },
          { days: 'Sat', time: '9:00 AM - 12:00 PM' },
          { days: 'Sun', time: 'Closed' }
        ],
        about: 'Cleveland Food Bank provides nutritious food to individuals and families in need through our network of partner agencies and programs.',
        whyRecommended: 'This resource addresses food insecurity which is a key factor contributing to elevated risk in this community.',
        mapPos: { x: 90, y: 35 }
      },
      {
        id: 'cuyahoga-health-1',
        name: 'MetroHealth Community Clinic',
        category: 'health',
        categoryLabel: 'Healthcare',
        verified: true,
        distance: 3.1,
        rating: 4.5,
        reviewsCount: 92,
        services: ['Primary care', 'Preventive care', 'Chronic disease mgmt', 'Sliding scale assistance'],
        hoursText: 'Mon - Fri: 8:00 AM - 5:00 PM',
        eligibility: 'Uninsured & insured. Sliding scale payment option.',
        address: '2500 Metrohealth Dr, Cleveland, OH 44109',
        phone: '(216) 778-7800',
        website: 'metrohealth.org/community',
        hoursList: [
          { days: 'Mon - Fri', time: '8:00 AM - 5:00 PM' },
          { days: 'Sat', time: '8:00 AM - 12:00 PM' },
          { days: 'Sun', time: 'Closed' }
        ],
        about: 'MetroHealth Community Clinic offers comprehensive medical services for adults and children, focusing on preventive health and wellness.',
        whyRecommended: 'This resource bridges critical healthcare accessibility gaps and reduces avoidable ER visits.',
        mapPos: { x: 55, y: 70 }
      },
      {
        id: 'cuyahoga-mental-1',
        name: 'Neighborhood Family Services',
        category: 'mental',
        categoryLabel: 'Mental Health',
        verified: true,
        distance: 3.4,
        rating: 4.4,
        reviewsCount: 76,
        services: ['Counseling', 'Psychiatry', 'Support groups', 'Crisis management'],
        hoursText: 'Mon - Fri: 9:00 AM - 6:00 PM',
        eligibility: 'All residents. Medicaid and private insurance accepted.',
        address: '11627 Clifton Blvd, Cleveland, OH 44102',
        phone: '(216) 281-2400',
        website: 'neofamily.org',
        hoursList: [
          { days: 'Mon - Fri', time: '9:00 AM - 6:00 PM' },
          { days: 'Sat & Sun', time: 'Closed' }
        ],
        about: 'Providing accessible, high-quality counseling and outpatient psychiatric services to help families navigate mental wellness.',
        whyRecommended: 'Addresses high rates of mental health risk indicators flagged in the area.',
        mapPos: { x: 35, y: 55 }
      },
      {
        id: 'cuyahoga-transit-1',
        name: 'RTA Community Transit Center',
        category: 'transit',
        categoryLabel: 'Transportation',
        verified: true,
        distance: 1.8,
        rating: 4.1,
        reviewsCount: 64,
        services: ['Bus passes', 'Route info', 'Paratransit services', 'Accessibility help'],
        hoursText: 'Mon - Sun: 6:00 AM - 8:00 PM',
        eligibility: 'All residents eligible. Seniors/Disabled qualify for discounts.',
        address: '1240 W 6th St, Cleveland, OH 44113',
        phone: '(216) 621-9500',
        website: 'riderta.com',
        hoursList: [
          { days: 'Mon - Sun', time: '6:00 AM - 8:00 PM' }
        ],
        about: 'RTA provides safe, reliable public transportation services connecting Greater Cleveland residents to jobs, medical centers, and schools.',
        whyRecommended: 'Mitigates transportation barriers preventing members from attending scheduled checkups.',
        mapPos: { x: 62, y: 48 }
      },
      {
        id: 'cuyahoga-housing-1',
        name: 'Cleveland Housing Network',
        category: 'housing',
        categoryLabel: 'Housing & Utilities',
        verified: false,
        distance: 4.2,
        rating: 4.3,
        reviewsCount: 88,
        services: ['Utility assistance', 'Rental counseling', 'Affordable housing leasing'],
        hoursText: 'Mon - Fri: 8:30 AM - 5:00 PM',
        eligibility: 'Low-to-moderate income residents of Cuyahoga County.',
        address: '2999 Payne Ave, Cleveland, OH 44114',
        phone: '(216) 574-7100',
        website: 'chnhousingpartners.org',
        hoursList: [
          { days: 'Mon - Fri', time: '8:30 AM - 5:00 PM' }
        ],
        about: 'CHN is a coalition of housing developers working to secure affordable housing and utility support programs for families.',
        whyRecommended: 'Combats housing instability which directly impacts chronic disease outcomes.',
        mapPos: { x: 78, y: 40 }
      },
      {
        id: 'cuyahoga-social-1',
        name: 'Step Forward Social Services',
        category: 'social',
        categoryLabel: 'Social Services',
        verified: true,
        distance: 2.9,
        rating: 4.6,
        reviewsCount: 51,
        services: ['Emergency aid', 'Head start education', 'Job training classes'],
        hoursText: 'Mon - Fri: 8:00 AM - 5:00 PM',
        eligibility: 'Families meeting income threshold guidelines.',
        address: '1801 Superior Ave, Cleveland, OH 44114',
        phone: '(216) 696-9077',
        website: 'stepforwardtoday.org',
        hoursList: [
          { days: 'Mon - Fri', time: '8:00 AM - 5:00 PM' }
        ],
        about: 'Ohio\'s largest Community Action Agency helping individuals find immediate relief and long-term economic independence.',
        whyRecommended: 'Resolves immediate economic distress in high social vulnerability index (SVI) tracts.',
        mapPos: { x: 82, y: 45 }
      }
    ]
  },
  wayne: {
    cityName: 'Detroit',
    mapCenterLabel: 'Detroit',
    mapSubLabels: ['Dearborn', 'Grosse Pointe', 'Hamtramck', 'Brooklyn (MI)'],
    categoriesCount: { food: 61, health: 84, mental: 42, transit: 31, housing: 48, social: 55, pharmacy: 36, other: 22 },
    resources: [
      {
        id: 'wayne-food-1',
        name: 'Gleaners Community Food Bank',
        category: 'food',
        categoryLabel: 'Food Assistance',
        verified: true,
        distance: 1.5,
        rating: 4.9,
        reviewsCount: 204,
        services: ['Mobile pantry', 'SNAP assistance', 'Youth nutrition', 'Fresh food distributions'],
        hoursText: 'Mon - Fri: 8:00 AM - 5:00 PM',
        eligibility: 'All Southeast Michigan residents.',
        address: '2131 Beaufait St, Detroit, MI 48207',
        phone: '(866) 453-2637',
        website: 'gcfb.org',
        hoursList: [
          { days: 'Mon - Fri', time: '8:00 AM - 5:00 PM' },
          { days: 'Sat', time: '9:00 AM - 1:00 PM' }
        ],
        about: 'Gleaners provides millions of pounds of emergency food annually to schools, soup kitchens, and pantries across Southeast Michigan.',
        whyRecommended: 'Directly addresses critical food deserts and food insecurity in the Detroit metropolitan area.',
        mapPos: { x: 80, y: 45 }
      },
      {
        id: 'wayne-health-1',
        name: 'Covenant Community Care Center',
        category: 'health',
        categoryLabel: 'Healthcare',
        verified: true,
        distance: 2.8,
        rating: 4.6,
        reviewsCount: 115,
        services: ['Family medicine', 'Dental clinic', 'Behavioral health', 'Prescription help'],
        hoursText: 'Mon - Fri: 8:30 AM - 5:00 PM',
        eligibility: 'All patients welcome. Sliding fee scale for uninsured.',
        address: '5716 Michigan Ave, Detroit, MI 48210',
        phone: '(313) 554-0485',
        website: 'covenantcommunitycare.org',
        hoursList: [
          { days: 'Mon - Fri', time: '8:30 AM - 5:00 PM' }
        ],
        about: 'A faith-based community health center providing high-quality care to patients regardless of their ability to pay.',
        whyRecommended: 'Fills crucial healthcare gaps in regions with high uninsured rates.',
        mapPos: { x: 45, y: 65 }
      },
      {
        id: 'wayne-transit-1',
        name: 'DDOT Transit Center',
        category: 'transit',
        categoryLabel: 'Transportation',
        verified: true,
        distance: 2.1,
        rating: 4.0,
        reviewsCount: 52,
        services: ['Bus passes', 'Route maps', 'ADA shuttle services'],
        hoursText: 'Mon - Sun: 5:00 AM - 11:00 PM',
        eligibility: 'All residents.',
        address: '1301 E Warren Ave, Detroit, MI 48207',
        phone: '(313) 933-1300',
        website: 'detroitmi.gov/ddot',
        hoursList: [
          { days: 'Mon - Sun', time: '5:00 AM - 11:00 PM' }
        ],
        about: 'DDOT is the primary public transit provider in Detroit, committed to providing clean, safe, and efficient transportation.',
        whyRecommended: 'Enables critical transit access for medical appointments.',
        mapPos: { x: 70, y: 35 }
      }
    ]
  },
  marion: {
    cityName: 'Indianapolis',
    mapCenterLabel: 'Indianapolis',
    mapSubLabels: ['Speedway', 'Lawrence', 'Greenwood', 'Carmel'],
    categoriesCount: { food: 38, health: 59, mental: 28, transit: 19, housing: 24, social: 33, pharmacy: 21, other: 12 },
    resources: [
      {
        id: 'marion-food-1',
        name: 'Gleaners Food Bank of Indiana',
        category: 'food',
        categoryLabel: 'Food Assistance',
        verified: true,
        distance: 3.2,
        rating: 4.8,
        reviewsCount: 145,
        services: ['Emergency pantry', 'Mobile distributions', 'SNAP registration support'],
        hoursText: 'Mon - Fri: 9:00 AM - 4:00 PM',
        eligibility: 'Indiana residents meeting USDA program guidelines.',
        address: '3737 Waldemere Ave, Indianapolis, IN 46241',
        phone: '(317) 925-0191',
        website: 'gleaners.org',
        hoursList: [
          { days: 'Mon - Fri', time: '9:00 AM - 4:00 PM' }
        ],
        about: 'Gleaners works to store and distribute food to local soup kitchens, food pantries, and shelters across Indianapolis.',
        whyRecommended: 'Combats regional food access gaps highlighted in the SDOH factors.',
        mapPos: { x: 30, y: 75 }
      },
      {
        id: 'marion-health-1',
        name: 'Eskenazi Health Center Pecar',
        category: 'health',
        categoryLabel: 'Healthcare',
        verified: true,
        distance: 2.6,
        rating: 4.4,
        reviewsCount: 89,
        services: ['Primary care', 'Pediatrics', 'Dental care', 'Nutrition coaching'],
        hoursText: 'Mon - Fri: 8:00 AM - 5:00 PM',
        eligibility: 'All patients. Financial assistance available based on household size.',
        address: '6940 Michigan Rd, Indianapolis, IN 46268',
        phone: '(317) 266-2901',
        website: 'eskenazihealth.edu',
        hoursList: [
          { days: 'Mon - Fri', time: '8:00 AM - 5:00 PM' }
        ],
        about: 'Eskenazi Health Center provides comprehensive family medicine and dental services, serving as a primary neighborhood health anchor.',
        whyRecommended: 'Closes community care gaps for high-risk diabetic and hypertensive patients.',
        mapPos: { x: 50, y: 30 }
      }
    ]
  },
  franklin: {
    cityName: 'Columbus',
    mapCenterLabel: 'Columbus',
    mapSubLabels: ['Grandview Heights', 'Bexley', 'Upper Arlington', 'Worthington'],
    categoriesCount: { food: 41, health: 62, mental: 31, transit: 20, housing: 28, social: 38, pharmacy: 25, other: 15 },
    resources: [
      {
        id: 'franklin-food-1',
        name: 'Mid-Ohio Food Collective',
        category: 'food',
        categoryLabel: 'Food Assistance',
        verified: true,
        distance: 2.9,
        rating: 4.8,
        reviewsCount: 162,
        services: ['Food pantry', 'Mobile markets', 'Nutrition education'],
        hoursText: 'Mon - Fri: 8:30 AM - 4:30 PM',
        eligibility: 'All residents of Franklin County.',
        address: '3960 Brookham Dr, Grove City, OH 43123',
        phone: '(614) 278-3130',
        website: 'mofc.org',
        hoursList: [
          { days: 'Mon - Fri', time: '8:30 AM - 4:30 PM' },
          { days: 'Sat', time: '9:00 AM - 1:00 PM' }
        ],
        about: 'Connecting hungry neighbors with nutritious food, the Mid-Ohio Food Collective aims to stabilize communities.',
        whyRecommended: 'Directly counters food insecurity trends observed in local tracts.',
        mapPos: { x: 35, y: 80 }
      },
      {
        id: 'franklin-health-1',
        name: 'PrimaryOne Health Center',
        category: 'health',
        categoryLabel: 'Healthcare',
        verified: true,
        distance: 1.9,
        rating: 4.5,
        reviewsCount: 97,
        services: ['Family medicine', 'OB/GYN services', 'Mental health therapy'],
        hoursText: 'Mon - Fri: 8:00 AM - 5:30 PM',
        eligibility: 'Uninsured/Insured welcome. Offers sliding fees.',
        address: '190 Carpenter St, Columbus, OH 43205',
        phone: '(614) 645-0556',
        website: 'primaryonehealth.org',
        hoursList: [
          { days: 'Mon - Fri', time: '8:00 AM - 5:30 PM' }
        ],
        about: 'Providing access to high-quality healthcare services to ensure wellness for all members of the community.',
        whyRecommended: 'Strengthens maternal-health and chronic disease preventive management.',
        mapPos: { x: 75, y: 55 }
      }
    ]
  }
}

const activeCommunity = computed(() => resourcesData[selectedId.value])

// Scraping and Live Resources Data State
const scrapedResources = ref([])
const isLoadingScrape = ref(false)

const currentResources = computed(() => {
  if (isAnalyzed.value) {
    return scrapedResources.value
  } else {
    return activeCommunity.value.resources
  }
})

// Chips definition based on state
const chips = computed(() => {
  if (isAnalyzed.value) {
    return [
      { id: 'all', label: 'All', imgSrc: '/assets/infinity.png', colorClass: 'grey' },
      { id: 'food', label: 'Food Access', imgSrc: '/assets/fork-and-knife.png', colorClass: 'orange' },
      { id: 'clinic', label: 'Healthcare Clinics', imgSrc: '/assets/healthcare.png', colorClass: 'green' },
      { id: 'gym', label: 'Fitness & Gyms', imgSrc: '/assets/dumbbell.png', colorClass: 'purple' },
      { id: 'park', label: 'Parks & Green Space', imgSrc: '/assets/park.png', colorClass: 'blue' }
    ]
  } else {
    return [
      { id: 'all', label: 'All', imgSrc: '/assets/infinity.png', colorClass: 'grey' },
      { id: 'food', label: 'Food Access', imgSrc: '/assets/fork-and-knife.png', colorClass: 'orange' },
      { id: 'health', label: 'Healthcare', imgSrc: '/assets/healthcare.png', colorClass: 'green' },
      { id: 'mental', label: 'Mental Health', imgSrc: '/assets/dumbbell.png', colorClass: 'purple' },
      { id: 'transit', label: 'Transportation', icon: 'trend', colorClass: 'blue' },
      { id: 'housing', label: 'Housing', icon: 'home', colorClass: 'pink' },
      { id: 'social', label: 'Social Services', icon: 'users', colorClass: 'rose' }
    ]
  }
})

function getCategoryCount(catId) {
  let list = currentResources.value
  
  if (radiusFilter.value) {
    const maxMiles = parseFloat(radiusFilter.value)
    if (!isNaN(maxMiles)) {
      list = list.filter(r => r.distance <= maxMiles)
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

  if (catId === 'all') {
    return list.length
  }
  return list.filter(r => r.category === catId).length
}

// Filter and Search Logic
const filteredResources = computed(() => {
  let list = currentResources.value

  // 1. Filter by category
  if (activeCategoryFilter.value !== 'all') {
    list = list.filter(r => r.category === activeCategoryFilter.value)
  }

  // 2. Filter by search query
  if (searchQuery.value.trim() !== '') {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(r => 
      r.name.toLowerCase().includes(q) || 
      (r.services && r.services.some(s => s.toLowerCase().includes(q))) ||
      (r.about && r.about.toLowerCase().includes(q))
    )
  }

  // 3. Filter by radius (miles)
  if (radiusFilter.value) {
    const maxMiles = parseFloat(radiusFilter.value)
    if (!isNaN(maxMiles)) {
      list = list.filter(r => r.distance <= maxMiles)
    }
  }

  return list
})

// Auto-select first resource on mount or community change
function syncSelectedResource() {
  if (filteredResources.value.length > 0) {
    selectedResource.value = filteredResources.value[0]
  } else {
    selectedResource.value = null
  }
}

function selectCommunity(id) {
  selectedId.value = id
  if (!isAnalyzed.value) {
    const lat = centerLatForCounty(id)
    const lon = centerLngForCounty(id)
    fetchScrapedResources(lat, lon)
  } else {
    syncSelectedResource()
  }
}

function selectCategory(cat) {
  activeCategoryFilter.value = cat
  syncSelectedResource()
}

function handleResourceClick(res) {
  selectedResource.value = res
  if (map && res.lat && res.lon) {
    map.setView([res.lat, res.lon], 14)
  }
}

function handleLocationFilterChange(e) {
  const val = e.target.value
  if (val.includes('Cuyahoga')) selectCommunity('cuyahoga')
  else if (val.includes('Wayne')) selectCommunity('wayne')
  else if (val.includes('Marion')) selectCommunity('marion')
  else if (val.includes('Franklin')) selectCommunity('franklin')
}

// Coordinate centers for legacy counties
function centerLatForCounty(id) {
  if (id === 'cuyahoga') return 41.4993
  if (id === 'wayne') return 42.3314
  if (id === 'marion') return 39.7684
  if (id === 'franklin') return 39.9612
  return 41.4993
}

function centerLngForCounty(id) {
  if (id === 'cuyahoga') return -81.6944
  if (id === 'wayne') return -83.0458
  if (id === 'marion') return -86.1581
  if (id === 'franklin') return -82.9988
  return -81.6944
}

// Fetch resources using the python scraping endpoint
async function fetchScrapedResources(lat, lon) {
  isLoadingScrape.value = true
  try {
    const res = await fetch(`${MAIN_BACKEND_URL}/api/patients/scrape-resources?lat=${lat}&lon=${lon}`)
    if (res.ok) {
      const data = await res.json()
      scrapedResources.value = data.resources
      syncSelectedResource()
      plotMarkers()
    }
  } catch (err) {
    console.error("Error fetching scraped resources:", err)
  } finally {
    isLoadingScrape.value = false
  }
}

// Get Color class for Category
function getCategoryColor(cat) {
  switch(cat) {
    case 'food': return 'orange'
    case 'health':
    case 'clinic': return 'green'
    case 'mental':
    case 'gym': return 'purple'
    case 'transit':
    case 'park': return 'blue'
    case 'housing': return 'pink'
    case 'social': return 'rose'
    case 'pharmacy': return 'teal'
    default: return 'grey'
  }
}

function getCategoryIcon(cat) {
  switch(cat) {
    case 'food': return 'pin'
    case 'health':
    case 'clinic': return 'pulse'
    case 'mental':
    case 'gym': return 'heart'
    case 'transit':
    case 'park': return 'home'
    case 'housing': return 'home'
    case 'social': return 'users'
    default: return 'puzzle'
  }
}

function getCategoryImgSrc(cat) {
  switch(cat) {
    case 'all': return '/assets/infinity.png'
    case 'food': return '/assets/fork-and-knife.png'
    case 'health':
    case 'clinic': return '/assets/healthcare.png'
    case 'mental':
    case 'gym': return '/assets/dumbbell.png'
    case 'park': return '/assets/park.png'
    default: return null
  }
}

function openResourceWebsite(website) {
  if (!website) return
  const url = website.startsWith('http') ? website : 'https://' + website
  window.open(url, '_blank')
}

// Leaflet Map logic
let map = null
let markerGroup = null

function initMap() {
  const container = document.getElementById('leaflet-resources-map')
  if (!container) return

  if (map) {
    map.remove()
  }

  const centerLat = isAnalyzed.value ? (patientData.value.lat || 41.4993) : centerLatForCounty(selectedId.value)
  const centerLng = isAnalyzed.value ? (patientData.value.long || -81.6944) : centerLngForCounty(selectedId.value)

  map = L.map('leaflet-resources-map', {
    zoomControl: true,
    attributionControl: false
  }).setView([centerLat, centerLng], 13)

  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    maxZoom: 19
  }).addTo(map)

  markerGroup = L.layerGroup().addTo(map)
  plotMarkers()
}

function plotMarkers() {
  if (!map || !markerGroup) return
  markerGroup.clearLayers()

  const centerLat = isAnalyzed.value ? (patientData.value.lat || 41.4993) : centerLatForCounty(selectedId.value)
  const centerLng = isAnalyzed.value ? (patientData.value.long || -81.6944) : centerLngForCounty(selectedId.value)

  // Standard marker for patient home/center point
  const homeIcon = L.divIcon({
    html: `<div class="home-marker-ping"><div class="ping-circle"></div><div class="core-circle"></div></div>`,
    className: 'custom-home-icon',
    iconSize: [24, 24],
    iconAnchor: [12, 12]
  })

  L.marker([centerLat, centerLng], { icon: homeIcon })
    .bindPopup(`<b>${isAnalyzed.value ? patientData.value.name + ' (Patient Residence)' : 'Center Location'}</b>`)
    .addTo(markerGroup)

  // Plot resources
  filteredResources.value.forEach(res => {
    let resLat = res.lat
    let resLon = res.lon

    if (!resLat || !resLon) {
      // Offset slightly for mock resources
      resLat = centerLat + ((res.mapPos?.y || 50) - 50) * 0.0005
      resLon = centerLng + ((res.mapPos?.x || 50) - 50) * 0.0005
    }

    const color = getCategoryColor(res.category)
    const colorHex = color === 'orange' ? '#f59e0b' : color === 'green' ? '#10b981' : color === 'purple' ? '#8b5cf6' : color === 'blue' ? '#3b82f6' : color === 'pink' ? '#ec4899' : '#f43f5e'

    const pinIcon = L.divIcon({
      html: `<div style="background-color: ${colorHex}; border: 2px solid white; width: 14px; height: 14px; border-radius: 50%; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>`,
      className: 'custom-resource-pin',
      iconSize: [14, 14],
      iconAnchor: [7, 7]
    })

    const marker = L.marker([resLat, resLon], { icon: pinIcon })
      .bindPopup(`<b>${res.name}</b><br>${res.categoryLabel}<br>${res.address}`)
      .addTo(markerGroup)

    marker.on('click', () => {
      selectedResource.value = res
    })
  })

  // Ensure Leaflet updates container layout size and centers perfectly
  setTimeout(() => {
    if (map) {
      map.invalidateSize()
      map.setView([centerLat, centerLng], 13)
    }
  }, 100)
}

// Watchers
watch(filteredResources, () => {
  plotMarkers()
})

watch(isAnalyzed, (newVal) => {
  if (newVal) {
    fetchScrapedResources(patientData.value.lat, patientData.value.long)
  }
})

watch(selectedId, () => {
  const lat = isAnalyzed.value ? patientData.value.lat : centerLatForCounty(selectedId.value)
  const lon = isAnalyzed.value ? patientData.value.long : centerLngForCounty(selectedId.value)
  fetchScrapedResources(lat, lon)
})

// Initialize resources data and map
onMounted(() => {
  const lat = isAnalyzed.value ? patientData.value.lat : centerLatForCounty(selectedId.value)
  const lon = isAnalyzed.value ? patientData.value.long : centerLngForCounty(selectedId.value)
  fetchScrapedResources(lat, lon)

  document.addEventListener('click', closeCategoryDropdown)

  setTimeout(() => {
    initMap()
  }, 200)
})

onUnmounted(() => {
  document.removeEventListener('click', closeCategoryDropdown)
  if (map) {
    map.remove()
  }
})
</script>

<template>
  <div class="community-resources-page">
    
    <!-- Toast notification message -->
    <Transition name="fade">
      <div v-if="showToast" class="toast-popup">
        <IconBase name="shield" :size="14" />
        <span>{{ toastMsg }}</span>
      </div>
    </Transition>

    <div class="main-layout">
      <!-- 1. Left/Center Main Panel -->
      <div class="content-body">
        
        <!-- Header -->
        <header class="page-header">
          <div>
            <h1>Community Resources</h1>
            <p class="description">Discover and connect members with local resources that support health and well-being.</p>
          </div>
        </header>

        <!-- Filters Bar Panel -->
        <section class="filters-panel card">
          <div class="filter-item search-col" style="flex: 1;">
            <span class="lbl">Search resources</span>
            <div class="search-input-wrapper">
              <IconBase name="search" :size="14" class="search-icon" />
              <input 
                v-model="searchQuery" 
                type="text" 
                placeholder="Search by name or service..." 
                class="search-input"
              />
            </div>
          </div>

          <div class="filter-item radius-col custom-radius-dropdown">
            <span class="lbl">Radius</span>
            <div class="custom-radius-trigger" style="position: relative;" @click="isRadiusDropdownOpen = !isRadiusDropdownOpen">
              <span class="selected-val font-bold">{{ radiusFilter }}</span>
              <span class="chevron-icon" :class="{ open: isRadiusDropdownOpen }">
                <IconBase name="chevron-down" :size="12" />
              </span>

              <!-- Custom Menu Popover -->
              <transition name="menu-fade">
                <ul v-if="isRadiusDropdownOpen" class="custom-radius-menu" @click.stop>
                  <li 
                    v-for="opt in radiusOptionsList" 
                    :key="opt"
                    class="radius-menu-item"
                    :class="{ active: radiusFilter === opt }"
                    @click="selectRadius(opt)"
                  >
                    <span class="item-text font-semibold">{{ opt }}</span>
                    <span v-if="radiusFilter === opt" class="active-check">✓</span>
                  </li>
                </ul>
              </transition>
            </div>

            <!-- Backdrop -->
            <div v-if="isRadiusDropdownOpen" class="dropdown-backdrop" @click="isRadiusDropdownOpen = false"></div>
          </div>
        </section>

        <!-- Segmented View Toggle Control & List Header -->
        <div class="results-header-row" style="margin-top: 18px; margin-bottom: 12px;">
          <h3 class="results-title">Nearby Resources <span class="count">({{ filteredResources.length }})</span></h3>
          
          <!-- Category Dropdown Button -->
          <div class="category-dropdown-wrapper">
            <button class="filter-dropdown-btn" @click.stop="isCategoryDropdownOpen = !isCategoryDropdownOpen">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="filter-icon"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
              <span class="font-bold">{{ activeCategoryLabel }}</span>
              <span class="count-badge">{{ getCategoryCount(activeCategoryFilter) }}</span>
              <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="chevron-icon"><polyline points="6 9 12 15 18 9"/></svg>
            </button>
            
            <transition name="dropdown-fade">
              <div class="filter-dropdown-menu" v-if="isCategoryDropdownOpen">
                <button 
                  v-for="chip in chips"
                  :key="chip.id"
                  class="dropdown-item category-dropdown-item"
                  :class="{ active: activeCategoryFilter === chip.id }"
                  @click="selectCategory(chip.id); isCategoryDropdownOpen = false"
                >
                  <span class="chip-icon-box mini" :class="chip.colorClass">
                    <img v-if="chip.imgSrc" :src="chip.imgSrc" style="width: 16px; height: 16px; object-fit: contain;" />
                    <IconBase v-else :name="chip.icon" :size="11" />
                  </span>
                  <span class="lbl-text">{{ chip.label }}</span>
                  <span class="count-val">{{ getCategoryCount(chip.id) }}</span>
                </button>
              </div>
            </transition>
          </div>
        </div>

        <!-- Collapsible Interactive Map Pane -->
        <Transition name="slide-up">
          <section v-if="viewMode === 'map'" class="map-section card">
            <div class="map-canvas-container" style="position: relative; height: auto;">
              <!-- Leaflet Map Container -->
              <div id="leaflet-resources-map" style="width: 100%; height: 500px; border-radius: 8px; z-index: 1;"></div>
            </div>

            <!-- Map Categories Legends Row -->
            <div class="map-legends-row">
              <span v-for="chip in chips.filter(c => c.id !== 'all')" :key="chip.id" class="legend-chip">
                <span class="chip-color" :class="chip.colorClass"></span> {{ chip.label }}
              </span>
            </div>
          </section>
        </Transition>

        <!-- Resources Results List -->
        <section class="resources-list-container">
          <div 
            v-for="res in filteredResources" 
            :key="res.id"
            class="resource-list-item card"
            :class="{ selected: res.id === selectedResource?.id }"
            @click="handleResourceClick(res)"
          >
            <!-- Category Icon bubble -->
            <div class="item-icon-col">
              <span class="category-icon-bubble" :class="getCategoryColor(res.category)">
                <img v-if="getCategoryImgSrc(res.category)" :src="getCategoryImgSrc(res.category)" style="width: 18px; height: 18px; object-fit: contain;" />
                <IconBase v-else
                  :name="getCategoryIcon(res.category)" 
                  :size="15" 
                />
              </span>
            </div>

            <!-- Resource Main details -->
            <div class="item-details-col">
              <div class="name-badge-row">
                <h4 class="res-name font-bold">{{ res.name }}</h4>
                <span v-if="res.verified" class="verified-badge">Verified</span>
              </div>
              <p class="res-sub-info font-semibold">
                {{ res.categoryLabel }} &bull; {{ res.distance }} miles away
              </p>
            </div>

            <!-- Services Offered -->
            <div class="item-services-col">
              <span class="label-header font-bold">Services</span>
              <p class="services-snippet">{{ res.services.slice(0, 3).join(', ') }}</p>
            </div>

            <!-- Hours and Eligibility -->
            <div class="item-hours-col">
              <span class="label-header font-bold">Hours</span>
              <p class="hours-snippet">{{ res.hoursText }}</p>
            </div>

            <div class="item-eligibility-col">
              <span class="label-header font-bold">Eligibility</span>
              <p class="eligibility-snippet">{{ res.eligibility }}</p>
            </div>

            <!-- Bookmark / Quick actions -->
            <div class="item-action-col" @click.stop="toggleBookmark(res.id)">
              <button class="bookmark-btn" :class="{ bookmarked: bookmarkedIds.has(res.id) }">
                <IconBase name="shield" :size="14" />
              </button>
            </div>
          </div>

          <div v-if="filteredResources.length === 0" class="empty-state-card card">
            <IconBase name="alert" :size="24" class="empty-icon" />
            <h4>No resources found matching search criteria.</h4>
            <p>Try resetting the category filter or searching with different keywords.</p>
          </div>
        </section>

        <!-- Pagination Bar -->
        <footer class="pagination-bar">
          <span class="showing-lbl">Showing 1-{{ filteredResources.length }} of {{ filteredResources.length }} resources</span>
        </footer>

      </div>

      <!-- 2. Right Detail Sidebar Panel (Selected Resource Details) -->
      <aside class="resource-detail-rail">
        <div v-if="selectedResource" class="detail-container">
          
          <!-- Back navigation & Close row -->
          <div class="detail-header-row">
            <button class="back-btn" @click="selectedResource = null">
              <IconBase name="trend" :size="12" style="transform: rotate(180deg);" /> Back to results
            </button>
            <button class="close-btn" @click="selectedResource = null">&times;</button>
          </div>

          <!-- Main Info Header -->
          <section class="detail-main-header">
            <div class="header-banner-row">
              <span class="detail-icon-bubble" :class="getCategoryColor(selectedResource.category)">
                <img v-if="getCategoryImgSrc(selectedResource.category)" :src="getCategoryImgSrc(selectedResource.category)" style="width: 24px; height: 24px; object-fit: contain;" />
                <IconBase v-else
                  :name="getCategoryIcon(selectedResource.category)" 
                  :size="20" 
                />
              </span>
              <div class="title-col">
                <div class="title-badge-row">
                  <h3 class="detail-name font-bold">{{ selectedResource.name }}</h3>
                  <span v-if="selectedResource.verified" class="verified-tag">Verified</span>
                </div>
                <p class="detail-sub-meta font-semibold">
                  {{ selectedResource.categoryLabel }} &bull; {{ selectedResource.distance }} miles away
                </p>
                <div class="rating-row font-semibold">
                  <span class="star-icon">&#9733;</span> {{ selectedResource.rating }} 
                  <span class="reviews-count font-normal">({{ selectedResource.reviewsCount }})</span>
                </div>
              </div>
            </div>
          </section>

          <!-- Core Call to Actions -->
          <section class="action-buttons-box">
            <button class="action-btn primary" @click="openResourceWebsite(selectedResource.website)" style="justify-content: center; width: 100%;">
              <IconBase name="external" :size="13" style="margin-right: 6px;" /> Know More
            </button>
          </section>

          <!-- Services Chips -->
          <section class="services-chips-box">
            <h4 class="sec-title font-bold">Services Offered</h4>
            <div class="chips-list">
              <span 
                v-for="serv in selectedResource.services" 
                :key="serv" 
                class="service-tag font-semibold"
              >
                {{ serv }}
              </span>
            </div>
          </section>

          <!-- Detailed Fields (Address, Phone, Website, Hours) -->
          <section class="fields-details-box">
            <div class="field-item">
              <span class="field-icon"><IconBase name="pin" :size="14" /></span>
              <div class="field-content">
                <span class="lbl font-bold">Address</span>
                <p class="val">{{ selectedResource.address }}</p>
              </div>
            </div>

            <div class="field-item">
              <span class="field-icon"><IconBase name="trend" :size="14" /></span>
              <div class="field-content">
                <span class="lbl font-bold">Phone</span>
                <p class="val">{{ selectedResource.phone }}</p>
              </div>
            </div>

            <div class="field-item">
              <span class="field-icon"><IconBase name="shield" :size="14" /></span>
              <div class="field-content">
                <span class="lbl font-bold">Website</span>
                <a :href="'https://' + selectedResource.website" target="_blank" class="val-link font-semibold">
                  {{ selectedResource.website }}
                  <span class="external-arrow">&nearr;</span>
                </a>
              </div>
            </div>

            <div class="field-item">
              <span class="field-icon"><IconBase name="pulse" :size="14" /></span>
              <div class="field-content">
                <span class="lbl font-bold">Hours</span>
                <ul class="hours-list">
                  <li v-for="h in selectedResource.hoursList" :key="h.days">
                    <span class="days font-semibold">{{ h.days }}:</span>
                    <span class="time">{{ h.time }}</span>
                  </li>
                </ul>
              </div>
            </div>
          </section>

          <!-- Eligibility Details -->
          <section class="eligibility-box">
            <h4 class="sec-title font-bold">Eligibility</h4>
            <p class="eligibility-text">{{ selectedResource.eligibility }}</p>
          </section>

          <!-- About resource -->
          <section class="about-box">
            <h4 class="sec-title font-bold">About this resource</h4>
            <p class="about-text">{{ selectedResource.about }}</p>
          </section>

          <!-- Why recommended Callout card -->
          <section class="why-recommended-callout">
            <span class="icon-bubble"><IconBase name="shield" :size="15" /></span>
            <div class="callout-content">
              <h5 class="callout-title font-bold">Why this resource is recommended</h5>
              <p class="callout-desc">{{ selectedResource.whyRecommended }}</p>
            </div>
          </section>

        </div>

        <div v-else class="no-selection-state">
          <IconBase name="pin" :size="32" class="placeholder-icon" />
          <p class="placeholder-text font-semibold">Select a community resource from the list to view full contact details, eligibility criteria, and clinical recommendations.</p>
        </div>
      </aside>
    </div>

  </div>
</template>

<style scoped>
.community-resources-page {
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

/* Card */
.card {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  padding: 16px;
}

/* Filters Panel */
.filters-panel {
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
}

.filter-item.location-col { flex: 1.2; min-width: 140px; }
.filter-item.search-col { flex: 2; min-width: 180px; }
.filter-item.radius-col { flex: 0 0 160px; }
.filter-item.category-col { flex: 1.2; min-width: 130px; }

.filter-item .lbl {
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

/* Custom Radius Dropdown UI */
.custom-radius-trigger {
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 5px 10px;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  user-select: none;
  transition: all 0.15s ease;
}

.custom-radius-trigger:hover {
  border-color: #cbd5e1;
  background: #f8fafc;
}

.selected-val {
  font-size: 0.76rem;
  color: var(--text-primary);
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

.custom-radius-menu {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: 8px;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.12);
  padding: 4px;
  margin: 0;
  list-style: none;
  z-index: 100;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.radius-menu-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.76rem;
  color: var(--text-primary);
  transition: background 0.15s ease;
}

.radius-menu-item:hover {
  background: #f1f5f9;
}

.radius-menu-item.active {
  background: #eff6ff;
  color: #1d4ed8;
  font-weight: 700;
}

.radius-menu-item .active-check {
  color: #2563eb;
  font-weight: bold;
}

.menu-fade-enter-active,
.menu-fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.menu-fade-enter-from,
.menu-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 10px;
  color: #94a3b8;
}

.search-input {
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 5px 8px 5px 30px;
  font-size: 0.76rem;
  color: var(--text-primary);
  background: #ffffff;
  outline: none;
  width: 100%;
}

.filters-btn {
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

/* Category Dropdown Filter Section */
.category-filter-section {
  margin-bottom: 14px;
  display: flex;
  align-items: center;
}

.category-dropdown-wrapper {
  position: relative;
  display: inline-block;
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

.count-badge {
  background: #eff6ff;
  color: #2563eb;
  padding: 2px 7px;
  border-radius: 10px;
  font-size: 0.68rem;
  font-weight: 750;
  margin-left: 2px;
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
  min-width: 220px;
  padding: 4px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.filter-dropdown-menu.left-align {
  left: 0;
  right: auto;
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
  display: flex;
  align-items: center;
  gap: 8px;
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

.category-dropdown-item .lbl-text {
  flex-grow: 1;
}

.category-dropdown-item .count-val {
  font-size: 0.68rem;
  color: #64748b;
  font-weight: 600;
}

.category-dropdown-item.active .count-val {
  color: #2563eb;
}

.chip-icon-box {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.chip-icon-box.mini {
  width: 22px;
  height: 22px;
  border-radius: 6px;
}

.chip-icon-box.orange { background: #fff9db; color: #f59e0b; }
.chip-icon-box.green { background: #e6fcf5; color: #10b981; }
.chip-icon-box.purple { background: #f3f0ff; color: #8b5cf6; }
.chip-icon-box.blue { background: #e7f5ff; color: #3b82f6; }
.chip-icon-box.pink { background: #fdf2f8; color: #ec4899; }
.chip-icon-box.rose { background: #fff1f2; color: #f43f5e; }
.chip-icon-box.grey { background: #f1f5f9; color: #64748b; }

/* Results header segmented view toggle control */
.results-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.results-title {
  margin: 0;
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--text-primary);
}

.results-title .count {
  font-weight: 500;
  color: var(--text-secondary);
}

.segmented-control {
  display: flex;
  background: #e2e8f0;
  border-radius: 8px;
  padding: 2.5px;
}

.segmented-control button {
  border: none;
  background: transparent;
  padding: 4px 10px;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--text-secondary);
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
}

.segmented-control button.active {
  background: #ffffff;
  color: var(--brand);
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

/* Collapsible Map Section */
.map-section {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.slide-up-enter-active, .slide-up-leave-active {
  transition: all 0.25s ease-out;
}
.slide-up-enter-from, .slide-up-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.map-canvas-container {
  height: 160px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
  background: #fafbfe;
  position: relative;
  overflow: hidden;
}

.map-svg {
  width: 100%;
  height: 100%;
  display: block;
}

.map-city-label {
  font-size: 8px;
  fill: #1e293b;
}

.map-suburb-text {
  font-size: 5px;
  fill: #94a3b8;
  font-weight: 700;
}

.pulse-ring {
  animation: pulse-effect 1.8s infinite ease-in-out;
  transform-origin: center;
}

@keyframes pulse-effect {
  0% { r: 6.5; opacity: 0.8; }
  100% { r: 16; opacity: 0; }
}

.map-pin-group {
  cursor: pointer;
}

.map-pin {
  transition: transform 0.15s ease, fill 0.15s ease;
}

.map-pin-group:hover .map-pin {
  transform: scale(1.35);
  fill: #1e3a8a;
}

.map-controls-box {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ctrl-btn {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  background: #ffffff;
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  cursor: pointer;
}

.ctrl-btn:hover {
  background: #f8fafc;
  color: var(--text-primary);
}

.map-legends-row {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
  border-top: 1px solid #f1f5f9;
  padding-top: 8px;
}

.legend-chip {
  font-size: 0.65rem;
  font-weight: 600;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 4px;
}

.chip-color {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}
.chip-color.orange { background: #f59e0b; }
.chip-color.green { background: #10b981; }
.chip-color.purple { background: #8b5cf6; }
.chip-color.blue { background: #3b82f6; }
.chip-color.pink { background: #ec4899; }
.chip-color.rose { background: #f43f5e; }

/* Resources List */
.resources-list-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.resource-list-item {
  display: grid;
  grid-template-columns: 36px 1.4fr 1.2fr 1fr 1fr 24px;
  align-items: center;
  gap: 16px;
  padding: 10px 14px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.resource-list-item:hover {
  border-color: #cbd5e1;
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.resource-list-item.selected {
  border-color: var(--brand);
  background: #f0f4ff;
  box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.08);
}

.category-icon-bubble {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.category-icon-bubble.orange { background: #fffbeb; color: #d97706; }
.category-icon-bubble.green { background: #ecfdf5; color: #059669; }
.category-icon-bubble.purple { background: #f5f3ff; color: #7c3aed; }
.category-icon-bubble.blue { background: #eff6ff; color: #2563eb; }
.category-icon-bubble.pink { background: #fdf2f8; color: #db2777; }
.category-icon-bubble.rose { background: #fff1f2; color: #e11d48; }

.name-badge-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.res-name {
  margin: 0;
  font-size: 0.78rem;
  color: var(--text-primary);
}

.verified-badge {
  font-size: 0.54rem;
  background: #d1fae5;
  color: #065f46;
  padding: 1px 5px;
  border-radius: 4px;
  font-weight: 700;
  white-space: nowrap;
}

.res-sub-info {
  margin: 2px 0 0;
  font-size: 0.68rem;
  color: var(--text-secondary);
}

.label-header {
  font-size: 0.58rem;
  color: var(--text-tertiary);
  text-transform: uppercase;
  display: block;
  margin-bottom: 2px;
}

.services-snippet, .hours-snippet, .eligibility-snippet {
  margin: 0;
  font-size: 0.68rem;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bookmark-btn {
  border: none;
  background: transparent;
  color: #cbd5e1;
  cursor: pointer;
  padding: 4px;
  display: flex;
  transition: color 0.15s ease;
}

.bookmark-btn:hover {
  color: #94a3b8;
}

.bookmark-btn.bookmarked {
  color: var(--brand);
}

/* Empty State Card */
.empty-state-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 30px;
}

.empty-icon {
  color: #94a3b8;
  margin-bottom: 10px;
}

.empty-state-card h4 {
  margin: 0 0 6px;
  font-size: 0.84rem;
  color: var(--text-primary);
}

.empty-state-card p {
  margin: 0;
  font-size: 0.74rem;
  color: var(--text-secondary);
}

/* Pagination Bar */
.pagination-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 14px;
  border-top: 1px solid var(--border);
  padding-top: 12px;
}

.showing-lbl {
  font-size: 0.72rem;
  color: var(--text-secondary);
}

.pager-btns {
  display: flex;
  align-items: center;
  gap: 4px;
}

.pager-btn {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  font-size: 0.7rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.pager-btn.outlined {
  background: #ffffff;
  border: 1px solid var(--border);
  color: var(--text-secondary);
}

.pager-btn.outlined:hover {
  background: #f8fafc;
  color: var(--text-primary);
}

.pager-btn.active {
  background: var(--brand);
  border: none;
  color: #ffffff;
}

.pager-dots {
  font-size: 0.7rem;
  color: var(--text-secondary);
  padding: 0 4px;
}

/* Right Detail Sidebar Panel */
.resource-detail-rail {
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

.detail-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.back-btn {
  border: none;
  background: transparent;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--brand);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 0;
}

.back-btn:hover {
  text-decoration: underline;
}

.close-btn {
  border: none;
  background: transparent;
  font-size: 1.15rem;
  color: var(--text-tertiary);
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.close-btn:hover {
  color: var(--text-primary);
}

.detail-icon-bubble {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.detail-icon-bubble.orange { background: #fff9db; color: #f59e0b; }
.detail-icon-bubble.green { background: #e6fcf5; color: #10b981; }
.detail-icon-bubble.purple { background: #f3f0ff; color: #8b5cf6; }
.detail-icon-bubble.blue { background: #e7f5ff; color: #3b82f6; }
.detail-icon-bubble.pink { background: #fdf2f8; color: #ec4899; }
.detail-icon-bubble.rose { background: #fff1f2; color: #f43f5e; }

.header-banner-row {
  display: flex;
  gap: 12px;
}

.title-col {
  display: flex;
  flex-direction: column;
}

.title-badge-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.detail-name {
  margin: 0;
  font-size: 0.95rem;
  color: var(--text-primary);
}

.verified-tag {
  font-size: 0.52rem;
  background: #d1fae5;
  color: #065f46;
  padding: 1px 5px;
  border-radius: 4px;
  font-weight: 700;
}

.detail-sub-meta {
  margin: 2px 0 0;
  font-size: 0.68rem;
  color: var(--text-secondary);
}

.rating-row {
  margin-top: 4px;
  font-size: 0.68rem;
  color: #fbbf24;
  display: flex;
  align-items: center;
  gap: 3px;
}

.rating-row .reviews-count {
  color: var(--text-secondary);
}

/* Action Buttons Box */
.action-buttons-box {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-btn {
  width: 100%;
  border-radius: var(--radius-md);
  font-size: 0.74rem;
  font-weight: 700;
  padding: 8px 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.action-btn.primary {
  background: var(--brand);
  border: none;
  color: #ffffff;
}
.action-btn.primary:hover {
  background: var(--brand-dark);
}

.action-btn.outlined {
  background: #ffffff;
  border: 1px solid var(--border);
  color: var(--text-primary);
}
.action-btn.outlined:hover {
  background: #f8fafc;
}

/* Services Offered */
.sec-title {
  margin: 0 0 6px;
  font-size: 0.7rem;
  color: var(--text-primary);
  text-transform: uppercase;
}

.chips-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.service-tag {
  font-size: 0.62rem;
  background: #f1f5f9;
  color: var(--text-secondary);
  padding: 2px 6px;
  border-radius: 4px;
}

/* Fields details box */
.fields-details-box {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field-item {
  display: flex;
  gap: 10px;
}

.field-icon {
  color: var(--text-tertiary);
  display: flex;
  margin-top: 2px;
}

.field-content {
  display: flex;
  flex-direction: column;
}

.field-content .lbl {
  font-size: 0.62rem;
  color: var(--text-tertiary);
  text-transform: uppercase;
}

.field-content .val {
  margin: 1px 0 0;
  font-size: 0.72rem;
  color: var(--text-primary);
  line-height: 1.35;
}

.val-link {
  margin: 1px 0 0;
  font-size: 0.72rem;
  color: var(--brand);
  text-decoration: none;
}
.val-link:hover {
  text-decoration: underline;
}

.hours-list {
  margin: 2px 0 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.hours-list li {
  font-size: 0.7rem;
}

.hours-list .days {
  color: var(--text-secondary);
  margin-right: 6px;
}

.hours-list .time {
  color: var(--text-primary);
}

/* Eligibility Box */
.eligibility-box .eligibility-text {
  margin: 0;
  font-size: 0.7rem;
  color: var(--text-secondary);
  line-height: 1.4;
}

/* About Box */
.about-box .about-text {
  margin: 0;
  font-size: 0.7rem;
  color: var(--text-secondary);
  line-height: 1.4;
}

/* Recommended Callout */
.why-recommended-callout {
  background: #f0fdf4;
  border: 1px solid #dcfce7;
  border-radius: 10px;
  padding: 10px 12px;
  display: flex;
  gap: 8px;
}

.why-recommended-callout .icon-bubble {
  color: #16a34a;
  display: flex;
  margin-top: 2px;
}

.callout-content {
  display: flex;
  flex-direction: column;
}

.callout-title {
  margin: 0;
  font-size: 0.72rem;
  color: #14532d;
}

.callout-desc {
  margin: 2px 0 0;
  font-size: 0.68rem;
  color: #166534;
  line-height: 1.35;
}

/* Placeholder state */
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

/* Home marker pulse */
.home-marker-ping {
  position: relative;
  width: 24px;
  height: 24px;
}
.ping-circle {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: rgba(79, 70, 229, 0.4);
  animation: marker-pulse 1.5s infinite ease-out;
}
.core-circle {
  position: absolute;
  top: 6px;
  left: 6px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #4f46e5;
  border: 2px solid #ffffff;
  box-shadow: 0 0 6px rgba(0, 0, 0, 0.4);
}
@keyframes marker-pulse {
  0% { transform: scale(0.5); opacity: 1; }
  100% { transform: scale(1.8); opacity: 0; }
}

/* ── RESPONSIVE OVERRIDES ── */
@media (max-width: 1100px) {
  .main-layout {
    grid-template-columns: 1fr;
    height: 100%;
    overflow-y: auto;
  }

  .content-body {
    height: auto;
    overflow: visible;
    padding: 16px 20px;
    flex-shrink: 0;
  }

  .resource-detail-rail {
    width: 100%;
    height: auto;
    border-left: none;
    border-top: 1px solid var(--border);
    overflow: visible;
    flex-shrink: 0;
  }
}

@media (max-width: 768px) {
  .filters-panel {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .filter-item {
    width: 100%;
    flex: none;
  }

  .filter-item.radius-col {
    flex: none;
  }
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
</style>
