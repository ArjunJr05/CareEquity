<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import IconBase from '../components/dashboard/IconBase.vue'
import { setAnalyzed, setPatientData, setLocationRecords, isLoggedIn, setLoggedIn, setShowLoginScreen, setMlPredictionResults, setPredictionModelResults, setOcrExtractedJson, setMlInputPayload, setAgentReport, isAgentLoading, currentUserName, logoutUser, userPlan, syncUserSubscription } from '../store/appState'
import { MAIN_BACKEND_URL, SYSTEM_BACKEND_URL, PREDICTION_BACKEND_URL, OCR_BACKEND_URL, AGENT_BACKEND_URL } from '../config'

import { US_STATES, US_COUNTIES_BY_STATE } from '../data/usData.js'

const router = useRouter()

const userName = computed(() => {
  return currentUserName.value || localStorage.getItem('user_name') || 'Jane Smith'
})

const planBadgeText = computed(() => {
  if (!isLoggedIn.value || !userPlan.value) return 'Choose Plan'
  return `${userPlan.value.toUpperCase()} Plan`
})

const triggerLogin = () => {
  setShowLoginScreen(true)
}

const handleLogout = async () => {
  await logoutUser(MAIN_BACKEND_URL)
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
      ? `${MAIN_BACKEND_URL}/api/history/email/${encodeURIComponent(userEmail.trim().toLowerCase())}`
      : `${MAIN_BACKEND_URL}/api/history/user/${userId || 1}`
      
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
    syncUserSubscription(MAIN_BACKEND_URL)
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
  syncUserSubscription(MAIN_BACKEND_URL)
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
      height_cm: item.height_cm || item.extra_data?.height_cm || 170.0,
      weight_kg: item.weight_kg || item.extra_data?.weight_kg || 70.0,
      notes: item.notes || item.extra_data?.notes || '',
      county: item.county || item.extra_data?.county || 'Cuyahoga County',
      state: item.state || item.extra_data?.state || 'OH'
    })
    const historyLocations = item.extra_data?.all_locations || (item.extra_data?.locations_list ? item.extra_data.locations_list.map(l => ({ county: l[0], state: l[1], country: l[2] || 'United States' })) : [{ county: item.county || item.extra_data?.county || 'Cuyahoga County', state: item.state || item.extra_data?.state || 'Ohio', country: 'United States' }])
    setLocationRecords(historyLocations)
    if (item.extra_data?.ml_prediction || item.ml_prediction) {
      setMlPredictionResults(item.extra_data?.ml_prediction || item.ml_prediction)
    }
    if (item.extra_data?.prediction_model || item.prediction_model) {
      setPredictionModelResults(item.extra_data?.prediction_model || item.prediction_model)
    }
    if (item.extra_data?.ocr_extracted || item.ocr_extracted) {
      setOcrExtractedJson(item.extra_data?.ocr_extracted || item.ocr_extracted)
    }
    if (item.extra_data?.ml_input_payload || item.ml_input_payload) {
      setMlInputPayload(item.extra_data?.ml_input_payload || item.ml_input_payload)
    }
    if (item.extra_data?.agent_report || item.agent_report) {
      setAgentReport(item.extra_data?.agent_report || item.agent_report)
    }
  }
  setAnalyzed(true)
  router.push('/overview')
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
  title: '',
  message: '',
  type: 'success'
})
let toastTimer = null

