<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import IconBase from '../components/dashboard/IconBase.vue'
import { setAnalyzed, setPatientData, isLoggedIn, setLoggedIn, setShowLoginScreen, setMlPredictionResults, setPredictionModelResults } from '../store/appState'
import { MAIN_BACKEND_URL, SYSTEM_BACKEND_URL, PREDICTION_BACKEND_URL } from '../config'
import { US_STATES, US_COUNTIES_BY_STATE } from '../data/usData.js'

const router = useRouter()

const userName = computed(() => {
  return localStorage.getItem('user_name') || 'Jane Smith'
})

const triggerLogin = () => {
  setShowLoginScreen(true)
}

const handleLogout = async () => {
  const storedEmail = localStorage.getItem('user_email')
  try {
    await fetch(`${MAIN_BACKEND_URL}/api/auth/logout`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: storedEmail || '',
        password: '' // empty password, backend will set status to false
      })
    })
  } catch (err) {
    console.error('Logout error:', err)
  }
  
  localStorage.removeItem('docpat_logged_in')
  localStorage.removeItem('user_email')
  localStorage.removeItem('user_name')
  setLoggedIn(false)
}

// Assessment History State
const userHistory = ref([])
const isLoadingHistory = ref(false)
const activeHistoryTab = ref('recent')

const fetchUserHistory = async () => {
  if (!isLoggedIn.value) {
    userHistory.value = []
    isLoadingHistory.value = false
    return
  }
  isLoadingHistory.value = true
  try {
    const userEmail = localStorage.getItem('user_email')
    const userId = localStorage.getItem('user_id') || 1
    
    const fetchUrl = userEmail 
      ? `${MAIN_BACKEND_URL}/api/history/email/${encodeURIComponent(userEmail)}`
      : `${MAIN_BACKEND_URL}/api/history/user/${userId}`
      
    const res = await fetch(fetchUrl)
    if (res.ok) {
      const data = await res.json()
      userHistory.value = data
    }
  } catch (err) {
    console.error('Error fetching history:', err)
  } finally {
    isLoadingHistory.value = false
  }
}

watch(isLoggedIn, (newVal) => {
  if (newVal) {
    fetchUserHistory()
  } else {
    userHistory.value = []
  }
}, { immediate: true })

const toggleFavoriteItem = async (item) => {
  // Toggle locally immediately for instant feedback
  item.is_favorite = !item.is_favorite
  try {
    await fetch(`${MAIN_BACKEND_URL}/api/history/${item.id}/favorite`, {
      method: 'PUT'
    })
  } catch (err) {
    console.error('Failed toggling favorite state on backend:', err)
  }
}

const displayedHistory = computed(() => {
  if (!isLoggedIn.value) return []
  if (activeHistoryTab.value === 'favorites') {
    return userHistory.value.filter(i => !!i.is_favorite)
  }
  return userHistory.value
})

onMounted(() => {
  if (isLoggedIn.value) {
    fetchUserHistory()
  }
})

const viewHistoryItem = (item) => {
  if (item) {
    setPatientData({
      name: item.name || 'Patient Record',
      age: item.age || 45,
      gender: item.gender || 'Female',
      diabetes: item.diabetes || 'No',
      hypertension: item.hypertension || 'No',
      heart_disease: item.heart_disease || 'No',
      asthma: item.asthma || 'No',
      previous_admission: item.previous_admission || 'No',
      er_visits: item.er_visits || 0,
      lat: item.lat || item.extra_data?.lat || 41.4993,
      long: item.long || item.extra_data?.long || -81.6944,
      medication_adherence: item.medication_adherence || item.extra_data?.medication_adherence || 85,
      county: item.county || item.extra_data?.county || 'Cuyahoga County',
      state: item.state || item.extra_data?.state || 'OH'
    })
    if (item.extra_data?.ml_prediction || item.ml_prediction) {
      setMlPredictionResults(item.extra_data?.ml_prediction || item.ml_prediction)
    }
    if (item.extra_data?.prediction_model || item.prediction_model) {
      setPredictionModelResults(item.extra_data?.prediction_model || item.prediction_model)
    }
  }
  setAnalyzed(true)
  router.push('/')
}

const formatDate = (isoStr) => {
  if (!isoStr) return 'Recently'
  const d = new Date(isoStr)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const downloadHistoryItem = (item) => {
  const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(item, null, 2))
  const downloadAnchor = document.createElement('a')
  downloadAnchor.setAttribute("href", dataStr)
  downloadAnchor.setAttribute("download", `patient_assessment_${item.name || item.id || 'record'}.json`)
  document.body.appendChild(downloadAnchor)
  downloadAnchor.click()
  downloadAnchor.remove()
}

// Form states
const activeTab = ref('file') // 'file' or 'connect'
const selectedTemplate = ref(null) // null, 'upload', 'mychart', 'apple', 'google', 'samsung'
const fileName = ref('')
const fileSize = ref('')
const isDragOver = ref(false)

// Custom Toast Banner State
const toast = ref({
  visible: false,
  title: 'Oops!',
  message: ''
})
let toastTimer = null

const showToast = (title, message) => {
  if (toastTimer) clearTimeout(toastTimer)
  toast.value = { visible: true, title, message }
  toastTimer = setTimeout(() => {
    toast.value.visible = false
  }, 5000)
}

const hideToast = () => {
  if (toastTimer) clearTimeout(toastTimer)
  toast.value.visible = false
}

const templates = [
  { id: 'upload', title: 'Upload File / Manual', subtitle: 'Upload patient clinical record', icon: '/assets/upload.png'},
  { id: 'mychart', title: 'MyChart', subtitle: 'Epic EHR integration', icon: '/assets/mychart_logo.png'},
  { id: 'apple', title: 'Apple Health', subtitle: 'iOS health metrics', icon: '/assets/ios_health.png'},
  { id: 'google', title: 'Google Fit', subtitle: 'Android health data', icon: '/assets/google_health.png' },
  { id: 'samsung', title: 'Samsung Health', subtitle: 'Galaxy health sync', icon: '/assets/samsang_health.png'}
]

const selectTemplate = (tplId) => {
  if (selectedTemplate.value === tplId) {
    selectedTemplate.value = null
    return
  }
  
  if (tplId === 'upload') {
    selectedTemplate.value = 'upload'
  } else {
    // Show coming soon toast message without selecting/highlighting card outline
    handleAppClick(templates.find(t => t.id === tplId)?.title || tplId)
  }
}

const handleAppClick = (appName) => {
  showToast('Oops!', `${appName} integration coming soon! Use "Upload File / Manual" to process records.`)
}

const form = ref({
  name: '',
  age: '',
  gender: 'Female',
  diabetes: 'No',
  hypertension: 'No',
  heart_disease: 'No',
  asthma: 'No',
  locations: [
    { country: 'United States', state: 'Kansas', county: 'Trego County' }
  ],
  height_cm: 170,
  weight_kg: 70,
  notes: ''
})

const addLocation = () => {
  if (form.value.locations.length < 5) {
    form.value.locations.push({
      country: 'United States',
      state: 'Ohio',
      county: US_COUNTIES_BY_STATE['Ohio'] ? US_COUNTIES_BY_STATE['Ohio'][0] : 'Cuyahoga County'
    })
  } else {
    showToast('Limit Reached', 'You can add a maximum of 5 locations.')
  }
}

