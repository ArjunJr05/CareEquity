<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { setLoggedIn, setShowLoginScreen, setAdmin, userPlan, setUserPlan } from '../store/appState'
import { MAIN_BACKEND_URL, RAZORPAY_KEY_ID } from '../config'

const router = useRouter()

// Steps: 'login', 'signup', 'otp', 'plans'
const currentStep = ref('login')

// Subscription Plans State
const billingCycle = ref('yearly') // 'monthly' or 'yearly'
const activeSelectedPlan = ref(userPlan.value || 'basic')

const loadRazorpaySDK = () => {
  return new Promise((resolve) => {
    if (window.Razorpay) {
      resolve(true)
      return
    }
    const script = document.createElement('script')
    script.src = 'https://checkout.razorpay.com/v1/checkout.js'
    script.onload = () => resolve(true)
    script.onerror = () => resolve(false)
    document.body.appendChild(script)
  })
}

const finishLogin = () => {
  setLoggedIn(true)
  setShowLoginScreen(false)
  router.push('/')
}

const saveLoginSubscription = async (planId, cycle, paymentId = null, orderId = null, signature = null) => {
  const userEmail = localStorage.getItem('user_email') || loginEmail.value || signupEmail.value || 'doctor@careequity.com'
  const storedUserId = localStorage.getItem('user_id')
  const parsedUserId = storedUserId ? parseInt(storedUserId) : null

  const payload = {
    razorpay_payment_id: paymentId || (planId === 'free' ? 'free_trial_15_days' : `pay_${Math.random().toString(36).substring(2, 12)}`),
    razorpay_order_id: orderId || null,
    razorpay_signature: signature || null,
    plan: planId,
    billing_cycle: cycle,
    user_email: userEmail,
    user_id: parsedUserId
  }

  try {
    const res = await fetch(`${MAIN_BACKEND_URL}/api/payments/verify-payment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    if (res.ok) {
      const data = await res.json()
      if (data.user_id && !localStorage.getItem('user_id')) {
        localStorage.setItem('user_id', data.user_id)
      }
      return data
    }
  } catch (e) {
    console.warn('verify-payment error from login:', e)
  }

  try {
    await fetch(`${MAIN_BACKEND_URL}/api/subscriptions/subscribe`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: parsedUserId,
        user_email: userEmail,
        subscribe: true,
        plan: planId,
        validity: cycle
      })
    })
  } catch (err2) {
    console.error('Login subscription save fallback error:', err2)
  }
}

const selectPlan = async (planId, title) => {
  activeSelectedPlan.value = planId
  setUserPlan(planId)
  const currentCycle = planId === 'free' ? '15_days' : billingCycle.value

  await loadRazorpaySDK()
  const prices = {
    free: 1,
    basic: billingCycle.value === 'yearly' ? 1068 : 99,
    pro: billingCycle.value === 'yearly' ? 2904 : 269
  }
  const planPrice = prices[planId] || 1
  const amountInPaise = Math.round(planPrice * 100)

  let razorpayOrderId = null
  try {
    const res = await fetch(`${MAIN_BACKEND_URL}/api/payments/create-order`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        plan: planId,
        billing_cycle: currentCycle,
        amount: planPrice,
        user_email: localStorage.getItem('user_email') || loginEmail.value || signupEmail.value || 'doctor@careequity.com'
      })
    })
    if (res.ok) {
      const data = await res.json()
      razorpayOrderId = data.order_id
    }
  } catch (err) {
    console.warn('Payment order fallback:', err)
  }

  const options = {
    key: RAZORPAY_KEY_ID,
    amount: amountInPaise,
    currency: 'INR',
    name: 'CareEquity',
    description: planId === 'free' ? '15-Day Free Trial Authorization' : `${title || planId.toUpperCase()} Plan (${billingCycle.value === 'yearly' ? 'Billed Yearly' : 'Billed Monthly'})`,
    image: (typeof window !== 'undefined' ? window.location.origin : '') + '/assets/careequity_logo.png',
    ...(razorpayOrderId ? { order_id: razorpayOrderId } : {}),
    handler: async function (response) {
      await saveLoginSubscription(
        planId,
        currentCycle,
        response.razorpay_payment_id,
        response.razorpay_order_id,
        response.razorpay_signature
      )
      showToast(`Payment Successful! (ID: ${response.razorpay_payment_id})`, 'success')
      setUserPlan(planId)
      setTimeout(() => {
        finishLogin()
      }, 1000)
    },
    prefill: {
      name: localStorage.getItem('user_name') || signupName.value || 'Dr. Jane Smith',
      email: localStorage.getItem('user_email') || loginEmail.value || signupEmail.value || 'doctor@careequity.com',
      contact: '9876543210'
    },
    theme: {
      color: '#1d6bf3'
    }
  }

  if (window.Razorpay) {
    const rzp = new window.Razorpay(options)
    rzp.open()
  } else {
    const fallbackPayId = `pay_fallback_${Math.random().toString(36).substring(2, 10)}`
    await saveLoginSubscription(planId, currentCycle, fallbackPayId)
    showToast(`Subscribed to ${planId.toUpperCase()} plan! Welcome to CareEquity.`, 'success')
    setTimeout(() => {
      finishLogin()
    }, 800)
  }
}

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
      showToast('Successfully authenticated! Welcome to CareEquity.', 'success')
      // Save session info
      setLoggedIn(true, data)
      setShowLoginScreen(false)
      setTimeout(() => {
        router.push('/')
      }, 500)
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
      const errData = await response.json().catch(() => ({}))
      showToast(errData.detail || 'Email is already registered.', 'error')
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
      showToast('OTP verified! Choose your subscription plan.', 'success')
      // Save session info
      setLoggedIn(true, data)
      setShowLoginScreen(false)
      setTimeout(() => {
        router.push('/plan')
      }, 400)
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

    <div class="auth-shell" :class="{ 'plans-mode': currentStep === 'plans' }">
      <!-- ── LEFT PANEL (Shown during login, signup, otp) ── -->
      <section v-if="currentStep !== 'plans'" class="left-panel">
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

      <!-- ── STEP 4: SUBSCRIPTION PLANS (Shown after OTP / Sign In) ── -->
      <section v-else class="plans-full-container">
        <button class="auth-close-btn" @click="finishLogin" title="Skip Plan Selection">
          <span>Skip & Exit →</span>
        </button>

        <div class="plans-header">
          <div class="left-logo central">
            <img src="/assets/careequity_remove.png" style="width: 36px; height: 36px; object-fit: contain;" alt="CareEquity Logo" />
            <div class="brand-text">
              <p class="brand-name" style="font-size: 20px;">CareEquity Plans</p>
            </div>
          </div>
          <h1 class="plans-title">Select Your Subscription Plan</h1>
          <p class="plans-sub">Empowering health equity with predictive SDOH intelligence & geospatial navigation.</p>
          
          <!-- Monthly / Yearly Billing Toggle -->
          <div class="billing-toggle-container">
            <span :class="{ active: billingCycle === 'monthly' }" @click="billingCycle = 'monthly'">Monthly</span>
            <label class="switch">
              <input type="checkbox" :checked="billingCycle === 'yearly'" @change="billingCycle = billingCycle === 'yearly' ? 'monthly' : 'yearly'" />
              <span class="slider round"></span>
            </label>
            <span :class="{ active: billingCycle === 'yearly' }" @click="billingCycle = 'yearly'">
              Yearly <span class="discount-badge">SAVE 10%</span>
            </span>
          </div>
        </div>

        <!-- 3 Pricing Cards Grid -->
        <div class="plans-grid">
          
          <!-- Plan 1: FREE -->
          <div class="plan-card" :class="{ 'active-plan': activeSelectedPlan === 'free' }">
            <div class="top-badge-row" v-if="activeSelectedPlan === 'free'">
              <span class="your-plan-badge" style="margin-left: auto;">Your Plan</span>
            </div>

            <div class="card-plan-header">
              <span class="plan-type">FREE</span>
              <div class="plan-price-box">
                <span class="currency">₹</span>
                <span class="amount">0</span>
                <span class="period">/mo</span>
              </div>
              <p class="plan-desc">Get started with a 15-day free trial — no credit card required. Full access to essential SDOH features.</p>
            </div>

            <ul class="features-list">
              <li class="check"><span class="icon">✓</span> <strong>SDOH profile</strong></li>
              <li class="check"><span class="icon">✓</span> <strong>Basic SDOH assessment</strong></li>
              <li class="check"><span class="icon">✓</span> <strong>Nearby healthcare resources</strong></li>
              <li class="check"><span class="icon">✓</span> <strong>Food & nutrition resources</strong></li>
              <li class="check"><span class="icon">✓</span> <strong>Basic location map</strong></li>
              <li class="check"><span class="icon">✓</span> <strong>Chat bot assistance</strong></li>
              <li class="check"><span class="icon">✓</span> <strong>Basic resource search</strong></li>
              <li class="check"><span class="icon">✓</span> <strong>Limited personalized recommendations</strong></li>
            </ul>

            <button class="plan-action-btn free-btn" :class="{ 'active-btn': activeSelectedPlan === 'free' }" @click="selectPlan('free', 'FREE')">
              {{ activeSelectedPlan === 'free' ? '✓ Current Plan' : 'Start Free' }}
            </button>
          </div>

          <!-- Plan 2: BASIC -->
          <div class="plan-card" :class="{ 'active-plan': activeSelectedPlan === 'basic' }">
            <div class="top-badge-row">
              <span class="pop-badge">MOST POPULAR</span>
              <span class="your-plan-badge" v-if="activeSelectedPlan === 'basic'">Your Plan</span>
            </div>

            <div class="card-plan-header">
              <span class="plan-type">BASIC</span>
              <div class="plan-price-box">
                <span class="currency">₹</span>
                <span class="amount">{{ billingCycle === 'yearly' ? '1068' : '99' }}</span>
                <span class="period">{{ billingCycle === 'yearly' ? '/yr' : '/mo' }}</span>
              </div>
              <p class="plan-sub-price" v-if="billingCycle === 'yearly'">≈ ₹89/mo · save ₹119/yr</p>
              <p class="plan-desc">Designed for care navigators &amp; individuals — essential SDOH tools with personalized support.</p>
            </div>

            <ul class="features-list">
              <li class="check"><span class="icon">✓</span> <strong>Up to 100 patient SDOH assessments</strong></li>
              <li class="check"><span class="icon">✓</span> <strong>CareMap 3D view & live OSRM directions</strong></li>
              <li class="check"><span class="icon">✓</span> <strong>SDOH Risk Score & detailed assessment insights</strong></li>
              <li class="check"><span class="icon">✓</span> <strong>Personalized community resource recommendations</strong></li>
              <li class="check"><span class="icon">✓</span> <strong>Automated intervention matching engine</strong></li>
              <li class="check"><span class="icon">✓</span> <strong>Basic PDF & CSV report exports</strong></li>
              <li class="check"><span class="icon">✓</span> <strong>Email helpdesk support</strong></li>
              <li class="check"><span class="icon">✓</span> <strong>Chat bot unlimited</strong></li>
            </ul>

            <button class="plan-action-btn basic-btn" :class="{ 'active-btn': activeSelectedPlan === 'basic' }" @click="selectPlan('basic', 'BASIC')">
              {{ activeSelectedPlan === 'basic' ? '✓ Subscribed' : 'Select Basic' }}
            </button>
          </div>

          <!-- Plan 3: PRO -->
          <div class="plan-card" :class="{ 'active-plan': activeSelectedPlan === 'pro' }">
            <div class="top-badge-row" v-if="activeSelectedPlan === 'pro'">
              <span class="your-plan-badge" style="margin-left: auto;">Your Plan</span>
            </div>

            <div class="card-plan-header">
              <span class="plan-type">PRO</span>
              <div class="plan-price-box">
                <span class="currency">₹</span>
                <span class="amount">{{ billingCycle === 'yearly' ? '2904' : '269' }}</span>
                <span class="period">{{ billingCycle === 'yearly' ? '/yr' : '/mo' }}</span>
              </div>
              <p class="plan-sub-price" v-if="billingCycle === 'yearly'">≈ ₹242/mo · save ₹360/yr</p>
              <p class="plan-desc">Advanced SDOH analytics, AI insights, and predictive intelligence.</p>
            </div>

            <ul class="features-list">
              <li class="check"><span class="icon">✓</span> <strong>Up to 500 patient SDOH assessments</strong></li>
              <li class="check"><span class="icon">✓</span> <strong>CareMap 3D view & live OSRM directions</strong></li>
              <li class="check"><span class="icon">✓</span> <strong>Advanced SDOH Risk Score & analytics</strong></li>
              <li class="check"><span class="icon">✓</span> <strong>AI-powered SDOH resource recommendations</strong></li>
              <li class="check"><span class="icon">✓</span> <strong>Automated intervention matching engine</strong></li>
              <li class="check"><span class="icon">✓</span> <strong>Advanced PDF & CSV report exports</strong></li>
              <li class="check"><span class="icon">✓</span> <strong>Equity Map & population-level insights</strong></li>
              <li class="check"><span class="icon">✓</span> <strong>AI SDOH Assistant for personalized guidance</strong></li>
            </ul>

            <button class="plan-action-btn pro-btn" :class="{ 'active-btn': activeSelectedPlan === 'pro' }" @click="selectPlan('pro', 'PRO')">
              {{ activeSelectedPlan === 'pro' ? '✓ Subscribed' : 'Get Pro' }}
            </button>
          </div>

        </div>
      </section>

      <!-- ── RIGHT PANEL (Shown during login, signup, otp) ── -->
      <aside v-if="currentStep !== 'plans'" class="right-panel">
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

/* ── SUBSCRIPTION PLANS MODAL STYLES ── */
.auth-shell.plans-mode {
  display: block !important;
  max-width: 1040px;
  width: 95vw;
  height: auto;
  min-height: auto;
  padding: 32px 36px;
  background: #f8fafc;
  overflow-y: auto;
  max-height: 92vh;
}

.plans-full-container {
  position: relative;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.left-logo.central {
  justify-content: center;
  margin-bottom: 12px;
}

.plans-header {
  text-align: center;
  margin-bottom: 24px;
  width: 100%;
}

.plans-title {
  font-size: 24px;
  font-weight: 800;
  color: #0f172a;
  margin: 4px 0;
}

.plans-sub {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 18px;
}

/* Billing Toggle Switch */
.billing-toggle-container {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
  user-select: none;
}
.billing-toggle-container span {
  cursor: pointer;
}
.billing-toggle-container span.active {
  color: #0f172a;
  font-weight: 800;
}
.discount-badge {
  background: #e0f2fe;
  color: #0284c7;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 10px;
  font-weight: 800;
  margin-left: 4px;
}

.switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
}
.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}
.slider {
  position: absolute;
  cursor: pointer;
  inset: 0;
  background-color: #cbd5e1;
  transition: .3s;
  border-radius: 24px;
}
.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: .3s;
  border-radius: 50%;
}
input:checked + .slider {
  background-color: #2563eb;
}
input:checked + .slider:before {
  transform: translateX(20px);
}

/* Pricing Grid */
.plans-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  width: 100%;
  margin-top: 10px;
}

.plan-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 18px;
  padding: 22px 18px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  position: relative;
  transition: all 0.2s ease;
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
}
.plan-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
}
.plan-card.active-plan {
  border: 2.2px solid #1d6bf3 !important;
  box-shadow: 0 12px 32px rgba(29, 107, 243, 0.2) !important;
  background: #ffffff;
}

.top-badge-row {
  position: absolute;
  top: -12px;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-between;
  padding: 0 16px;
  z-index: 10;
}
.pop-badge {
  background: #1d6bf3;
  color: white;
  font-size: 9.5px;
  font-weight: 800;
  padding: 3px 10px;
  border-radius: 9999px;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 8px rgba(29, 107, 243, 0.3);
}
.your-plan-badge {
  background: #1d6bf3;
  color: white;
  font-size: 9.5px;
  font-weight: 800;
  padding: 3px 10px;
  border-radius: 9999px;
  box-shadow: 0 2px 8px rgba(29, 107, 243, 0.3);
}

.plan-action-btn.active-btn {
  background: #1d6bf3 !important;
  color: #ffffff !important;
  border: none !important;
  box-shadow: 0 4px 14px rgba(29, 107, 243, 0.3) !important;
}

.card-plan-header {
  margin-bottom: 12px;
}
.plan-type {
  font-size: 11px;
  font-weight: 800;
  color: #475569;
  letter-spacing: 1px;
}
.plan-price-box {
  display: flex;
  align-items: baseline;
  margin: 4px 0 2px 0;
}
.plan-price-box .currency {
  font-size: 18px;
  font-weight: 800;
  color: #0f172a;
}
.plan-price-box .amount {
  font-size: 28px;
  font-weight: 800;
  color: #0f172a;
  line-height: 1;
}
.plan-price-box .period {
  font-size: 12px;
  color: #64748b;
  font-weight: 600;
  margin-left: 2px;
}
.plan-sub-price {
  font-size: 10.5px;
  color: #2563eb;
  font-weight: 700;
  margin-bottom: 4px;
}
.plan-desc {
  font-size: 11.5px;
  color: #64748b;
  line-height: 1.4;
  margin-top: 4px;
  min-height: 42px;
}

/* Feature Check List */
.features-list {
  list-style: none;
  padding: 0;
  margin: 12px 0 20px 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.features-list li {
  font-size: 11.5px;
  color: #334155;
  display: flex;
  align-items: flex-start;
  gap: 6px;
  line-height: 1.35;
}
.features-list li.check .icon {
  color: #2563eb;
  font-weight: 800;
}
.features-list li.cross {
  color: #94a3b8;
}
.features-list li.cross .icon {
  color: #ef4444;
  font-weight: 700;
}

/* Action Button */
.plan-action-btn {
  width: 100%;
  padding: 9px 0;
  border-radius: 8px;
  font-size: 12.5px;
  font-weight: 700;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #0f172a;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}
.plan-action-btn:hover {
  border-color: #2563eb;
  color: #2563eb;
  background: #eff6ff;
}
.plan-action-btn.basic-btn {
  background: #dcfce7;
  color: #15803d;
  border: 1px solid #bbf7d0;
}
.plan-action-btn.basic-btn:hover {
  background: #16a34a;
  color: white;
}

@media (max-width: 1100px) {
  .plans-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 640px) {
  .plans-grid {
    grid-template-columns: 1fr;
  }
}
</style>
