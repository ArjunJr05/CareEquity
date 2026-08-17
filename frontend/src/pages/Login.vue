<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { setLoggedIn, setShowLoginScreen, setAdmin } from '../store/appState'
import { MAIN_BACKEND_URL } from '../config'

const router = useRouter()

// Steps: 'login', 'signup', 'otp'
const currentStep = ref('login')

// Form Inputs
const loginEmail = ref('')
const loginPassword = ref('')

const signupName = ref('')
const signupEmail = ref('')
const signupPassword = ref('')
const signupConfirmPassword = ref('')

const otpInput = ref('')

const isSubmitting = ref(false)

// OTP Resend Timer
const resendSecs = ref(55)
let resendTimer = null

// Toast State
const toast = ref({
  show: false,
  msg: '',
  type: 'error', // 'success' or 'error'
  title: 'Oops!'
})
let toastTimer = null

// Filter non-digits for OTP
const onOTPInput = (e) => {
  otpInput.value = e.target.value.replace(/\D/g, '')
}

// Toast utility
const showToast = (msg, type = 'error') => {
  toast.value.show = true
  toast.value.msg = msg
  toast.value.type = type
  toast.value.title = type === 'success' ? 'Success!' : 'Oops!'

  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    toast.value.show = false
  }, 3500)
}

const hideToast = () => {
  toast.value.show = false
}

// Switch between login and signup
const goToSignUp = () => {
  currentStep.value = 'signup'
}

const goToLogin = () => {
  currentStep.value = 'login'
}

// Handle Sign In Submission
const handleSignIn = async () => {
  if (!loginEmail.value.trim() || !loginEmail.value.includes('@')) {
    showToast('Enter a valid email address', 'error')
    return
  }
  if (!loginPassword.value.trim()) {
    showToast('Enter your password', 'error')
    return
  }

  // Check for inbuilt admin user
  if (loginEmail.value.trim() === 'contact.careequity@gmail.com' && loginPassword.value === 'arjund') {
    isSubmitting.value = true
    setTimeout(() => {
      showToast('Successfully authenticated as Admin!', 'success')
      localStorage.setItem('docpat_logged_in', 'true')
      localStorage.setItem('user_email', 'contact.careequity@gmail.com')
      localStorage.setItem('user_name', 'Admin User')
      setLoggedIn(true)
      setAdmin(true)
      setShowLoginScreen(false)
      isSubmitting.value = false
      router.push('/admin')
    }, 500)
    return
  }

  isSubmitting.value = true
  try {
    const response = await fetch(`${MAIN_BACKEND_URL}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: loginEmail.value,
        password: loginPassword.value
      })
    })

    if (!response.ok) {
      const errData = await response.json()
      showToast(errData.detail || 'Failed to authenticate.', 'error')
    } else {
      const data = await response.json()
      showToast('Successfully authenticated!', 'success')
      // Save session info
      localStorage.setItem('docpat_logged_in', 'true')
      localStorage.setItem('user_email', data.email)
      localStorage.setItem('user_name', data.name)
      setTimeout(() => {
        setLoggedIn(true)
        setShowLoginScreen(false)
      }, 1000)
    }
  } catch (error) {
    showToast('Could not connect to authentication server.', 'error')
    console.error('Login error:', error)
  } finally {
    isSubmitting.value = false
  }
}

// Handle Sign Up Submission
const handleSignUp = async () => {
  if (!signupName.value.trim()) {
    showToast('Enter your full name', 'error')
    return
  }
  if (!signupEmail.value.trim() || !signupEmail.value.includes('@')) {
    showToast('Enter a valid email address', 'error')
    return
  }
  if (signupPassword.value.length < 6) {
    showToast('Password must be at least 6 characters', 'error')
    return
  }
  if (signupPassword.value !== signupConfirmPassword.value) {
    showToast('Passwords do not match', 'error')
    return
  }

  isSubmitting.value = true
  try {
    const response = await fetch(`${MAIN_BACKEND_URL}/api/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: signupName.value,
        email: signupEmail.value,
        password: signupPassword.value
      })
    })

    if (!response.ok) {
      const errData = await response.json()
      showToast(errData.detail || 'Registration failed.', 'error')
    } else {
      showToast('Verification OTP sent to ' + signupEmail.value, 'success')
      // Switch to OTP page
      currentStep.value = 'otp'
      startResendTimer()
    }
  } catch (error) {
    showToast('Could not connect to authentication server.', 'error')
    console.error('Registration error:', error)
  } finally {
    isSubmitting.value = false
  }
}