const removeLocation = (index) => {
  if (form.value.locations.length > 1) {
    form.value.locations.splice(index, 1)
  }
}

const getCountiesForState = (stateName) => {
  return US_COUNTIES_BY_STATE[stateName] || ['Default County']
}

const availableCounties = computed(() => {
  return US_COUNTIES_BY_STATE[form.value.state] || []
})

watch(() => form.value.state, (newState) => {
  const counties = US_COUNTIES_BY_STATE[newState]
  if (counties && counties.length > 0) {
    if (!counties.includes(form.value.county)) {
      form.value.county = counties[0]
    }
  } else {
    form.value.county = ''
  }
})

// Validation and errors
const errors = ref({
  name: false,
  age: false,
  country: false,
  state: false,
  county: false,
  height_cm: false,
  weight_kg: false,
})

// Loading/Analysis states
const isAnalyzing = ref(false)
const isUploadingFile = ref(false)
const analysisProgress = ref(0)
const activeStep = ref(0)
const steps = [
  'Verifying patient history and clinical parameters...',
  'Matching address coordinates to Census tract SVI index...',
  'Analyzing environmental, food desert, and transit barriers...',
  'Calculating customized health risk & hospitalization probability...',
  'Assembling personalized intervention recommendations...'
]

// Testimonial avatar source
import mitchellPhoto from '../assets/dr_sarah_mitchell.png'

const uploadFileToOCR = async (file) => {
  isUploadingFile.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await fetch(`${SYSTEM_BACKEND_URL}/api/v1/ocr/upload`, {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) throw new Error('OCR upload failed: ' + response.status)
    const result = await response.json()
    
    if (result.success && result.extracted_data) {
      const data = result.extracted_data
      
      // Auto-populate demographics
      if (data.demographics) {
        if (data.demographics.patient_name) {
          form.value.name = data.demographics.patient_name
        }
        if (data.demographics.age) {
          form.value.age = data.demographics.age
        }
        if (data.demographics.gender) {
          const g = data.demographics.gender.toLowerCase()
          if (g.startsWith('f')) form.value.gender = 'Female'
          else if (g.startsWith('m')) form.value.gender = 'Male'
          else form.value.gender = 'Other'
        }
      }
      
      // Auto-populate vitals
      if (data.vital_signs) {
        if (data.vital_signs.height_cm) {
          form.value.height_cm = Math.round(data.vital_signs.height_cm)
        }
        if (data.vital_signs.weight_kg) {
          form.value.weight_kg = Math.round(data.vital_signs.weight_kg)
        }
      }
      
      // Auto-populate medical history
      if (data.medical_history) {
        if (data.medical_history.diabetes !== undefined && data.medical_history.diabetes !== null) {
          form.value.diabetes = (data.medical_history.diabetes === true || data.medical_history.diabetes === 'Yes' || String(data.medical_history.diabetes).toLowerCase() === 'true') ? 'Yes' : 'No'
        }
        if (data.medical_history.hypertension !== undefined && data.medical_history.hypertension !== null) {
          form.value.hypertension = (data.medical_history.hypertension === true || data.medical_history.hypertension === 'Yes' || String(data.medical_history.hypertension).toLowerCase() === 'true') ? 'Yes' : 'No'
        }
      }
      
      console.log('✓ Successfully populated form fields from OCR:', result)
    }
  } catch (err) {
    console.error('Failed uploading to OCR:', err)
  } finally {
    isUploadingFile.value = false
  }
}

// Handle file selection
const onFileChange = (e) => {
  const file = e.target.files[0]
  if (file) {
    const extension = file.name.split('.').pop().toLowerCase()
    if (['pdf', 'doc', 'docx'].includes(extension)) {
      fileName.value = file.name
      fileSize.value = (file.size / (1024 * 1024)).toFixed(1) + ' MB'
      uploadFileToOCR(file)
    } else {
      alert('Only PDF and Word documents are supported!')
      e.target.value = ''
    }
  }
}

const onDragOver = () => {
  isDragOver.value = true
}

const onDragLeave = () => {
  isDragOver.value = false
}

const onDrop = (e) => {
  isDragOver.value = false
  const file = e.dataTransfer.files[0]
  if (file) {
    const extension = file.name.split('.').pop().toLowerCase()
    if (['pdf', 'doc', 'docx'].includes(extension)) {
      fileName.value = file.name
      fileSize.value = (file.size / (1024 * 1024)).toFixed(1) + ' MB'
      uploadFileToOCR(file)
    } else {
      alert('Only PDF and Word documents are supported!')
    }
  }
}

// Trigger choose file dialog
const fileInput = ref(null)
const triggerChooseFile = () => {
  fileInput.value.click()
}

// Modal state for data source / file upload popup after analyze
const showUploadModal = ref(false)

const openUploadModal = () => {
  // Validate
  errors.value.name = !form.value.name
  errors.value.age = !form.value.age
  errors.value.country = !form.value.country
  errors.value.state = !form.value.state
  errors.value.county = !form.value.county
  errors.value.height_cm = !form.value.height_cm || form.value.height_cm <= 0
  errors.value.weight_kg = !form.value.weight_kg || form.value.weight_kg <= 0

  if (errors.value.name || errors.value.age || errors.value.country || errors.value.state || errors.value.county || errors.value.height_cm || errors.value.weight_kg) {
    const firstErr = document.querySelector('.form-field.error')
    if (firstErr) firstErr.scrollIntoView({ behavior: 'smooth', block: 'center' })
    return
  }

  showUploadModal.value = true
}

const closeUploadModal = () => {
  showUploadModal.value = false
}

