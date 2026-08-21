import { ref } from 'vue'

export const isLoggedIn = ref(localStorage.getItem('docpat_logged_in') === 'true')
export const isAnalyzed = ref(false)
export const showLoginScreen = ref(false)
export const isAdmin = ref(localStorage.getItem('user_role') === 'admin')
export const mlPredictionResults = ref(null)
export const predictionModelResults = ref(null)
export const ocrExtractedJson = ref(null)

export const patientData = ref({
  name: '',
  age: '',
  gender: 'Female',
  diabetes: 'No',
  hypertension: 'No',
  heart_disease: 'No',
  asthma: 'No',
  previous_admission: 'No',
  er_visits: 0,
  lat: 41.4993,
  long: -81.6944,
  medication_adherence: 85,
})

export const currentUserName = ref(localStorage.getItem('user_name') || '')
export const currentUserEmail = ref(localStorage.getItem('user_email') || '')
export const currentUserId = ref(localStorage.getItem('user_id') || '')

export const userPlan = ref(localStorage.getItem('user_plan') || null)

export function setLoggedIn(val, userData = null) {
  isLoggedIn.value = val
  localStorage.setItem('docpat_logged_in', val ? 'true' : 'false')
  if (val && userData) {
    if (userData.name) {
      currentUserName.value = userData.name
      localStorage.setItem('user_name', userData.name)
    }
    if (userData.email) {
      currentUserEmail.value = userData.email
      localStorage.setItem('user_email', userData.email)
    }
    if (userData.id) {
      currentUserId.value = String(userData.id)
      localStorage.setItem('user_id', String(userData.id))
    }
  } else if (!val) {
    isAdmin.value = false
    localStorage.removeItem('user_role')
  }
}

export async function logoutUser(backendUrl = 'http://localhost:8000') {
  const storedEmail = currentUserEmail.value || localStorage.getItem('user_email')
  try {
    if (storedEmail) {
      await fetch(`${backendUrl}/api/auth/logout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: storedEmail })
      })
    }
  } catch (err) {
    console.warn('Logout request note:', err)
  }

  // Clear all localStorage and reactive session references
  localStorage.removeItem('docpat_logged_in')
  localStorage.removeItem('user_email')
  localStorage.removeItem('user_name')
  localStorage.removeItem('user_id')
  localStorage.removeItem('user_plan')
  localStorage.removeItem('user_role')

  isLoggedIn.value = false
  isAdmin.value = false
  isAnalyzed.value = false
  userPlan.value = null
  currentUserName.value = ''
  currentUserEmail.value = ''
  currentUserId.value = ''
  mlPredictionResults.value = null
  predictionModelResults.value = null
  ocrExtractedJson.value = null
  patientData.value = {
    name: '',
    age: '',
    gender: 'Female',
    diabetes: 'No',
    hypertension: 'No',
    heart_disease: 'No',
    asthma: 'No',
    previous_admission: 'No',
    er_visits: 0,
    lat: 41.4993,
    long: -81.6944,
    medication_adherence: 85,
  }
}

export async function syncUserSubscription(backendUrl = 'http://localhost:8000') {
  const storedEmail = currentUserEmail.value || localStorage.getItem('user_email')
  const storedId = currentUserId.value || localStorage.getItem('user_id')
  if (!storedEmail && !storedId) {
    setUserPlan(null)
    return null
  }

  try {
    const params = new URLSearchParams()
    if (storedEmail) params.append('email', storedEmail.trim().toLowerCase())
    if (storedId) params.append('user_id', storedId)

    const res = await fetch(`${backendUrl}/api/subscriptions/latest?${params.toString()}`)
    if (res.ok) {
      const data = await res.json()
      if (data && data.plan && data.subscribe) {
        setUserPlan(data.plan.toLowerCase())
        return data.plan.toLowerCase()
      } else {
        setUserPlan(null)
        return null
      }
    }
  } catch (err) {
    console.warn('Subscription sync error:', err)
  }
  return null
}

export function setUserPlan(plan) {
  userPlan.value = plan
  if (plan) {
    localStorage.setItem('user_plan', plan)
  } else {
    localStorage.removeItem('user_plan')
  }
}

export function setAnalyzed(val) {
  isAnalyzed.value = val
}

export function setPatientData(data) {
  patientData.value = {
    previous_admission: 'No',
    er_visits: 0,
    medication_adherence: 85,
    ...data
  }
}

export function setShowLoginScreen(val) {
  showLoginScreen.value = val
}

export function setAdmin(val) {
  isAdmin.value = val
  if (val) {
    localStorage.setItem('user_role', 'admin')
  } else {
    localStorage.removeItem('user_role')
  }
}

export function setMlPredictionResults(val) {
  mlPredictionResults.value = val
}

export function setPredictionModelResults(val) {
  predictionModelResults.value = val
}

export function setOcrExtractedJson(val) {
  ocrExtractedJson.value = val
}