// Verify OTP Action
const handleVerifyOTP = async () => {
  if (otpInput.value.length < 6) {
    showToast('Enter the 6-digit OTP code', 'error')
    return
  }

  isSubmitting.value = true
  try {
    const response = await fetch(`${MAIN_BACKEND_URL}/api/auth/verify-otp`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: signupEmail.value || loginEmail.value,
        otp: otpInput.value
      })
    })

    if (!response.ok) {
      const errData = await response.json()
      showToast(errData.detail || 'OTP verification failed.', 'error')
    } else {
      const data = await response.json()
      showToast('Successfully registered and authenticated!', 'success')
      // Save session info
      localStorage.setItem('docpat_logged_in', 'true')
      localStorage.setItem('user_email', data.email)
      localStorage.setItem('user_name', data.name)
      setTimeout(() => {
        setLoggedIn(true)
        setShowLoginScreen(false)
      }, 1000)
    }
  } catch (error) {
    showToast('Could not connect to authentication server.', 'error')
    console.error('OTP verify error:', error)
  } finally {
    isSubmitting.value = false
  }
}

// Resend OTP Action
const handleResend = () => {
  if (resendSecs.value > 0) return
  handleSignUp()
}

const startResendTimer = () => {
  if (resendTimer) clearInterval(resendTimer)
  resendSecs.value = 55
  resendTimer = setInterval(() => {
    resendSecs.value--
    if (resendSecs.value <= 0) {
      clearInterval(resendTimer)
      resendTimer = null
    }
  }, 1000)
}

const backToForm = () => {
  if (resendTimer) clearInterval(resendTimer)
  otpInput.value = ''
  currentStep.value = 'signup'
}

const handleCancelLogin = () => {
  setShowLoginScreen(false)
}

// Carousel State
const currentSlide = ref(0)
const totalSlides = 3
let carouselInterval = null

onMounted(() => {
  // Rotate slide every 5 seconds
  carouselInterval = setInterval(() => {
    currentSlide.value = (currentSlide.value + 1) % totalSlides
  }, 5000)
})

onUnmounted(() => {
  if (resendTimer) clearInterval(resendTimer)
  if (carouselInterval) clearInterval(carouselInterval)
  if (toastTimer) clearTimeout(toastTimer)
})
</script>