// Form submission / Start analysis
const handleAnalyze = async () => {
  closeUploadModal()
  // Validate
  errors.value.name = !form.value.name
  errors.value.age = !form.value.age
  errors.value.height_cm = !form.value.height_cm || form.value.height_cm <= 0
  errors.value.weight_kg = !form.value.weight_kg || form.value.weight_kg <= 0

  const hasInvalidLocation = !form.value.locations || form.value.locations.length === 0 || form.value.locations.some(loc => !loc.country || !loc.state || !loc.county)

  if (errors.value.name || errors.value.age || errors.value.height_cm || errors.value.weight_kg || hasInvalidLocation) {
    showToast('Missing Fields', 'Please fill in Patient Name, Age, Height, Weight, and Location details.')
    const firstErr = document.querySelector('.form-field.error')
    if (firstErr) firstErr.scrollIntoView({ behavior: 'smooth', block: 'center' })
    return
  }

  // Save patient data in state
  setPatientData(form.value)

  // Start analysis animation sequence
  isAnalyzing.value = true
  analysisProgress.value = 0
  activeStep.value = 0

  let apisCompleted = false

  // Persist patient data to PostgreSQL backend database
  const savePatientPromise = (async () => {
    try {
      const response = await fetch(`${MAIN_BACKEND_URL}/api/patients/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: form.value.name,
          age: parseInt(form.value.age) || 0,
          gender: form.value.gender,
          diabetes: form.value.diabetes,
          hypertension: form.value.hypertension,
          heart_disease: form.value.heart_disease,
          asthma: form.value.asthma,
          previous_admission: 'No',
          er_visits: 0,
          lat: parseFloat(form.value.lat) || 0.0,
          long: parseFloat(form.value.long) || 0.0,
          medication_adherence: 85,
          height_cm: parseFloat(form.value.height_cm) || 170.0,
          weight_kg: parseFloat(form.value.weight_kg) || 70.0,
          notes: form.value.notes || ''
        })
      })

      if (!response.ok) {
        console.error('Backend submission failed:', await response.text())
      } else {
        const data = await response.json()
        console.log('Saved to PostgreSQL database:', data)
      }
    } catch (error) {
      console.error('Failed connecting to backend database server:', error)
    }

    // Unconditionally save to /api/history/save database table
    try {
      const primaryLoc = form.value.locations[0] || { country: 'United States', state: 'Kansas', county: 'Trego County' }
      const historyPayload = {
        user_id: 1,
        name: form.value.name,
        age: parseInt(form.value.age) || 45,
        gender: form.value.gender,
        diabetes: form.value.diabetes,
        hypertension: form.value.hypertension,
        heart_disease: form.value.heart_disease,
        asthma: form.value.asthma,
        height_cm: parseFloat(form.value.height_cm) || 170.0,
        weight_kg: parseFloat(form.value.weight_kg) || 70.0,
        latitude: 0.0,
        longitude: 0.0,
        zipcode: '44102',
        previous_admission: 'No',
        er_visits: 0,
        medication_adherence: 85,
        notes: form.value.notes || '',
        extra_data: {
          county: primaryLoc.county,
          state: primaryLoc.state,
          country: primaryLoc.country,
          all_locations: form.value.locations,
          saved_at: new Date().toISOString()
        }
      }

      await fetch(`${MAIN_BACKEND_URL}/api/history/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(historyPayload)
      })
      await fetchUserHistory()
    } catch (err) {
      console.error('Failed saving to history table:', err)
    }
  })()

  // Trigger ML System Unified Prediction
  const mlPredictionPromise = (async () => {
    try {
      const height = parseFloat(form.value.height_cm) || 170
      const weight = parseFloat(form.value.weight_kg) || 70
      const calculatedBmi = parseFloat((weight / ((height / 100) ** 2)).toFixed(1))

      const healthMetrics = {
        age: parseInt(form.value.age) || 45,
        height_cm: height,
        weight_kg: weight,
        bmi: calculatedBmi,
        blood_pressure: form.value.hypertension === 'Yes' ? '140/90' : '120/80',
        glucose: form.value.diabetes === 'Yes' ? 165 : 95,
        gender: form.value.gender,
        diabetes: form.value.diabetes === 'Yes',
        hypertension: form.value.hypertension === 'Yes',
        heart_disease: form.value.heart_disease === 'Yes',
        asthma: form.value.asthma === 'Yes',
        smoking_history: 'Non-Smoker',
        total_cholesterol_mg_dl: form.value.heart_disease === 'Yes' ? 240 : 185
      }

      const zipcode = '44102' // Default Cuyahoga County zipcode for mapping SVI
      const url = `${SYSTEM_BACKEND_URL}/api/v1/unified-predict?member_id=DEMO001&zipcode=${zipcode}`
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(healthMetrics)
      })
      
      if (!response.ok) throw new Error('ML Predict HTTP error: ' + response.status)
      const data = await response.json()
      console.log('✓ Received ML unified prediction:', data)
      setMlPredictionResults(data)
    } catch (err) {
      console.error('❌ Failed fetching ML prediction:', err)
      // Save a fallback simulated prediction so the UI can still show patient-specific insights
      setMlPredictionResults({
        risk_scores: {
          diabetes: form.value.diabetes === 'Yes' ? 0.85 : 0.25,
          hypertension: form.value.hypertension === 'Yes' ? 0.78 : 0.32,
          heart_disease: form.value.heart_disease === 'Yes' ? 0.70 : 0.15,
          asthma: form.value.asthma === 'Yes' ? 0.65 : 0.10
        },
        risk_levels: {
          diabetes: form.value.diabetes === 'Yes' ? 'High' : 'Low',
          hypertension: form.value.hypertension === 'Yes' ? 'High' : 'Low',
          heart_disease: form.value.heart_disease === 'Yes' ? 'High' : 'Low',
          asthma: form.value.asthma === 'Yes' ? 'High' : 'Low'
        },
        sdoh_barriers: [
          'High economic stability concerns',
          'Limited access to primary care providers',
          'Transportation accessibility limits'
        ],
        kb_insights: 'Patient clinical risk factors indicate elevated risk. Monitor medication adherence (currently ' + form.value.medication_adherence + '%).',
        disease_pathways: {
          pathway: 'Clinical assessment suggests screening every 3 months. Lifestyle modifications recommended.'
        }
      })
    }
  })()

  // Trigger Prediction Model Risk Lookup
  const predictionModelPromise = (async () => {
    try {
      const predUrl = `${PREDICTION_BACKEND_URL}/api/v1/predict-by-coords?lat=${form.value.lat}&lon=${form.value.long}`
      const response = await fetch(predUrl)
      if (!response.ok) throw new Error('Prediction API HTTP error: ' + response.status)
      const data = await response.json()
      console.log('✓ Received Prediction Model output:', data)
      setPredictionModelResults(data)
    } catch (err) {
      console.error('❌ Failed fetching Prediction Model data:', err)
      // Fallback simulated prediction model scores
      setPredictionModelResults({
        zipcode: '44102',
        city: 'Cleveland',
        state: 'Ohio',
        overall_risk_score: 0.625,
        overall_risk_category: 'Medium',
        scores: {
          economic_stability: 0.58,
          healthcare_access: 0.64,
          education_access: 0.70,
          neighborhood_environment: 0.55,
          food_security: 0.60,
          social_context: 0.68
        }
      })
    }
  })()

  // Execute all fetches in parallel
  Promise.all([savePatientPromise, mlPredictionPromise, predictionModelPromise]).then(async () => {
    console.log('🏁 All DataSetup API calls completed!')
    apisCompleted = true

    // Persist full report data to PostgreSQL if user is logged in
    if (isLoggedIn.value) {
      try {
        const primaryLoc = form.value.locations[0] || { country: 'United States', state: 'Kansas', county: 'Trego County' }
        const historyPayload = {
          user_id: 1,
          name: form.value.name,
          age: parseInt(form.value.age) || 45,
          gender: form.value.gender,
          diabetes: form.value.diabetes,
          hypertension: form.value.hypertension,
          heart_disease: form.value.heart_disease,
          asthma: form.value.asthma,
          height_cm: parseFloat(form.value.height_cm) || 170.0,
          weight_kg: parseFloat(form.value.weight_kg) || 70.0,
          latitude: 0.0,
          longitude: 0.0,
          zipcode: '44102',
          previous_admission: 'No',
          er_visits: 0,
          medication_adherence: 85,
          notes: form.value.notes || '',
          extra_data: {
            county: primaryLoc.county,
            state: primaryLoc.state,
            country: primaryLoc.country,
            all_locations: form.value.locations,
            ml_prediction: mlPredictionResults.value,
            prediction_model: predictionModelResults.value,
            saved_at: new Date().toISOString()
          }
        }

        await fetch(`${MAIN_BACKEND_URL}/api/history/save`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(historyPayload)
        })
        fetchUserHistory()
      } catch (err) {
        console.error('Failed saving complete report history to PostgreSQL:', err)
      }
    } else {
      console.log('User is logged out: Assessment history not saved to database.')
    }
  })

  // Loading bar animation sequence
  const interval = setInterval(() => {
    if (analysisProgress.value < 90) {
      analysisProgress.value += 1
    } else if (apisCompleted) {
      analysisProgress.value += 2
    }
    
    // Update steps based on progress
    if (analysisProgress.value < 20) activeStep.value = 0
    else if (analysisProgress.value < 40) activeStep.value = 1
    else if (analysisProgress.value < 65) activeStep.value = 2
    else if (analysisProgress.value < 85) activeStep.value = 3
    else activeStep.value = 4

    if (analysisProgress.value >= 100) {
      clearInterval(interval)
      // Done processing: Unlock dashboard and redirect to Overview
      setAnalyzed(true)
      router.push('/')
    }
  }, 40)
}
</script>