const showToast = (title, message, type = 'success') => {
  if (toastTimer) clearTimeout(toastTimer)
  // Auto-detect error type if title contains error or missing
  const finalType = (type === 'error' || title.toLowerCase().includes('error') || title.toLowerCase().includes('missing') || title.toLowerCase().includes('oops')) ? 'error' : 'success'
  toast.value = { visible: true, title, message, type: finalType }
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

const defaultLocationPresets = [
  { country: 'United States', state: 'Alabama', county: 'Limestone County' },
  { country: 'United States', state: 'Georgia', county: 'Columbia County' },
  { country: 'United States', state: 'Mississippi', county: 'Hancock County' },
  { country: 'United States', state: 'North Carolina', county: 'Camden County' },
  { country: 'United States', state: 'Tennessee', county: 'Rutherford County' }
]

const form = ref({
  name: '',
  age: '',
  gender: 'Female',
  systolic_bp: '',
  diastolic_bp: '',
  hba1c: '',
  fasting_glucose: '',
  total_cholesterol: '',
  smoking_status: 'Never',
  locations: [
    { country: 'United States', state: '', county: '' }
  ],
  height_cm: '',
  weight_kg: '',
  notes: ''
})

const addLocation = () => {
  if (form.value.locations.length < 5) {
    form.value.locations.push({ country: 'United States', state: '', county: '' })
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

const onLocationStateChange = (loc) => {
  const counties = getCountiesForState(loc.state)
  if (counties && counties.length > 0) {
    if (!counties.includes(loc.county)) {
      loc.county = counties[0]
    }
  }
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

// Input sanitizers (prevent numbers in name, prevent negatives/decimals in age)
const onNameInput = (e) => {
  const cleaned = e.target.value.replace(/[0-9]/g, '')
  form.value.name = cleaned
  e.target.value = cleaned
  if (errors.value.name) errors.value.name = !cleaned.trim()
}

const onAgeInput = (e) => {
  let cleaned = e.target.value.replace(/\D/g, '')
  if (cleaned.length > 1 && cleaned.startsWith('0')) {
    cleaned = cleaned.replace(/^0+/, '')
  }
  if (parseInt(cleaned) > 125) {
    cleaned = '125'
  }
  form.value.age = cleaned
  e.target.value = cleaned
  if (errors.value.age) errors.value.age = !cleaned || parseInt(cleaned) <= 0
}

const onHeightInput = (e) => {
  let cleaned = e.target.value.replace(/[^0-9.]/g, '')
  form.value.height_cm = cleaned
  e.target.value = cleaned
  if (errors.value.height_cm) errors.value.height_cm = !cleaned || parseFloat(cleaned) <= 0
}

const onWeightInput = (e) => {
  let cleaned = e.target.value.replace(/[^0-9.]/g, '')
  form.value.weight_kg = cleaned
  e.target.value = cleaned
  if (errors.value.weight_kg) errors.value.weight_kg = !cleaned || parseFloat(cleaned) <= 0
}

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

const ocrRawJson = ref(null)
const ocrStatus = ref({ checking: false, healthy: null, message: '' })
const ocrExtractedFields = ref({
  name: false,
  age: false,
  gender: false,
  systolic_bp: false,
  diastolic_bp: false,
  hba1c: false,
  fasting_glucose: false,
  total_cholesterol: false,
  smoking_status: false,
  height_cm: false,
  weight_kg: false
})

const checkOcrBackendHealth = async () => {
  ocrStatus.value.checking = true
  ocrStatus.value.healthy = null
  ocrStatus.value.message = 'Testing OCR connection...'
  try {
    const res = await fetch(`${OCR_BACKEND_URL}/health`)
    if (res.ok) {
      const data = await res.json()
      ocrStatus.value.healthy = true
      ocrStatus.value.message = `OCR Backend Connected (${data.status || 'healthy'})`
      showToast('OCR Service Online', `OCR backend on ${OCR_BACKEND_URL} is connected and ready!`)
    } else {
      throw new Error(`HTTP ${res.status}`)
    }
  } catch (err) {
    ocrStatus.value.healthy = false
    ocrStatus.value.message = 'OCR Backend Offline'
    showToast('OCR Error', `Cannot connect to OCR backend on ${OCR_BACKEND_URL}. ${err.message}`)
  } finally {
    ocrStatus.value.checking = false
  }
}

const uploadFileToOCR = async (file) => {
  isUploadingFile.value = true
  // Reset extracted fields highlight & clear form
  ocrExtractedFields.value = {
    name: false,
    age: false,
    gender: false,
    systolic_bp: false,
    diastolic_bp: false,
    hba1c: false,
    fasting_glucose: false,
    total_cholesterol: false,
    smoking_status: false,
    height_cm: false,
    weight_kg: false
  }

  // Clear fields before OCR population so non-extracted fields stay blank
  form.value.name = ''
  form.value.age = ''
  form.value.systolic_bp = ''
  form.value.diastolic_bp = ''
  form.value.hba1c = ''
  form.value.fasting_glucose = ''
  form.value.total_cholesterol = ''
  form.value.height_cm = ''
  form.value.weight_kg = ''

  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('file_format', 'patient_details')
    
    let response = await fetch(`${OCR_BACKEND_URL}/extract?file_format=patient_details`, {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) {
      console.warn('Primary OCR backend returned non-OK (' + response.status + '), trying fallback system backend...')
      response = await fetch(`${SYSTEM_BACKEND_URL}/api/v1/ocr/upload`, {
        method: 'POST',
        body: formData
      })
    }
    
    if (!response.ok) {
      const errText = await response.text()
      throw new Error(`OCR upload failed (${response.status}): ${errText}`)
    }
    const result = await response.json()
    ocrRawJson.value = result
    setOcrExtractedJson(result)
    
    // Extract root dataset
    const ext = result.data || result.extracted_data || result
    
    // Target structured patient info object first
    const pInfo = ext.patient_info || ext.patient_details || ext.demographics || ext.patient || {}
    
    // 1. Patient Name (Target patient_info.patient_name, patient_info.name, or patient_info.full_name)
    let rawName = pInfo.patient_name || pInfo.name || pInfo.full_name
    
    // Fallback search only if not found in patient_info, ignoring schema metadata field names
    if (!rawName) {
      if (typeof ext.patient_name === 'string') rawName = ext.patient_name
      else if (typeof ext.name === 'string' && !ext.name.includes('.')) rawName = ext.name
    }
    
    if (rawName && typeof rawName === 'string' && rawName.trim().length > 0 && !rawName.includes('.')) {
      form.value.name = rawName.trim()
      ocrExtractedFields.value.name = true
    }

    // 2. Age (Target patient_info.age or patient_info.patient_age)
    let rawAge = pInfo.age !== undefined ? pInfo.age : pInfo.patient_age
    if (rawAge === undefined) rawAge = ext.age !== undefined ? ext.age : ext.patient_age

    if (rawAge !== null && rawAge !== undefined) {
      const parsedAge = parseInt(String(rawAge).replace(/[^0-9]/g, ''), 10)
      if (!isNaN(parsedAge) && parsedAge > 0 && parsedAge < 120) {
        form.value.age = parsedAge
        ocrExtractedFields.value.age = true
      }
    }

    // 3. Gender (Target patient_info.gender or patient_info.sex)
    let rawGender = pInfo.gender || pInfo.sex
    if (!rawGender) rawGender = ext.gender || ext.sex

    if (rawGender && typeof rawGender === 'string') {
      const g = rawGender.toLowerCase().trim()
      if (g.startsWith('f') || g.includes('female') || g.includes('woman')) {
        form.value.gender = 'Female'
        ocrExtractedFields.value.gender = true
      } else if (g.startsWith('m') || g.includes('male') || g.includes('man')) {
        form.value.gender = 'Male'
        ocrExtractedFields.value.gender = true
      } else {
        form.value.gender = 'Other'
        ocrExtractedFields.value.gender = true
      }
    }

    // Target vitals object
    const vitalsObj = ext.vital_signs || ext.vitals || {}

    // 4. Systolic BP & Diastolic BP
    const rawBP = vitalsObj.blood_pressure || ext.blood_pressure || ext.bp
    if (rawBP && typeof rawBP === 'string' && rawBP.includes('/')) {
      const parts = rawBP.split('/')
      const sys = parseInt(parts[0].replace(/[^0-9]/g, ''), 10)
      const dia = parseInt(parts[1].replace(/[^0-9]/g, ''), 10)
      if (!isNaN(sys) && sys > 40 && sys < 250) {
        form.value.systolic_bp = sys
        ocrExtractedFields.value.systolic_bp = true
      }
      if (!isNaN(dia) && dia > 30 && dia < 160) {
        form.value.diastolic_bp = dia
        ocrExtractedFields.value.diastolic_bp = true
      }
    }

    // 5. Height (cm)
    const rawHeight = vitalsObj.height || vitalsObj.height_cm || vitalsObj.stature
    if (rawHeight) {
      const parsedH = parseFloat(String(rawHeight).replace(/[^0-9.]/g, ''))
      if (!isNaN(parsedH) && parsedH > 0 && parsedH < 300) {
        form.value.height_cm = Math.round(parsedH)
        ocrExtractedFields.value.height_cm = true
      }
    }

    // 6. Weight (kg)
    const rawWeight = vitalsObj.weight || vitalsObj.weight_kg || vitalsObj.mass
    if (rawWeight) {
      const parsedW = parseFloat(String(rawWeight).replace(/[^0-9.]/g, ''))
      if (!isNaN(parsedW) && parsedW > 0 && parsedW < 500) {
        form.value.weight_kg = Math.round(parsedW)
        ocrExtractedFields.value.weight_kg = true
      }
    }

    // 7. Clinical Lab Numbers (HbA1c, Glucose, Cholesterol, Smoking)
    const jsonString = JSON.stringify(ext).toLowerCase()

    // HbA1c (%)
    const hba1cMatch = jsonString.match(/(?:hba1c|glycated|a1c)[^\d]*(\d+(?:\.\d+)?)/i)
    if (hba1cMatch && hba1cMatch[1]) {
      const val = parseFloat(hba1cMatch[1])
      if (!isNaN(val) && val >= 3 && val <= 18) {
        form.value.hba1c = val
        ocrExtractedFields.value.hba1c = true
      }
    }

    // Fasting Glucose (mg/dL)
    const glucoseMatch = jsonString.match(/(?:glucose|fasting_glucose|fpg)[^\d]*(\d+(?:\.\d+)?)/i)
    if (glucoseMatch && glucoseMatch[1]) {
      const val = parseFloat(glucoseMatch[1])
      if (!isNaN(val) && val >= 40 && val <= 500) {
        form.value.fasting_glucose = Math.round(val)
        ocrExtractedFields.value.fasting_glucose = true
      }
    }

    // Total Cholesterol (mg/dL)
    const cholMatch = jsonString.match(/(?:cholesterol|total_cholesterol)[^\d]*(\d+(?:\.\d+)?)/i)
    if (cholMatch && cholMatch[1]) {
      const val = parseFloat(cholMatch[1])
      if (!isNaN(val) && val >= 80 && val <= 600) {
        form.value.total_cholesterol = Math.round(val)
        ocrExtractedFields.value.total_cholesterol = true
      }
    }

    // Smoking Status
    if (jsonString.includes('former') || jsonString.includes('ex-smoker') || jsonString.includes('quit')) {
      form.value.smoking_status = 'Former'
      ocrExtractedFields.value.smoking_status = true
    } else if (jsonString.includes('current') || jsonString.includes('smoker')) {
      form.value.smoking_status = 'Current'
      ocrExtractedFields.value.smoking_status = true
    } else if (jsonString.includes('never') || jsonString.includes('non-smoker')) {
      form.value.smoking_status = 'Never'
      ocrExtractedFields.value.smoking_status = true
    }

    const countExtracted = Object.values(ocrExtractedFields.value).filter(Boolean).length
    if (countExtracted > 0) {
      showToast('OCR Complete', `Successfully extracted patient record! ${countExtracted} fields populated and highlighted in blue.`)
    } else {
      showToast('OCR Complete', 'Document processed! Raw OCR JSON is ready below. Please complete any blank fields.')
    }
    console.log('✓ Successfully processed OCR response:', result)
  } catch (err) {
    console.error('Failed uploading to OCR:', err)
    showToast('OCR Error', err.message || 'Failed extracting OCR data. Please fill out details manually.')
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
  const ageVal = parseInt(form.value.age)
  errors.value.name = !form.value.name || !form.value.name.trim() || /\d/.test(form.value.name)
  errors.value.age = !form.value.age || isNaN(ageVal) || ageVal <= 0
  errors.value.country = !form.value.country
  errors.value.state = !form.value.state
  errors.value.county = !form.value.county
  errors.value.height_cm = !form.value.height_cm || parseFloat(form.value.height_cm) <= 0
  errors.value.weight_kg = !form.value.weight_kg || parseFloat(form.value.weight_kg) <= 0

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
  const ageVal = parseInt(form.value.age)
  errors.value.name = !form.value.name || !form.value.name.trim() || /\d/.test(form.value.name)
  errors.value.age = !form.value.age || isNaN(ageVal) || ageVal <= 0
  errors.value.height_cm = !form.value.height_cm || parseFloat(form.value.height_cm) <= 0
  errors.value.weight_kg = !form.value.weight_kg || parseFloat(form.value.weight_kg) <= 0

  // Validate all location entries
  let hasLocationErrors = false
  form.value.locations.forEach((loc) => {
    loc.errors = {
      country: !loc.country,
      state: !loc.state,
      county: !loc.county
    }
    if (loc.errors.country || loc.errors.state || loc.errors.county) {
      hasLocationErrors = true
    }
  })

  const hasGeneralErrors = errors.value.name || errors.value.age || errors.value.height_cm || errors.value.weight_kg

  if (hasGeneralErrors || hasLocationErrors) {
    if (errors.value.name && /\d/.test(form.value.name)) {
      showToast('Invalid Name', 'Numbers are not allowed in the Name field.')
    } else if (errors.value.age && (isNaN(ageVal) || ageVal <= 0)) {
      showToast('Invalid Age', 'Please enter a valid positive age (greater than 0).')
    } else if (hasLocationErrors) {
      showToast('Incomplete Location', 'Please select Country, State, and County for all target location entries before analyzing.')
    } else {
      showToast('Missing Fields', 'Please fill in required patient demographics and height/weight.')
    }

    const firstErr = document.querySelector('.form-field.error')
    if (firstErr) firstErr.scrollIntoView({ behavior: 'smooth', block: 'center' })
    return
  }

  // Check for unpopulated/blank clinical lab fields
  const unpopulatedFields = []
  if (form.value.systolic_bp === '' || form.value.systolic_bp === null) unpopulatedFields.push('Systolic BP')
  if (form.value.diastolic_bp === '' || form.value.diastolic_bp === null) unpopulatedFields.push('Diastolic BP')
  if (form.value.hba1c === '' || form.value.hba1c === null) unpopulatedFields.push('HbA1c (%)')
  if (form.value.fasting_glucose === '' || form.value.fasting_glucose === null) unpopulatedFields.push('Fasting Glucose')
  if (form.value.total_cholesterol === '' || form.value.total_cholesterol === null) unpopulatedFields.push('Total Cholesterol')

  if (unpopulatedFields.length > 0) {
    const fieldNames = unpopulatedFields.join(', ')
    const confirmProceed = window.confirm(
      `The following field(s) are blank:\n• ${fieldNames}\n\nDo you want to consider them as "Don't Know (No)" and proceed with ML analysis?`
    )
    if (!confirmProceed) {
      showToast('Action Cancelled', 'Please enter the missing clinical values or upload a document.')
      return
    }
  }

  // Check for duplicate locations (Same Country + State + County cannot be added twice)
  const locKeys = form.value.locations.map(l => `${(l.country||'').trim().toLowerCase()}_${(l.state||'').trim().toLowerCase()}_${(l.county||'').trim().toLowerCase()}`)
  const seenKeys = new Set()
  let hasDuplicates = false

  locKeys.forEach((key, index) => {
    if (seenKeys.has(key)) {
      hasDuplicates = true
      const targetLoc = form.value.locations[index]
      if (!targetLoc.errors) targetLoc.errors = {}
      targetLoc.errors.county = true
      targetLoc.errors.isDuplicate = true
    } else {
      seenKeys.add(key)
    }
  })

  if (hasDuplicates) {
    showToast('Duplicate Location', 'Two target locations cannot be the same. Please select a different state or county.')
    const locSection = document.querySelector('.target-locations-card')
    if (locSection) locSection.scrollIntoView({ behavior: 'smooth', block: 'center' })
    return
  }

  // Transform locations into list of lists: [[county, state, country], [county, state, country], ...]
  const locationsListOfLists = form.value.locations.map(loc => [
    loc.county || '',
    loc.state || '',
    loc.country || ''
  ])

  // Save patient data in state including locations_list
  setPatientData({
    ...form.value,
    locations_list: locationsListOfLists
  })
  setLocationRecords(form.value.locations)

  // Start analysis animation sequence
  isAnalyzing.value = true
  analysisProgress.value = 0
  activeStep.value = 0

  let apisCompleted = false

  // Persist patient data to PostgreSQL backend database
  const savePatientPromise = (async () => {
    try {
      const primaryLoc = form.value.locations[0] || { country: 'United States', state: 'Kansas', county: 'Trego County' }
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
          notes: form.value.notes || '',
          county: primaryLoc.county,
          state: primaryLoc.state,
          country: primaryLoc.country,
          locations_list: locationsListOfLists
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
      const storedEmail = localStorage.getItem('user_email')
      const storedId = localStorage.getItem('user_id')
      const currentUserId = storedId ? parseInt(storedId) : null

      const historyPayload = {
        user_id: currentUserId,
        user_email: storedEmail,
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
          locations_list: locationsListOfLists,
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

      const sysVal = form.value.systolic_bp !== '' && form.value.systolic_bp !== null && form.value.systolic_bp !== undefined ? parseFloat(form.value.systolic_bp) : "No"
      const diaVal = form.value.diastolic_bp !== '' && form.value.diastolic_bp !== null && form.value.diastolic_bp !== undefined ? parseFloat(form.value.diastolic_bp) : "No"
      const hba1cVal = form.value.hba1c !== '' && form.value.hba1c !== null && form.value.hba1c !== undefined ? parseFloat(form.value.hba1c) : "No"
      const glucoseVal = form.value.fasting_glucose !== '' && form.value.fasting_glucose !== null && form.value.fasting_glucose !== undefined ? parseFloat(form.value.fasting_glucose) : "No"
      const cholVal = form.value.total_cholesterol !== '' && form.value.total_cholesterol !== null && form.value.total_cholesterol !== undefined ? parseFloat(form.value.total_cholesterol) : "No"

      const healthMetrics = {
        age: parseInt(form.value.age) || 45,
        height_cm: height || "No",
        weight_kg: weight || "No",
        bmi: isNaN(calculatedBmi) ? "No" : calculatedBmi,
        systolic_bp: sysVal,
        diastolic_bp: diaVal,
        blood_pressure: (sysVal !== "No" && diaVal !== "No") ? `${sysVal}/${diaVal}` : "No",
        hba1c: hba1cVal,
        fasting_glucose: glucoseVal,
        total_cholesterol: cholVal,
        total_cholesterol_mg_dl: cholVal,
        gender: form.value.gender || 'Female',
        sex: form.value.gender || 'Female',
        smoking_status: form.value.smoking_status || 'Never',
        smoking_history: form.value.smoking_status || 'Never'
      }

      const v2Payload = {
        patient_id: form.value.name ? `PATIENT_${form.value.name.replace(/\s+/g, '_').toUpperCase()}` : 'OCR_PATIENT_001',
        medical_data: healthMetrics,
        target_locations: locationsListOfLists,
        patient_data: {
          name: form.value.name,
          age: parseInt(form.value.age) || 45,
          gender: form.value.gender,
          diabetes: form.value.diabetes,
          hypertension: form.value.hypertension,
          heart_disease: form.value.heart_disease,
          asthma: form.value.asthma,
          height_cm: height,
          weight_kg: weight
        }
      }

      setMlInputPayload(v2Payload)

      // 1. Send directly to ML Service V2 Model (ml_pipelineV2.pkl)
      let data = null
      try {
        let v2Response = await fetch(`${MAIN_BACKEND_URL}/predict`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(v2Payload)
        })
        if (!v2Response.ok) {
          v2Response = await fetch(`http://localhost:8000/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(v2Payload)
          })
        }
        if (v2Response.ok) {
          data = await v2Response.json()
          console.log('✓ Received ML V2 (ml_pipelineV2.pkl) prediction:', data)
        }
      } catch (v2Err) {
        console.warn('ML V2 direct endpoint failed, trying fallback:', v2Err)
      }

      // 2. Fallback to system backend if needed
      if (!data) {
        const zipcode = '44102'
        const url = `${SYSTEM_BACKEND_URL}/api/v1/unified-predict?member_id=DEMO001&zipcode=${zipcode}`
        const response = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(healthMetrics)
        })
        if (!response.ok) throw new Error('ML Predict HTTP error: ' + response.status)
        data = await response.json()
      }

      // Ensure normalized structures exist on V2 response for all frontend components
      if (data && data.county_predictions && data.county_predictions.length > 0) {
        const primaryDiseases = data.county_predictions[0].diseases
        data.risk_scores = {
          diabetes: primaryDiseases?.diabetes?.probability ?? 0.25,
          hypertension: primaryDiseases?.hypertension?.probability ?? 0.32,
          heart_disease: primaryDiseases?.heart_disease?.probability ?? 0.15,
          asthma: primaryDiseases?.asthma?.probability ?? 0.10
        }
        data.risk_levels = {
          diabetes: primaryDiseases?.diabetes?.risk_tier ?? 'Low',
          hypertension: primaryDiseases?.hypertension?.risk_tier ?? 'Low',
          heart_disease: primaryDiseases?.heart_disease?.risk_tier ?? 'Low',
          asthma: primaryDiseases?.asthma?.risk_tier ?? 'Low'
        }
        const topSdohs = []
        Object.values(primaryDiseases || {}).forEach(d => {
          if (d.top_3_sdoh_factors) {
            d.top_3_sdoh_factors.forEach(sf => {
              const formattedName = sf.sdoh_factor.replace(/_/g, ' ')
              if (!topSdohs.includes(formattedName)) topSdohs.push(formattedName)
            })
          }
        })
        data.sdoh_barriers = topSdohs.length > 0 ? topSdohs.slice(0, 4) : [
          'Economic stability concerns',
          'Primary healthcare access barrier',
          'Transportation limitations'
        ]
      }

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

  // Trigger Research Assistant 4-Agent Pipeline backend call
  const agentBackendPromise = (async () => {
    try {
      isAgentLoading.value = true
      const primaryLoc = form.value.locations[0] || { county: 'Bronx County', state: 'NY' }
      const chronicList = []
      if (form.value.diabetes === 'Yes') chronicList.push('Type 2 Diabetes')
      if (form.value.hypertension === 'Yes') chronicList.push('Essential Hypertension')
      if (form.value.heart_disease === 'Yes') chronicList.push('Congestive Heart Failure')
      if (form.value.asthma === 'Yes') chronicList.push('Asthma')

      const agentPayload = {
        case_id: form.value.name ? `CASE_${form.value.name.replace(/\s+/g, '_').toUpperCase()}` : 'PATIENT_001',
        age: parseInt(form.value.age) || 45,
        geography: `${primaryLoc.county}, ${primaryLoc.state}`,
        risk_score: 75.0,
        risk_level: 'high',
        chronic_conditions: chronicList.length > 0 ? chronicList : ['Type 2 Diabetes'],
        transportation: true,
        food_access: true,
        economic_stability: true,
        housing: false,
        social_isolation: false
      }

      const res = await fetch(`${AGENT_BACKEND_URL}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(agentPayload)
      })

      if (res.ok) {
        const reportData = await res.json()
        setAgentReport(reportData)
        console.log('✓ Received 4-Agent Research Assistant synthesis report:', reportData)
      }
    } catch (agentErr) {
      console.warn('Agent Backend endpoint failed:', agentErr)
    } finally {
      isAgentLoading.value = false
    }
  })()


  // Trigger Prediction Model Risk Lookup
  const predictionModelPromise = (async () => {
    try {
      const latVal = form.value.lat !== undefined && form.value.lat !== null && form.value.lat !== '' ? form.value.lat : '41.4993'
      const lonVal = form.value.long !== undefined && form.value.long !== null && form.value.long !== '' ? form.value.long : '-81.6944'
      const predUrl = `${PREDICTION_BACKEND_URL}/api/v1/predict-by-coords?lat=${latVal}&lon=${lonVal}`
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

  // Execute all service fetches in parallel (ML, RAG/KG, Agent, Prediction Model, Database Save)
  Promise.allSettled([savePatientPromise, mlPredictionPromise, predictionModelPromise, agentBackendPromise]).then(async () => {
    console.log('🏁 All DataSetup pipeline service calls completed!')
    apisCompleted = true
    analysisProgress.value = 100
  })

  // Fallback safety timeout (ensure auto-completion even if external network delays occur)
  setTimeout(() => {
    apisCompleted = true
  }, 3500)

    if (isLoggedIn.value) {
      try {
        const primaryLoc = form.value.locations[0] || { country: 'United States', state: 'Kansas', county: 'Trego County' }
        const storedEmail = localStorage.getItem('user_email')
        const storedId = localStorage.getItem('user_id')
        const currentUserId = storedId ? parseInt(storedId) : null

        const historyPayload = {
          user_id: currentUserId,
          user_email: storedEmail,
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
            ocr_extracted: ocrExtractedJson.value,
            ml_input_payload: mlInputPayload.value,
            agent_report: agentReport.value,
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

  // Loading bar animation sequence
  const interval = setInterval(() => {
    analysisProgress.value += 3
    
    // Update steps based on progress
    if (analysisProgress.value < 20) activeStep.value = 0
    else if (analysisProgress.value < 40) activeStep.value = 1
    else if (analysisProgress.value < 65) activeStep.value = 2
    else if (analysisProgress.value < 85) activeStep.value = 3
    else activeStep.value = 4

    if (analysisProgress.value >= 100) {
      clearInterval(interval)
      analysisProgress.value = 100
      activeStep.value = 4
      // Done processing: Unlock dashboard and redirect to Overview page
      setAnalyzed(true)
      isAnalyzing.value = false
      router.push('/overview')
    }
  }, 50)
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
        <div class="custom-toast-box" 
             style="background: #ffffff; border-radius: 50px; box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1), 0 4px 10px rgba(0, 0, 0, 0.05); padding: 8px 16px 8px 10px; display: flex; align-items: center; gap: 10px; white-space: nowrap; max-width: 90vw; transition: all 0.2s ease;"
             :style="toast.type === 'error' ? { border: '1.5px solid #fee2e2', borderBottom: '3px solid #ef4444' } : { border: '1.5px solid #dcfce7', borderBottom: '3px solid #22c55e' }">
          
          <!-- Icon Circle (Green Checkmark for success, Red X for error) -->
          <div :style="toast.type === 'error' ? { background: '#fee2e2' } : { background: '#dcfce7' }" 
               style="width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
            
            <!-- Green Checkmark Icon -->
            <svg v-if="toast.type !== 'error'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            
            <!-- Red X Icon -->
            <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round">
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
      <div class="nav-right" style="display: flex; align-items: center; gap: 12px;">
        <!-- Subscription plan badge -->
        <button 
          class="chip chip-plan" 
          :class="{ 'chip-no-plan': !userPlan }"
          @click="router.push('/plan')" 
          :title="userPlan ? 'Current Subscription Plan' : 'Click to Choose a Plan'"
        >
          <IconBase name="sparkle" :size="15" class="sparkle-icon" />
          <span>{{ planBadgeText }}</span>
        </button>

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
          <div style="margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between;">
            <div>
              <h2 style="margin: 0; font-size: 1.25rem; font-weight: 800; color: var(--text-primary);">Select Data Source Template</h2>
              <p class="form-sub" style="margin: 4px 0 0; font-size: 0.78rem; color: var(--text-secondary);">Choose a source below to open the data entry form, or view your history below.</p>
            </div>

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
              <div v-if="isUploadingFile" class="upload-loading-overlay" style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(4px); z-index: 50; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 14px; border-radius: inherit;">
                <div class="ocr-spinner" style="width: 44px; height: 44px; border: 4px solid #e0e7ff; border-top-color: #4f46e5; border-radius: 50%; animation: spinner-rotate 0.75s linear infinite; box-shadow: 0 0 12px rgba(79, 70, 229, 0.2);"></div>
                <p style="font-weight: 700; color: #4338ca; margin: 0; font-size: 0.92rem; letter-spacing: 0.2px;">Extracting patient data with OCR AI...</p>
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
                <div class="form-field" :class="{ error: errors.name, 'ocr-extracted': ocrExtractedFields.name }">
                  <label>Name * </label>
                  <input 
                    type="text" 
                    :value="form.name" 
                    @input="onNameInput" 
                    placeholder="e.g., Robert Chen" 
                    class="setup-input" 
                    autocomplete="off"
                  />
                  <span v-if="errors.name" class="err-msg">Valid name without numbers is required</span>
                </div>

                <!-- Age -->
                <div class="form-field" :class="{ error: errors.age, 'ocr-extracted': ocrExtractedFields.age }">
                  <label>Age *</label>
                  <input 
                    type="number" 
                    min="1" 
                    max="125"
                    :value="form.age" 
                    @input="onAgeInput" 
                    placeholder="e.g., 54" 
                    class="setup-input no-spin" 
                  />
                  <span v-if="errors.age" class="err-msg">Valid positive age is required</span>
                </div>

                <!-- Gender -->
                <div class="form-field" :class="{ 'ocr-extracted': ocrExtractedFields.gender }">
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

                <!-- Systolic BP -->
                <div class="form-field" :class="{ 'ocr-extracted': ocrExtractedFields.systolic_bp }">
                  <label>Systolic BP (mmHg) *</label>
                  <input 
                    type="number" 
                    min="50" 
                    max="250"
                    v-model="form.systolic_bp" 
                    placeholder="e.g., 120" 
                    class="setup-input no-spin" 
                  />
                </div>

                <!-- Diastolic BP -->
                <div class="form-field" :class="{ 'ocr-extracted': ocrExtractedFields.diastolic_bp }">
                  <label>Diastolic BP (mmHg) *</label>
                  <input 
                    type="number" 
                    min="30" 
                    max="150"
                    v-model="form.diastolic_bp" 
                    placeholder="e.g., 80" 
                    class="setup-input no-spin" 
                  />
                </div>

                <!-- HbA1c (%) -->
                <div class="form-field" :class="{ 'ocr-extracted': ocrExtractedFields.hba1c }">
                  <label>HbA1c (%) *</label>
                  <input 
                    type="number" 
                    step="0.1"
                    min="3" 
                    max="15"
                    v-model="form.hba1c" 
                    placeholder="e.g., 5.7" 
                    class="setup-input no-spin" 
                  />
                </div>

                <!-- Fasting Glucose -->
                <div class="form-field" :class="{ 'ocr-extracted': ocrExtractedFields.fasting_glucose }">
                  <label>Fasting Glucose (mg/dL) *</label>
                  <input 
                    type="number" 
                    min="40" 
                    max="400"
                    v-model="form.fasting_glucose" 
                    placeholder="e.g., 100" 
                    class="setup-input no-spin" 
                  />
                </div>

                <!-- Total Cholesterol -->
                <div class="form-field" :class="{ 'ocr-extracted': ocrExtractedFields.total_cholesterol }">
                  <label>Total Cholesterol (mg/dL) *</label>
                  <input 
                    type="number" 
                    min="80" 
                    max="500"
                    v-model="form.total_cholesterol" 
                    placeholder="e.g., 190" 
                    class="setup-input no-spin" 
                  />
                </div>

                <!-- Smoking Status -->
                <div class="form-field" :class="{ 'ocr-extracted': ocrExtractedFields.smoking_status }">
                  <label>Smoking Status *</label>
                  <div class="select-wrapper">
                    <select v-model="form.smoking_status" class="setup-select">
                      <option value="Never">Never (Never Smoked)</option>
                      <option value="Former">Former (Used to Smoke / Quit)</option>
                      <option value="Current">Current (Currently Smokes)</option>
                    </select>
                    <IconBase name="chevron-down" :size="13" class="chevron" />
                  </div>
                </div>

                <!-- Height (cm) -->
                <div class="form-field" :class="{ error: errors.height_cm, 'ocr-extracted': ocrExtractedFields.height_cm }">
                  <label>Height (cm) *</label>
                  <input 
                    type="number" 
                    min="1" 
                    :value="form.height_cm" 
                    @input="onHeightInput" 
                    placeholder="e.g., 170" 
                    class="setup-input no-spin" 
                  />
                  <span v-if="errors.height_cm" class="err-msg">Valid height is required</span>
                </div>

                <!-- Weight (kg) -->
                <div class="form-field" :class="{ error: errors.weight_kg, 'ocr-extracted': ocrExtractedFields.weight_kg }">
                  <label>Weight (kg) *</label>
                  <input 
                    type="number" 
                    min="1" 
                    :value="form.weight_kg" 
                    @input="onWeightInput" 
                    placeholder="e.g., 70" 
                    class="setup-input no-spin" 
                  />
                  <span v-if="errors.weight_kg" class="err-msg">Valid weight is required</span>
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
                    <div class="form-field" :class="{ error: loc.errors?.country }">
                      <label style="font-size: 0.75rem;">Country {{ idx + 1 }} *</label>
                      <div class="select-wrapper">
                        <select v-model="loc.country" class="setup-select">
                          <option value="United States">United States</option>
                        </select>
                        <IconBase name="chevron-down" :size="13" class="chevron" />
                      </div>
                    </div>

                    <!-- State -->
                    <div class="form-field" :class="{ error: loc.errors?.state }">
                      <label style="font-size: 0.75rem;">State {{ idx + 1 }} *</label>
                      <div class="select-wrapper">
                        <select v-model="loc.state" @change="onLocationStateChange(loc); loc.errors && (loc.errors.state = !loc.state)" class="setup-select">
                          <option value="" disabled selected>Select One...</option>
                          <option v-for="st in US_STATES" :key="st" :value="st">{{ st }}</option>
                        </select>
                        <IconBase name="chevron-down" :size="13" class="chevron" />
                      </div>
                      <span v-if="loc.errors?.state" class="err-msg">Please select state</span>
                    </div>

                    <!-- County -->
                    <div class="form-field" :class="{ error: loc.errors?.county }">
                      <label style="font-size: 0.75rem;">County {{ idx + 1 }} *</label>
                      <div class="select-wrapper">
                        <select v-model="loc.county" @change="loc.errors && (loc.errors.county = !loc.county, loc.errors.isDuplicate = false)" class="setup-select" :disabled="!loc.state">
                          <option value="" disabled selected>{{ loc.state ? 'Select One...' : 'Select State First...' }}</option>
                          <option v-for="cnt in getCountiesForState(loc.state)" :key="cnt" :value="cnt">{{ cnt }}</option>
                        </select>
                        <IconBase name="chevron-down" :size="13" class="chevron" />
                      </div>
                      <span v-if="loc.errors?.county" class="err-msg">{{ loc.errors?.isDuplicate ? 'Duplicate location - select another county' : 'Please select county' }}</span>
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

/* Remove up/down increase/decrease spinner buttons */
input[type=number]::-webkit-inner-spin-button,
input[type=number]::-webkit-outer-spin-button,
.setup-input::-webkit-inner-spin-button,
.setup-input::-webkit-outer-spin-button,
.no-spin::-webkit-inner-spin-button,
.no-spin::-webkit-outer-spin-button {
  -webkit-appearance: none !important;
  margin: 0 !important;
}

input[type=number],
.setup-input[type=number],
.no-spin {
  -moz-appearance: textfield !important;
  appearance: textfield !important;
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

/* OCR AI Extracted Field Highlighting (Blue theme) */
.form-field.ocr-extracted .setup-input,
.form-field.ocr-extracted .setup-select {
  border-color: #3b82f6 !important;
  background-color: #eff6ff !important;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.18) !important;
  color: #1e3a8a !important;
  font-weight: 600 !important;
  transition: all 0.2s ease-in-out;
}

.form-field.ocr-extracted label {
  color: #1d4ed8 !important;
  font-weight: 700;
}

.ocr-tag {
  display: inline-block;
  margin-left: 6px;
  background: #3b82f6;
  color: #ffffff;
  font-size: 0.65rem;
  font-weight: 800;
  padding: 1px 6px;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
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

/* Subscription Plan Chip */
.chip {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 7px 14px;
  border: 1px solid var(--border);
  border-radius: 10px;
  font-size: 0.82rem;
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
  transition: all 0.2s ease;
}

.chip-plan {
  background: #eff6ff;
  border-color: #bfdbfe;
  color: #1d6bf3;
}

.chip-plan.chip-no-plan {
  background: #f8fafc;
  border: 1.5px dashed #3b82f6;
  color: #2563eb;
  font-weight: 700;
}

.chip-plan:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.12);
}

.chip-plan:hover .sparkle-icon,
.chip-plan:hover :deep(.sparkle-icon) {
  animation: iconSpin 3.5s linear infinite;
}

@keyframes iconSpin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
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