<template>
  <div class="login-page-body">
    <!-- Toast -->
    <div class="toast" :class="[toast.type, { show: toast.show }]">
      <div class="toast-icon">{{ toast.type === 'success' ? '✓' : '✕' }}</div>
      <div>
        <div class="toast-title">{{ toast.title }}</div>
        <div class="toast-msg">{{ toast.msg }}</div>
      </div>
      <button class="toast-close" @click="hideToast">×</button>
      <div class="toast-bar"></div>
    </div>

    <div class="auth-shell">
      <!-- ── LEFT PANEL ── -->
      <section class="left-panel">
        <!-- Close / Back Button -->
        <button class="auth-close-btn" @click="handleCancelLogin" title="Go Back">
          <span>← Back</span>
        </button>

        <div class="left-logo">
          <img src="/assets/careequity_logo.png" style="width: 32px; height: 32px; object-fit: contain;" alt="CareEquity Logo" />
          <div class="brand-text">
            <p class="brand-name">CareEquity</p>
            <p class="brand-sub">Healthier Communities. Equitable Futures.</p>
          </div>
        </div>

        <!-- STEP 1: Login -->
        <div class="step" :class="{ active: currentStep === 'login' }">
          <h1 class="form-title">Welcome back.</h1>
          <p class="form-sub">Sign in to continue building healthier, more equitable communities.</p>

          <div class="input-group">
            <input 
              type="email" 
              v-model="loginEmail"
              placeholder="Email address"
              class="form-input"
              autocomplete="email" 
            />
          </div>

          <div class="input-group">
            <input 
              type="password" 
              v-model="loginPassword"
              placeholder="Password"
              class="form-input"
              autocomplete="current-password" 
              @keydown.enter="handleSignIn"
            />
          </div>

          <button 
            class="primary-btn" 
            :disabled="isSubmitting" 
            @click="handleSignIn"
          >
            {{ isSubmitting ? 'Signing in...' : 'Sign In' }}
          </button>

          <div class="empty-divider"></div>

          <p class="switch-mode-text">
            Don't have an account? 
            <span class="link-btn" @click="goToSignUp">Sign up</span>
          </p>
        </div>

        <!-- STEP 2: SignUp -->
        <div class="step" :class="{ active: currentStep === 'signup' }">
          <h1 class="form-title" style="font-size: 24px; margin-bottom: 4px;">Create Account</h1>
          <p class="form-sub" style="margin-bottom: 12px; font-size: 13px;">Join us in building healthier, more equitable communities.</p>

          <div class="input-group mini">
            <input 
              type="text" 
              v-model="signupName"
              placeholder="Full name"
              class="form-input"
              autocomplete="name" 
            />
          </div>

          <div class="input-group mini">
            <input 
              type="email" 
              v-model="signupEmail"
              placeholder="Email address"
              class="form-input"
              autocomplete="email" 
            />
          </div>

          <div class="input-group mini">
            <input 
              type="password" 
              v-model="signupPassword"
              placeholder="Password (min 6 chars)"
              class="form-input"
              autocomplete="new-password" 
            />
            <p style="font-size: 11px; color: #64748b; margin-top: 2px; margin-bottom: 0; text-align: left; padding-left: 2px;">Password must be at least 6 characters.</p>
          </div>

          <div class="input-group mini">
            <input 
              type="password" 
              v-model="signupConfirmPassword"
              placeholder="Confirm password"
              class="form-input"
              autocomplete="new-password" 
              @keydown.enter="handleSignUp"
            />
          </div>

          <button 
            class="primary-btn" 
            :disabled="isSubmitting" 
            @click="handleSignUp"
            style="height: 40px; font-size: 14px;"
          >
            {{ isSubmitting ? 'Signing up...' : 'Sign Up' }}
          </button>

          <div class="empty-divider"></div>

          <p class="switch-mode-text" style="margin-top: 14px;">
            Already have an account? 
            <span class="link-btn" @click="goToLogin">Sign in</span>
          </p>
        </div>

        <!-- STEP 3: OTP Verification -->
        <div class="step" :class="{ active: currentStep === 'otp' }">
          <div class="back-row">
            <button class="back-btn" @click="backToForm" aria-label="Back">←</button>
            <h1 class="form-title" style="font-size:26px; margin-bottom: 0;">Verify OTP</h1>
          </div>
          <p class="form-sub" style="margin-bottom: 12px;">
            A 6-digit verification code has been sent.
          </p>

          <div class="id-chip">
            <span>{{ loginEmail || signupEmail }}</span>
            <button @click="backToForm">Change</button>
          </div>

          <input 
            type="text" 
            class="otp-input" 
            :value="otpInput"
            @input="onOTPInput"
            maxlength="6" 
            placeholder="• • • • • •"
            autocomplete="one-time-code" 
            @keydown.enter="handleVerifyOTP"
          />

          <button 
            class="resend-btn" 
            :disabled="resendSecs > 0" 
            @click="handleResend"
          >
            {{ resendSecs > 0 ? `Resend in ${resendSecs}s` : 'Resend OTP' }}
          </button>

          <button 
            class="primary-btn" 
            :disabled="isSubmitting" 
            @click="handleVerifyOTP"
          >
            {{ isSubmitting ? 'Verifying...' : 'Verify & Continue' }}
          </button>
        </div>

        <div class="form-spacer"></div>
      </section>

      <!-- ── RIGHT PANEL ── -->
      <aside class="right-panel">
        <div class="carousel">
          <div class="carousel-viewport">
            <div 
              class="carousel-slide" 
              :class="{ active: currentSlide === 0 }"
              style="background-image: url('/assets/login_graphic.png');"
            ></div>
            <div 
              class="carousel-slide" 
              :class="{ active: currentSlide === 1 }"
              style="background-image: url('/assets/login_security.png');"
            ></div>
            <div 
              class="carousel-slide" 
              :class="{ active: currentSlide === 2 }"
              style="background-image: url('/assets/login_chatbot.png');"
            ></div>
          </div>
          <div class="carousel-dots">
            <div class="carousel-dot" :class="{ active: currentSlide === 0 }" @click="currentSlide = 0"></div>
            <div class="carousel-dot" :class="{ active: currentSlide === 1 }" @click="currentSlide = 1"></div>
            <div class="carousel-dot" :class="{ active: currentSlide === 2 }" @click="currentSlide = 2"></div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