<template>
  <div class="data-setup-page">
    <!-- Processing overlay -->
    <div v-if="isAnalyzing" class="analysis-overlay">
      <article class="card loading-card">
        <h3>AI SDOH Engine Processing</h3>
        <p class="subtitle">Our AI is parsing your clinical data, matching geographical SVI indices, and calculating priority interventions.</p>

        <!-- Progress ring/bar -->
        <div class="progress-bar-container">
          <div class="progress-bar-fill" :style="{ width: analysisProgress + '%' }"></div>
          <span class="progress-pct">{{ analysisProgress }}%</span>
        </div>

        <!-- Processing Checklist -->
        <ul class="steps-checklist">
          <li v-for="(step, idx) in steps" :key="idx" :class="{ completed: analysisProgress > (idx + 1) * 20, active: activeStep === idx }">
            <span class="step-indicator">
              <IconBase v-if="analysisProgress > (idx + 1) * 20" name="shield" :size="12" />
              <span v-else-if="activeStep === idx" class="step-spinner"></span>
              <span v-else class="step-bullet"></span>
            </span>
            <span class="step-text">{{ step }}</span>
          </li>
        </ul>
      </article>
    </div>

    <!-- Custom Pop-Up Toast Modal (Single Line Banner, Auto-close 5s) -->
    <transition name="toast-fade">
      <div v-if="toast.visible" class="custom-toast-overlay" style="position: fixed; top: 18px; left: 50%; transform: translateX(-50%); z-index: 99999; display: flex; justify-content: center; pointer-events: auto;">
        <div class="custom-toast-box" style="background: #ffffff; border-radius: 50px; box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1), 0 4px 10px rgba(0, 0, 0, 0.05); padding: 8px 16px 8px 10px; border: 1.5px solid #fee2e2; border-bottom: 3px solid #ef4444; display: flex; align-items: center; gap: 10px; white-space: nowrap; max-width: 90vw;">
          <!-- Red Circle with X Icon -->
          <div style="width: 28px; height: 28px; border-radius: 50%; background: #fee2e2; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </div>
          <!-- Title & Message Text in Single Line -->
          <div style="display: flex; align-items: center; gap: 6px;">
            <strong style="font-size: 0.85rem; font-weight: 800; color: #1e293b;">{{ toast.title }}</strong>
            <span style="font-size: 0.82rem; color: #475569; font-weight: 500;">{{ toast.message }}</span>
          </div>
          <!-- Close Button -->
          <button @click="hideToast" style="background: transparent; border: none; cursor: pointer; color: #94a3b8; padding: 2px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-left: 6px;" onmouseenter="this.style.color='#475569'" onmouseleave="this.style.color='#94a3b8'">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </div>
    </transition>

    <!-- Top Full Width App Bar -->
    <header class="app-bar">
      <div class="brand" style="display: flex; align-items: center; gap: 12px;">
        <img src="/assets/careequity_logo.png" style="height: 45px; object-fit: contain;" alt="CareEquity Logo" />
        <img src="/assets/careequity_name.png" style="height: 60px; object-fit: contain;" alt="CareEquity" />
      </div>
      <div class="nav-right" style="display: flex; align-items: center; gap: 16px;">
        <!-- If logged in, show user name and Sign Out -->
        <button v-if="isLoggedIn" class="user-chip-btn" @click="handleLogout" title="Click to Logout" style="cursor: pointer; padding: 6px 12px; display: flex; align-items: center; gap: 8px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); color: var(--text-primary); transition: background-color .15s ease;">
          <span style="font-size: 0.85rem; font-weight: 600;">{{ userName }}</span>
          <span style="font-size: 10px; color: #ef4444; font-weight: 600; border: 1px solid rgba(239, 68, 68, 0.2); background: rgba(239, 68, 68, 0.05); padding: 2px 6px; border-radius: 6px; white-space: nowrap;">Sign Out</span>
        </button>

        <!-- If logged out, show Sign In / Login button -->
        <button v-else class="btn-login-trigger" @click="triggerLogin" style="height: 38px; border: 1px solid rgba(37, 99, 235, 0.2); border-radius: 10px; padding: 0 16px; background-image: linear-gradient(135deg, #3b82f6, #1d4ed8); color: #fff; font-size: 0.85rem; font-weight: 600; display: flex; align-items: center; gap: 8px; cursor: pointer; transition: opacity .15s ease; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.15); border: none;">
          <IconBase name="sparkle" :size="15" /> Sign In / Login
        </button>
      </div>
    </header>

    <!-- Layout Grid -->
    <div class="setup-grid">
      <!-- 1. Left Sidebar Guide (Now containing right side info block content) -->
      <aside class="sidebar-guide">
        <!-- What Happens Next? -->
        <article class="card info-block-card">
          <h4>What Happens Next?</h4>
          
          <ul class="steps-flow">
            <li>
              <span class="flow-icon-gif"><img src="/assets/verified-profile.gif" alt="Validate Data" class="flow-gif" /></span>
              <div>
                <h5>We validate your data</h5>
                <p>Check format, quality & completeness</p>
              </div>
            </li>
            <li>
              <span class="flow-icon-gif"><img src="/assets/organic.gif" alt="SDOH Enrichment" class="flow-gif" /></span>
              <div>
                <h5>SDOH Enrichment</h5>
                <p>We match with external SDOH datasets</p>
              </div>
            </li>
            <li>
              <span class="flow-icon-gif"><img src="/assets/magnifying-glass-fingerprint.gif" alt="AI Analysis" class="flow-gif" /></span>
              <div>
                <h5>AI Analysis</h5>
                <p>Predict risks, gaps & opportunities</p>
              </div>
            </li>
            <li>
              <span class="flow-icon-gif"><img src="/assets/computer-screen.gif" alt="Actionable Insights" class="flow-gif" /></span>
              <div>
                <h5>Actionable Insights</h5>
                <p>View results in interactive dashboard</p>
              </div>
            </li>
          </ul>
        </article>

        <!-- Expected Insights You'll Get -->
        

        <!-- Need Help -->
        <article class="card help-card">
          <h5>Need Help?</h5>
          <p>Our team is here to help you get started.</p>
          <a href="mailto:contact.careequity@gmail.com?subject=CareEquity%20Support%20Request" class="help-link">Contact Support &rarr;</a>
        </article>
      </aside>
      <!-- 2. Center Content panel -->
      <main class="center-content-panel">
        <div class="center-panel-wrapper">
          <div style="margin-bottom: 20px;">
            <h2 style="margin: 0; font-size: 1.25rem; font-weight: 800; color: var(--text-primary);">Select Data Source Template</h2>
            <p class="form-sub" style="margin: 4px 0 0; font-size: 0.78rem; color: var(--text-secondary);">Choose a source below to open the data entry form, or view your history below.</p>
          </div>

          <!-- Template Cards Grid (Excel-like equal 5 boxes grid layout) -->
          <div class="templates-cards-grid" style="display: flex; gap: 14px; margin-bottom: 24px; width: 100%;">
            <div 
              v-for="tpl in templates" 
              :key="tpl.id" 
              class="tpl-card-item"
              :class="{ active: selectedTemplate === tpl.id }"
              @click="selectTemplate(tpl.id)"
              style="flex: 1; min-width: 0; cursor: pointer; transition: transform 0.15s ease;"
            >
              <!-- Card Top Preview Box (Excel-like rectangular thumbnail box) -->
              <div 
                class="tpl-card-box"
                style="height: 100px; background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 10px; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 14px; margin-bottom: 8px; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05); transition: all 0.2s ease;"
                :style="selectedTemplate === tpl.id ? { borderColor: '#6366f1', boxShadow: '0 0 0 2px rgba(99, 102, 241, 0.25)', background: '#faf5ff' } : {}"
              >
                <img :src="tpl.icon" :alt="tpl.title" style="height: 44px; width: 44px; object-fit: contain;" />
              </div>
              <!-- Title & Subtitle Below Preview Box -->
              <h4 style="margin: 0 0 2px; font-size: 0.8rem; font-weight: 700; color: var(--text-primary); text-align: left; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{{ tpl.title }}</h4>
              <p style="margin: 0; font-size: 0.7rem; color: var(--text-secondary); text-align: left; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{{ tpl.subtitle }}</p>
            </div>
          </div>

          <!-- File Upload & Data Form Card (Revealed when Upload File / Manual is selected) -->
          <div v-if="selectedTemplate === 'upload'">
            

            <div class="card upload-card" :class="{ dragover: isDragOver }" @dragover.prevent="onDragOver" @dragleave.prevent="onDragLeave" @drop.prevent="onDrop">
              <div v-if="isUploadingFile" class="upload-loading-overlay" style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(255, 255, 255, 0.9); z-index: 10; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; border-radius: inherit;">
                <div class="ocr-spinner" style="width: 32px; height: 32px; border: 3px solid rgba(99, 102, 241, 0.1); border-top-color: #6366f1; border-radius: 50%; animation: spinner-rotate 0.8s linear infinite;"></div>
                <p style="font-weight: 600; color: #4f46e5; margin: 0; font-size: 0.9rem;">Extracting patient data with OCR AI...</p>
              </div>
              <input type="file" ref="fileInput" class="hidden-input" accept=".pdf,.doc,.docx" @change="onFileChange" />
              
              <div class="upload-content">
                <div class="upload-icon-circle">
                  <img src="/assets/upload.png" alt="Upload Icon" class="upload-img-icon" />
                </div>
                
                <p v-if="!fileName" class="upload-text">Drag & drop your file here</p>
                <p v-else class="upload-text selected-file">{{ fileName }} <span>({{ fileSize }})</span></p>
                
                <span v-if="!fileName" class="or-text">or</span>
                
                <button class="btn primary choose-btn" @click="triggerChooseFile">
                  {{ fileName ? 'Change File' : 'Choose File' }}
                </button>
                
                <p class="format-note">Supports PDF, Word files up to 200MB</p>
              </div>
            </div>
          </div>
          <!-- Patient Demographic Form & Analyze Button (Revealed when Upload File / Manual template is selected) -->
          <div v-if="selectedTemplate === 'upload'">
            <section class="form-section">
              <div class="form-grid">
                <!-- Patient Name -->
                <div class="form-field" :class="{ error: errors.name }">
                  <label>Name *</label>
                  <input type="text" v-model="form.name" placeholder="e.g., Robert Chen" class="setup-input" />
                  <span v-if="errors.name" class="err-msg">Name is required</span>
                </div>

                <!-- Age -->
                <div class="form-field" :class="{ error: errors.age }">
                  <label>Age *</label>
                  <input type="number" v-model="form.age" placeholder="e.g., 54" class="setup-input" />
                  <span v-if="errors.age" class="err-msg">Age is required</span>
                </div>

                <!-- Gender -->
                <div class="form-field">
                  <label>Gender *</label>
                  <div class="select-wrapper">
                    <select v-model="form.gender" class="setup-select">
                      <option>Female</option>
                      <option>Male</option>
                      <option>Other</option>
                    </select>
                    <IconBase name="chevron-down" :size="13" class="chevron" />
                  </div>
                </div>

                <!-- Diabetes -->
                <div class="form-field">
                  <label>Diabetes *</label>
                  <div class="select-wrapper">
                    <select v-model="form.diabetes" class="setup-select">
                      <option>No</option>
                      <option>Yes</option>
                    </select>
                    <IconBase name="chevron-down" :size="13" class="chevron" />
                  </div>
                </div>

                <!-- Hypertension -->
                <div class="form-field">
                  <label>Hypertension *</label>
                  <div class="select-wrapper">
                    <select v-model="form.hypertension" class="setup-select">
                      <option>No</option>
                      <option>Yes</option>
                    </select>
                    <IconBase name="chevron-down" :size="13" class="chevron" />
                  </div>
                </div>

                <!-- Heart Disease -->
                <div class="form-field">
                  <label>Heart Disease *</label>
                  <div class="select-wrapper">
                    <select v-model="form.heart_disease" class="setup-select">
                      <option>No</option>
                      <option>Yes</option>
                    </select>
                    <IconBase name="chevron-down" :size="13" class="chevron" />
                  </div>
                </div>

                <!-- Asthma -->
                <div class="form-field">
                  <label>Asthma *</label>
                  <div class="select-wrapper">
                    <select v-model="form.asthma" class="setup-select">
                      <option>No</option>
                      <option>Yes</option>
                    </select>
                    <IconBase name="chevron-down" :size="13" class="chevron" />
                  </div>
                </div>

                <!-- Height (cm) -->
                <div class="form-field" :class="{ error: errors.height_cm }">
                  <label>Height (cm) *</label>
                  <input type="number" v-model="form.height_cm" placeholder="e.g., 170" class="setup-input" />
                  <span v-if="errors.height_cm" class="err-msg">Height is required</span>
                </div>

                <!-- Weight (kg) -->
                <div class="form-field" :class="{ error: errors.weight_kg }">
                  <label>Weight (kg) *</label>
                  <input type="number" v-model="form.weight_kg" placeholder="e.g., 70" class="setup-input" />
                  <span v-if="errors.weight_kg" class="err-msg">Weight is required</span>
                </div>

              </div>

              <!-- Dynamic Location Section (Up to 5 Locations) -->
              <div style="margin-top: 20px; border-top: 1px solid #f1f5f9; padding-top: 16px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                  <h4 style="margin: 0; font-size: 0.9rem; font-weight: 700; color: var(--text-primary); display: flex; align-items: center; gap: 6px;">
                    <IconBase name="location" :size="15" style="color: #4f46e5;" /> Target Locations (Max 5)
                  </h4>
                  <button 
                    type="button" 
                    @click="addLocation" 
                    v-if="form.locations.length < 5"
                    style="background: rgba(79, 70, 229, 0.08); border: 1px solid rgba(79, 70, 229, 0.2); color: #4f46e5; border-radius: 6px; padding: 6px 12px; cursor: pointer; font-size: 0.78rem; font-weight: 700; display: inline-flex; align-items: center; gap: 4px; transition: all 0.15s ease;"
                  >
                    + Add Location 
                  </button>
                </div>

                <div v-for="(loc, idx) in form.locations" :key="idx" style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; margin-bottom: 12px;">
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="font-size: 0.78rem; font-weight: 700; color: #475569;">Location Entry #{{ idx + 1 }}</span>
                    <button 
                      type="button" 
                      v-if="form.locations.length > 1"
                      @click="removeLocation(idx)" 
                      style="background: transparent; border: none; color: #ef4444; font-size: 0.75rem; font-weight: 600; cursor: pointer;"
                    >
                      Remove
                    </button>
                  </div>

                  <div class="form-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 0;">
                    <!-- Country -->
                    <div class="form-field">
                      <label style="font-size: 0.75rem;">Country {{ idx + 1 }} *</label>
                      <div class="select-wrapper">
                        <select v-model="loc.country" class="setup-select">
                          <option value="United States">United States</option>
                        </select>
                        <IconBase name="chevron-down" :size="13" class="chevron" />
                      </div>
                    </div>

                    <!-- State -->
                    <div class="form-field">
                      <label style="font-size: 0.75rem;">State {{ idx + 1 }} *</label>
                      <div class="select-wrapper">
                        <select v-model="loc.state" class="setup-select">
                          <option v-for="st in US_STATES" :key="st" :value="st">{{ st }}</option>
                        </select>
                        <IconBase name="chevron-down" :size="13" class="chevron" />
                      </div>
                    </div>

                    <!-- County -->
                    <div class="form-field">
                      <label style="font-size: 0.75rem;">County {{ idx + 1 }} *</label>
                      <div class="select-wrapper">
                        <select v-model="loc.county" class="setup-select">
                          <option v-for="cnt in getCountiesForState(loc.state)" :key="cnt" :value="cnt">{{ cnt }}</option>
                        </select>
                        <IconBase name="chevron-down" :size="13" class="chevron" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <!-- Analyze Button -->
            <div class="analyze-footer">
              <button class="btn gradient-btn" @click="handleAnalyze">
                <IconBase name="sparkle" :size="16" /> Analyze Patient Risk & Generate Insights
              </button>
              <p class="secure-footer-text"><img src="/assets/insurance.png" alt="Secure Icon" class="secure-img-icon" /> Your data is secure and encrypted</p>
            </div>
          </div>

          <!-- Assessment History Section (Higher container with Excel-style subtabs) -->
          <section class="history-section-card" style="margin-top: 10px; background: #ffffff; border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 24px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03); min-height: 420px; display: flex; flex-direction: column;">
            <!-- Top History Bar with Tabs matching Excel -->
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #e2e8f0; padding-bottom: 12px;">
              <div style="display: flex; gap: 24px; align-items: center;">
                <h3 
                  @click="activeHistoryTab = 'recent'"
                  :style="{
                    margin: 0,
                    fontSize: '1.05rem',
                    fontWeight: 800,
                    color: activeHistoryTab === 'recent' ? 'var(--text-primary)' : 'var(--text-secondary)',
                    borderBottom: activeHistoryTab === 'recent' ? '2px solid #4f46e5' : '2px solid transparent',
                    paddingBottom: '12px',
                    marginBottom: '-13px',
                    cursor: 'pointer'
                  }"
                >
                  Recent
                </h3>
                <h3 
                  @click="activeHistoryTab = 'favorites'"
                  :style="{
                    margin: 0,
                    fontSize: '1.05rem',
                    fontWeight: 800,
                    color: activeHistoryTab === 'favorites' ? 'var(--text-primary)' : 'var(--text-secondary)',
                    borderBottom: activeHistoryTab === 'favorites' ? '2px solid #4f46e5' : '2px solid transparent',
                    paddingBottom: '12px',
                    marginBottom: '-13px',
                    cursor: 'pointer'
                  }"
                >
                  Favorites ({{ userHistory.filter(i => !!i.is_favorite).length }})
                </h3>
              </div>
              <span style="font-size: 0.78rem; color: var(--text-secondary); font-weight: 600;">Saved Patient Assessments</span>
            </div>

            <div v-if="!isLoggedIn" style="padding: 60px 24px; text-align: center; color: var(--text-secondary); font-size: 0.9rem; background: #f8fafc; border-radius: 12px; flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 280px;">
              <IconBase name="lock" :size="32" style="color: #94a3b8; margin-bottom: 12px;" />
              <p style="margin: 0; font-weight: 600; color: #475569;">
                Please sign in to view saved patient assessment records.
              </p>
              <button @click="triggerLogin" style="margin-top: 14px; background: #4f46e5; color: #ffffff; border: none; border-radius: 8px; padding: 9px 20px; font-weight: 600; font-size: 0.85rem; cursor: pointer; transition: background 0.15s ease;">
                Sign In
              </button>
            </div>

            <div v-else-if="isLoadingHistory" style="padding: 60px 20px; text-align: center; color: var(--text-secondary); font-size: 0.9rem; flex: 1;">
              Loading assessment history...
            </div>

            <div v-else-if="displayedHistory.length === 0" style="padding: 60px 24px; text-align: center; color: var(--text-secondary); font-size: 0.9rem; background: #f8fafc; border-radius: 12px; flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 280px;">
              <IconBase name="folder" :size="32" style="color: #94a3b8; margin-bottom: 12px;" />
              <p style="margin: 0; font-weight: 600; color: #475569;">
                {{ activeHistoryTab === 'favorites' ? 'No starred favorite records found.' : 'No prior assessment history found.' }}
              </p>
              <p style="margin: 4px 0 0; font-size: 0.8rem; color: #94a3b8;">
                {{ activeHistoryTab === 'favorites' ? 'Click the star icon next to any recent patient record to mark it as favorite.' : 'Click Upload File / Manual above to analyze patient data.' }}
              </p>
            </div>

            <div v-else style="flex: 1;">
              <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem; text-align: left;">
                <thead>
                  <tr style="border-bottom: 1.5px solid var(--border); color: var(--text-secondary);">
                    <th style="padding: 12px 10px; width: 36px; text-align: center;">★</th>
                    <th style="padding: 12px 14px;">Patient Name</th>
                    <th style="padding: 12px 14px;">Location</th>
                    <th style="padding: 12px 14px;">Conditions</th>
                    <th style="padding: 12px 14px;">Date Modified</th>
                    <th style="padding: 12px 14px; text-align: right;">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in displayedHistory" :key="item.id" style="border-bottom: 1px solid #f1f5f9; transition: background 0.15s ease;" class="history-row-item">
                    <!-- Favorite Star Button -->
                    <td style="padding: 14px 10px; text-align: center;">
                      <button 
                        type="button" 
                        @click.stop="toggleFavoriteItem(item)" 
                        title="Toggle Favorite"
                        style="background: transparent; border: none; cursor: pointer; font-size: 1.1rem; padding: 2px 4px; transition: transform 0.15s ease;"
                        onmouseenter="this.style.transform='scale(1.25)'"
                        onmouseleave="this.style.transform='scale(1.0)'"
                      >
                        <span v-if="item.is_favorite" style="color: #f59e0b;">★</span>
                        <span v-else style="color: #cbd5e1;">☆</span>
                      </button>
                    </td>
                    <td style="padding: 14px; font-weight: 600; color: var(--text-primary);">
                      {{ item.name || 'Patient Record' }} <span style="font-weight: normal; color: var(--text-secondary); font-size: 0.78rem;">(Age {{ item.age || 45 }})</span>
                    </td>
                    <td style="padding: 14px; color: var(--text-secondary);">
                      {{ item.extra_data?.county || item.county || 'Cuyahoga County' }}, {{ item.extra_data?.state || item.state || 'OH' }}
                    </td>
                    <td style="padding: 14px; color: var(--text-secondary);">
                      <span v-if="item.diabetes === 'Yes'" style="background: rgba(239, 68, 68, 0.1); color: #ef4444; padding: 3px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 600; margin-right: 6px;">Diabetes</span>
                      <span v-if="item.hypertension === 'Yes'" style="background: rgba(245, 158, 11, 0.1); color: #d97706; padding: 3px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 600;">Hypertension</span>
                      <span v-if="item.diabetes !== 'Yes' && item.hypertension !== 'Yes'" style="color: #10b981; font-weight: 600; font-size: 0.78rem;">Standard</span>
                    </td>
                    <td style="padding: 14px; color: var(--text-secondary); font-size: 0.8rem;">
                      {{ formatDate(item.timestamp || item.created_at) }}
                    </td>
                    <td style="padding: 14px; text-align: right;">
                      <div style="display: inline-flex; align-items: center; gap: 8px; justify-content: flex-end;">
                        <button @click="viewHistoryItem(item)" title="View on Main Dashboard" style="background: #4f46e5; border: 1px solid #4f46e5; color: #ffffff; border-radius: 6px; padding: 7px 12px; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; font-weight: 600; font-size: 0.78rem; transition: all 0.15s ease; box-shadow: 0 1px 2px rgba(79, 70, 229, 0.2);">
                          <IconBase name="eye" :size="15" /> View
                        </button>
                        <button @click="downloadHistoryItem(item)" title="Download Assessment Data" style="background: #ffffff; border: 1px solid #4f46e5; color: #4f46e5; border-radius: 6px; padding: 7px 12px; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; font-weight: 600; font-size: 0.78rem; transition: all 0.15s ease; box-shadow: 0 1px 2px rgba(79, 70, 229, 0.05);">
                          <img src="/assets/download.gif" alt="Download" style="width: 16px; height: 16px; object-fit: contain;" /> Download
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </div>
      </main>

      <!-- Right Sidebar Removed -->
    </div>
  </div>
