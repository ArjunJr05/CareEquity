import { ref } from 'vue'

export const isLoggedIn = ref(localStorage.getItem('docpat_logged_in') === 'true')
export const isAnalyzed = ref(false)
export const showLoginScreen = ref(false)
export const isAdmin = ref(localStorage.getItem('user_role') === 'admin')
export const mlPredictionResults = ref(null)
export const predictionModelResults = ref(null)

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

export const userPlan = ref(localStorage.getItem('user_plan') || 'basic')

export function setLoggedIn(val) {
  isLoggedIn.value = val
  localStorage.setItem('docpat_logged_in', val ? 'true' : 'false')
  if (!val) {
    isAdmin.value = false
    localStorage.removeItem('user_role')
  }
}

export function setUserPlan(plan) {
  userPlan.value = plan
  localStorage.setItem('user_plan', plan)
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