.login-page-body {
  font-family: 'Inter', sans-serif;
  color: #0f172a;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  width: 100vw;
  position: fixed;
  inset: 0;
  z-index: 99999;
  background: #f0f9ff;
  background-image:
    linear-gradient(rgba(37, 99, 235, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(37, 99, 235, 0.04) 1px, transparent 1px);
  background-size: 72px 72px;
  overflow-y: auto;
  padding: 20px 16px;
}

/* ── TOAST ── */
.toast {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%) translateY(-120%);
  min-width: min(420px, calc(100vw - 32px));
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 12px;
  padding: 16px 18px;
  background: #fff;
  border: 1px solid rgba(37, 99, 235, 0.2);
  border-radius: 14px;
  box-shadow: 0 20px 40px rgba(37, 99, 235, 0.1);
  z-index: 100000;
  transition: transform .35s cubic-bezier(.2, .8, .2, 1);
  overflow: hidden;
}

.toast.show {
  transform: translateX(-50%) translateY(0);
}

.toast-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 800;
}

.toast.success .toast-icon {
  background: #dcfce7;
  color: #15803d;
}

.toast.error .toast-icon {
  background: #fee2e2;
  color: #b91c1c;
}

.toast-title {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
}

.toast-msg {
  font-size: 13px;
  color: #475569;
  margin-top: 2px;
  line-height: 1.4;
}

.toast-close {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 22px;
  color: #475569;
  line-height: 1;
}

.toast-bar {
  position: absolute;
  left: 0;
  bottom: 0;
  height: 3px;
  width: 100%;
  transform-origin: left;
}

.toast.success .toast-bar {
  background: #22c55e;
}

.toast.error .toast-bar {
  background: #ef4444;
}

/* ── COMPACT CONTAINER SHELL ── */
.auth-shell {
  width: min(980px, 100%);
  height: 600px;
  background: #fff;
  border: 1px solid rgba(37, 99, 235, 0.15);
  border-radius: 22px;
  overflow: hidden;
  display: grid;
  grid-template-columns: 1.08fr 0.92fr;
  box-shadow: 0 25px 60px rgba(37, 99, 235, 0.12);
  animation: shell-in .45s cubic-bezier(.2, .8, .2, 1) both;
}