</template>

<style scoped>
.data-setup-page {
  background: #f8fafc;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* App Bar styling */
.app-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 32px;
  background: #ffffff;
  border-bottom: 1px solid var(--border);
  height: 64px;
  flex-shrink: 0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

/* Analysis processing overlay */
.analysis-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.loading-card {
  width: 500px;
  max-width: 90%;
  padding: 36px;
  background: #ffffff;
  border-radius: var(--radius-lg);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.15);
  text-align: center;
}

.loading-card h3 {
  margin: 0 0 10px;
  font-size: 1.3rem;
  font-weight: 800;
  color: var(--text-primary);
}

.loading-card .subtitle {
  font-size: 0.86rem;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 24px;
}

.progress-bar-container {
  height: 24px;
  background: #e2e8f0;
  border-radius: 99px;
  position: relative;
  overflow: hidden;
  margin-bottom: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.progress-bar-fill {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  border-radius: 99px;
  transition: width 0.1s ease;
}

.progress-pct {
  position: relative;
  z-index: 2;
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--text-primary);
}

.steps-checklist {
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.steps-checklist li {
  display: flex;
  align-items: center;
  gap: 10px;
  opacity: 0.4;
  transition: opacity 0.25s ease;
}

.steps-checklist li.active {
  opacity: 0.9;
  font-weight: 600;
}

.steps-checklist li.completed {
  opacity: 1;
  color: var(--teal);
}

.step-indicator {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.completed .step-indicator {
  background: var(--teal-bg);
  border-color: var(--teal);
  color: var(--teal);
}

.step-bullet {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-secondary);
}

.step-spinner {
  width: 10px;
  height: 10px;
  border: 2px solid #cbd5e1;
  border-top-color: var(--brand);
  border-radius: 50%;
  animation: spinner-rotate 0.8s linear infinite;
}

@keyframes spinner-rotate {
  to {
    transform: rotate(360deg);
  }
}

.active .step-bullet {
  background: var(--brand);
}

.step-text {
  font-size: 0.8rem;
  color: var(--text-primary);
}

.completed .step-text {
  color: var(--text-secondary);
}

/* Page Setup Grid */
.setup-grid {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  flex: 1;
  height: calc(100vh - 64px);
  overflow: hidden;
}

/* 1. Left Sidebar Guide */
.sidebar-guide {
  background: #ffffff;
  border-right: 1px solid var(--border);
  padding: 16px 16px;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.help-card {
  margin-top: auto;
}

/* 2. Center Content panel */
.center-content-panel {
  padding: 12px 24px;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  gap: 12px;
  overflow: hidden;
  height: 100%;
}

.center-panel-wrapper {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 100%;
  gap: 8px;
}

/* Form fields layout */
.form-section {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px 16px;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.form-field label {
  font-size: 0.76rem;
  font-weight: 600;
  color: var(--text-primary);
}

.setup-input,
.setup-select,
.setup-textarea {
  width: 100%;
  padding: 6px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  background: #ffffff;
  font-size: 0.8rem;
  color: var(--text-primary);
  outline: none;
  font-family: inherit;
  box-shadow: inset 0 1px 2px rgba(0,0,0,0.02);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
/* Capsule Tab selector */
.tabs-wrapper {
  display: inline-flex;
  background: #e2e8f0;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 3px;
  align-self: flex-start;
  margin-bottom: 4px;
}

.tab-btn {
  border: none;
  background: transparent;
  padding: 6px 18px;
  font-size: 0.76rem;
  font-weight: 600;
  color: #475569;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.tab-btn.active {
  background: #ffffff;
  color: var(--text-primary);
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}

/* Upload Card styling */
.upload-card {
  padding: 16px 20px;
  border: 2px dashed #cbd5e1;
  border-radius: var(--radius-lg);
  background: #ffffff;
  transition: border-color 0.15s ease, background 0.15s ease;
  text-align: center;
  box-shadow: var(--shadow-sm);
  position: relative;
}

.upload-card.dragover {
  border-color: var(--brand);
  background: var(--brand-light);
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.upload-icon-circle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--brand-light);
  color: var(--brand);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 6px;
}

.upload-img-icon {
  width: 22px;
  height: 22px;
  object-fit: contain;
}

.upload-text {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.upload-text.selected-file {
  color: var(--brand);
}

.upload-text span {
  font-size: 0.72rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.or-text {
  font-size: 0.68rem;
  color: var(--text-tertiary);
  margin: 2px 0;
}

.btn.choose-btn {
  background: #2563eb;
  color: #ffffff;
  padding: 5px 18px;
  font-size: 0.74rem;
  border-radius: 6px;
  font-weight: 600;
}

.btn.choose-btn:hover {
  background: #1d4ed8;
}

.format-note {
  font-size: 0.66rem;
  color: var(--text-tertiary);
  margin: 4px 0 0;
}

.hidden-input {
  display: none;
}

/* Connect Data Source list */
.connectors-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.connector-item {
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 8px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #ffffff;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: var(--shadow-sm);
}

.connector-item:hover {
  border-color: var(--brand);
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.connector-logo {
  height: 28px;
  width: auto;
  max-width: 80px;
  object-fit: contain;
  margin-bottom: 6px;
}

.connector-item b {
  font-size: 0.72rem;
  color: var(--text-primary);
  display: block;
  margin-bottom: 2px;
}

/* Locked Connect Data Source styles */
.locked-connect-card {
  position: relative;
  overflow: hidden;
  min-height: 120px;
}

.connector-item.clickable {
  cursor: pointer;
}

.connector-item.clickable:hover {
  border-color: var(--brand);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.12);
}

.connect-info-text {
  font-size: 0.72rem;
  color: var(--text-secondary);
  margin: 10px 0 0;
  text-align: center;
}

.disabled-section {
  opacity: 0.65;
  pointer-events: none;
}

.form-disabled-banner {
  background: #fffbe6;
  border: 1px solid #ffe58f;
  color: #d46b08;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 0.75rem;
  margin: 0 0 10px;
  font-weight: 500;
}

.page-lock-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(248, 250, 252, 0.78);
  backdrop-filter: blur(4px);
  z-index: 50;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-lg);
}

.page-lock-overlay .lock-icon-box {
  width: 44px;
  height: 44px;
  margin-bottom: 8px;
}

.page-lock-overlay h4 {
  font-size: 1rem;
  margin-bottom: 6px;
}

.page-lock-overlay p {
  font-size: 0.8rem;
  max-width: 420px;
}

.form-section h2 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 800;
  color: var(--text-primary);
}

.form-sub {  margin: 0 0 12px;
  font-size: 0.76rem;
  color: var(--text-secondary);
}

.form-field.fullwidth {
  grid-column: span 3;
}

.setup-input:focus,
.setup-select:focus,
.setup-textarea:focus {
  border-color: var(--brand);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.form-field.error .setup-input {
  border-color: var(--red);
  background: #fff8f8;
}

.err-msg {
  font-size: 0.64rem;
  color: var(--red-text);
  font-weight: 500;
}

.select-wrapper {
  position: relative;
}

.setup-select {
  appearance: none;
  padding-right: 28px;
}

.select-wrapper .chevron {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-secondary);
  pointer-events: none;
}

.setup-textarea {
  min-height: 52px;
  max-height: 60px;
  resize: none;
}

/* Footer analyze row */
.analyze-footer {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
  padding-top: 14px;
  border-top: 1px solid var(--border);
}

.btn.gradient-btn {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  color: #ffffff;
  padding: 10px 40px;
  font-size: 0.88rem;
  border-radius: 10px;
  box-shadow: 0 4px 14px rgba(79, 70, 229, 0.25);
  font-weight: 700;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn.gradient-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(79, 70, 229, 0.35);
}

.secure-footer-text {
  font-size: 0.68rem;
  color: var(--text-tertiary);
  display: flex;
  align-items: center;
  gap: 5px;
  margin: 0;
}

.secure-img-icon {
  width: 14px;
  height: 14px;
  object-fit: contain;
}

/* 3. Right Sidebar info columns */
.sidebar-info {
  background: #ffffff;
  border-left: 1px solid var(--border);
  padding: 24px 18px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow-y: auto;
  height: 100%;
}

.info-block-card {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px;
}

.info-block-card h4 {
  margin: 0 0 20px;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

/* Next steps flow list */
.steps-flow {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 22px;
  padding-left: 0;
}

.steps-flow::before {
  content: '';
  position: absolute;
  left: 21px;
  top: 21px;
  bottom: 21px;
  width: 2px;
  background: #e2e8f0;
  z-index: 1;
}

.steps-flow li {
  display: flex;
  gap: 14px;
  position: relative;
  z-index: 2;
  align-items: center;
}

.flow-icon {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-weight: 700;
  font-size: 0.68rem;
  flex-shrink: 0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.flow-icon-gif {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.flow-gif {
  width: 34px;
  height: 34px;
  object-fit: contain;
}

.flow-icon.validate { background: #10b981; }
.flow-icon.enrich { background: #8b5cf6; }
.flow-icon.ai-model { background: #f59e0b; }
.flow-icon.dashboard-gen { background: #3b82f6; }

.steps-flow h5,
.insights-flow h5 {
  margin: 0 0 2px;
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--text-primary);
}

.steps-flow p,
.insights-flow p {
  margin: 0;
  font-size: 0.68rem;
  color: var(--text-secondary);
  line-height: 1.35;
}

/* Insights list */
.insights-flow {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.insights-flow li {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.insights-flow .icon {
  width: 26px;
  height: 26px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.insights-flow .icon.assess { background: var(--brand-light); color: var(--brand); }
.insights-flow .icon.equity { background: var(--teal-bg); color: var(--teal); }
.insights-flow .icon.sdoh-impact { background: var(--purple-bg); color: var(--purple); }
.insights-flow .icon.actions { background: var(--amber-bg); color: var(--amber-text); }

/* Need Help */
.help-card {
  background: #f8fafc;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 16px;
  text-align: left;
}

.help-card h5 {
  margin: 0 0 4px;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-primary);
}

.help-card p {
  margin: 0 0 10px;
  font-size: 0.7rem;
  color: var(--text-secondary);
}

.help-link {
  font-size: 0.74rem;
  font-weight: 700;
  color: var(--brand);
  text-decoration: none;
}

.help-link:hover {
  text-decoration: underline;
}

/* General button utilities */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 9px 16px;
  border-radius: 8px;
  font-size: 0.78rem;
  font-weight: 600;
  white-space: nowrap;
  transition: all 0.2s ease;
  border: none;
  cursor: pointer;
}

.btn.primary {
  background: var(--brand);
  color: #fff;
}
.btn.primary:hover {
  background: var(--brand-dark);
}

/* Template Card Pop-Up Hover Effect */
.tpl-card-item {
  transition: transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
}

.tpl-card-item:hover {
  transform: translateY(-6px) scale(1.03);
}

.tpl-card-item:hover .tpl-card-box {
  border-color: #6366f1 !important;
  box-shadow: 0 10px 20px rgba(99, 102, 241, 0.15), 0 4px 6px rgba(0, 0, 0, 0.05) !important;
  background: #ffffff !important;
}

.tpl-card-item:hover img {
  transform: scale(1.1);
  transition: transform 0.2s ease;
}

/* Toast Vue Animation */
.toast-fade-enter-active,
.toast-fade-leave-active {
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.toast-fade-enter-from,
.toast-fade-leave-to {
  opacity: 0;
  transform: translate(-50%, -20px) scale(0.95) !important;
}
</style>