@keyframes shell-in {
  from {
    opacity: 0;
    transform: translateY(14px) scale(.994);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

/* ── LEFT PANEL ── */
.left-panel {
  padding: 40px 48px;
  background: #fff;
  display: flex;
  flex-direction: column;
  justify-content: center;
  overflow-y: auto;
  height: 100%;
  position: relative;
}

.auth-close-btn {
  position: absolute;
  top: 24px;
  right: 24px;
  background: transparent;
  border: 1px solid #e2e8f0;
  color: #64748b;
  font-size: 0.78rem;
  font-weight: 600;
  padding: 6px 12px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: all 0.15s ease;
}

.auth-close-btn:hover {
  background: #f8fafc;
  color: #0f172a;
  border-color: #cbd5e1;
}

.left-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
}

.brand-text {
  text-align: left;
}

.brand-name {
  font-size: 1.15rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
  line-height: 1.2;
}

.brand-sub {
  font-size: 0.68rem;
  color: #64748b;
  margin: 1px 0 0;
}

.form-title {
  font-size: 28px;
  font-weight: 800;
  color: #0f172a;
  margin-bottom: 6px;
  text-align: left;
  letter-spacing: -0.02em;
}

.form-sub {
  font-size: 13.5px;
  color: #64748b;
  margin-bottom: 18px;
  line-height: 1.45;
  text-align: left;
}

/* Steps */
.step {
  display: none;
}

.step.active {
  display: block;
  animation: step-in .3s ease both;
}

@keyframes step-in {
  from {
    opacity: 0;
    transform: translateX(12px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

/* Input group */
.input-group {
  margin-bottom: 14px;
}

.input-group.mini {
  margin-bottom: 10px;
}

.form-input {
  width: 100%;
  height: 46px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #fff;
  padding: 0 14px;
  font-size: 14px;
  color: #0f172a;
  outline: none;
  transition: border-color .2s, box-shadow .2s;
}

.form-input:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.input-group.mini .form-input {
  height: 40px;
  font-size: 13.5px;
}

/* OTP Input */
.otp-input {
  width: 100%;
  height: 52px;
  border: 1.5px solid #cbd5e1;
  border-radius: 8px;
  background: #fff;
  color: #0f172a;
  font-size: 24px;
  letter-spacing: 10px;
  text-align: center;
  outline: none;
  transition: border-color .2s, box-shadow .2s;
  margin-bottom: 16px;
}

.otp-input:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

/* Buttons */
.primary-btn {
  width: 100%;
  height: 46px;
  border: none;
  border-radius: 8px;
  background-image: linear-gradient(135deg, #3b82f6, #1d4ed8);
  color: #fff;
  font-size: 14.5px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity .2s, transform .2s, box-shadow .2s;
  box-shadow: 0 4px 14px rgba(37, 99, 235, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
}

.primary-btn:hover:not(:disabled) {
  opacity: .95;
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(37, 99, 235, 0.3);
}

.primary-btn:disabled {
  opacity: .6;
  cursor: not-allowed;
}

/* Resend Button */
.resend-btn {
  display: block;
  width: 100%;
  text-align: right;
  background: none;
  border: none;
  color: #2563eb;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  margin-bottom: 12px;
}

.resend-btn:disabled {
  color: #94a3b8;
  cursor: not-allowed;
}

/* Back Row */
.back-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.back-btn {
  width: 32px;
  height: 32px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
  color: #475569;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: border-color .2s, background .2s;
}

.back-btn:hover {
  border-color: #2563eb;
  color: #2563eb;
}

/* Identifier Chip */
.id-chip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 40px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0 12px;
  margin-bottom: 14px;
  background: #f8fafc;
  color: #334155;
  font-weight: 500;
  font-size: 13px;
}

.id-chip button {
  background: none;
  border: none;
  color: #2563eb;
  font-weight: 600;
  font-size: 12px;
  cursor: pointer;
}

/* Divider */
.empty-divider {
  border-bottom: 1px solid #e2e8f0;
  margin: 24px 0;
  width: 100%;
}

.switch-mode-text {
  font-size: 13px;
  color: #64748b;
  text-align: center;
  margin-top: 18px;
}

.link-btn {
  color: #2563eb;
  font-weight: 600;
  cursor: pointer;
  margin-left: 4px;
}

.link-btn:hover {
  text-decoration: underline;
}

.form-spacer {
  flex: 1;
}

/* ── RIGHT PANEL ── */
.right-panel {
  border-left: 1px solid rgba(37, 99, 235, 0.1);
  position: relative;
  overflow: hidden;
  height: 100%;
  width: 100%;
}

.carousel {
  position: absolute;
  inset: 0;
  z-index: 1;
}

.carousel-viewport {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.carousel-slide {
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity .8s ease-in-out;
  background-size: cover;
  background-position: center center;
  background-repeat: no-repeat;
}

.carousel-slide.active {
  opacity: 1;
}

.carousel-dots {
  position: absolute;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
  z-index: 10;
}

.carousel-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(37, 99, 235, 0.25);
  cursor: pointer;
  transition: all .3s ease;
}

.carousel-dot.active {
  width: 24px;
  border-radius: 100px;
  background: #2563eb;
}

/* ── RESPONSIVE ── */
@media (max-width: 900px) {
  .auth-shell {
    grid-template-columns: 1fr;
    height: auto;
    min-height: 500px;
    border-radius: 16px;
  }

  .right-panel {
    display: none;
  }

  .left-panel {
    padding: 32px 24px;
  }
}
</style>
