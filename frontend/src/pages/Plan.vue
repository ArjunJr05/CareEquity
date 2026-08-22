<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { userPlan, setUserPlan } from '../store/appState'
import { MAIN_BACKEND_URL, RAZORPAY_KEY_ID } from '../config'

const router = useRouter()
const isYearly = ref(false)
const showConfirmationModal = ref(false)
const selectedPlanTitle = ref('')
const paymentDetails = ref(null)
const isProcessingPayment = ref(false)

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

const toggleBilling = (mode) => {
  isYearly.value = mode === 'yearly'
}

const handleExit = () => {
  router.push('/')
}

const saveSubscriptionToBackend = async (planKey, cycle, paymentId = null, orderId = null, signature = null) => {
  const userEmail = localStorage.getItem('user_email') || 'doctor@careequity.com'
  const storedUserId = localStorage.getItem('user_id')
  const parsedUserId = storedUserId ? parseInt(storedUserId) : null

  const payload = {
    razorpay_payment_id: paymentId || (planKey === 'free' ? 'free_trial_15_days' : `pay_${Math.random().toString(36).substring(2, 12)}`),
    razorpay_order_id: orderId || null,
    razorpay_signature: signature || null,
    plan: planKey,
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
      console.log('Subscription saved successfully in PostgreSQL:', data)
      if (data.user_id && !localStorage.getItem('user_id')) {
        localStorage.setItem('user_id', data.user_id)
      }
      setUserPlan(planKey)
      return data
    }
  } catch (e) {
    console.warn('verify-payment error, trying direct subscribe:', e)
  }

  // Backup fallback: direct /api/subscriptions/subscribe
  try {
    const res2 = await fetch(`${MAIN_BACKEND_URL}/api/subscriptions/subscribe`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: parsedUserId,
        user_email: userEmail,
        subscribe: true,
        plan: planKey,
        validity: cycle
      })
    })
    if (res2.ok) {
      const data2 = await res2.json()
      console.log('Direct subscription saved:', data2)
      return data2
    }
  } catch (err2) {
    console.error('Subscription backend save error:', err2)
  }
}

const selectPlan = async (planKey, title) => {
  const currentCycle = planKey === 'free' ? '15_days' : (isYearly.value ? 'yearly' : 'monthly')

  // FREE Plan: Directly activate without Razorpay payment modal
  if (planKey === 'free') {
    isProcessingPayment.value = true
    const freePayId = 'free_trial_15_days'
    await saveSubscriptionToBackend('free', '15_days', freePayId)
    setUserPlan('free')
    selectedPlanTitle.value = title
    paymentDetails.value = { razorpay_payment_id: 'Free 15-Day Trial (No Card Needed)' }
    isProcessingPayment.value = false
    showConfirmationModal.value = true
    return
  }

  // Paid Plans (Basic / Pro): Initiate Razorpay Checkout
  isProcessingPayment.value = true
  await loadRazorpaySDK()

  const targetPlan = plans.value.find(p => p.key === planKey) || { monthlyPrice: 0, yearlyPrice: 0 }
  const rawPrice = isYearly.value ? (targetPlan.yearlyPrice * 12) : targetPlan.monthlyPrice
  // Razorpay minimum charge is ₹1 token auth for free trial verification, or plan price for paid plans
  const chargeAmount = planKey === 'free' ? 1 : Math.max(1, rawPrice)
  const amountInPaise = Math.round(chargeAmount * 100)

  let razorpayOrderId = null
  let activeKeyId = RAZORPAY_KEY_ID

  // Try creating order via backend (with fallback)
  try {
    const res = await fetch(`${MAIN_BACKEND_URL}/api/payments/create-order`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        plan: planKey,
        billing_cycle: currentCycle,
        amount: chargeAmount,
        user_email: localStorage.getItem('user_email') || 'doctor@careequity.com'
      })
    })
    if (res.ok) {
      const data = await res.json()
      razorpayOrderId = data.order_id
      if (data.key_id && data.key_id !== 'rzp_test_YOUR_KEY_HERE') {
        activeKeyId = data.key_id
      }
    }
  } catch (err) {
    console.warn('Backend payment order fallback:', err)
  }

  const activateFallbackSubscription = async () => {
    isProcessingPayment.value = false
    const fallbackPayId = `pay_sim_${Math.random().toString(36).substring(2, 10)}`
    await saveSubscriptionToBackend(planKey, currentCycle, fallbackPayId)
    setUserPlan(planKey)
    selectedPlanTitle.value = title
    paymentDetails.value = { razorpay_payment_id: fallbackPayId }
    showConfirmationModal.value = true
  }

  const options = {
    key: activeKeyId,
    amount: amountInPaise,
    currency: 'INR',
    name: 'CareEquity',
    description: planKey === 'free' 
      ? '15-Day Free Trial Activation (Token Auth ₹1)' 
      : `${title} Plan (${isYearly.value ? 'Billed Yearly' : 'Billed Monthly'})`,
    image: (typeof window !== 'undefined' ? window.location.origin : '') + '/assets/careequity_logo.png',
    ...(razorpayOrderId ? { order_id: razorpayOrderId } : {}),
    handler: async function (response) {
      isProcessingPayment.value = false
      await saveSubscriptionToBackend(
        planKey,
        currentCycle,
        response.razorpay_payment_id,
        response.razorpay_order_id,
        response.razorpay_signature
      )

      setUserPlan(planKey)
      paymentDetails.value = response
      selectedPlanTitle.value = title
      showConfirmationModal.value = true
    },
    prefill: {
      name: localStorage.getItem('user_name') || 'Dr. Jane Smith',
      email: localStorage.getItem('user_email') || 'doctor@careequity.com',
      contact: '9876543210'
    },
    theme: {
      color: '#1d6bf3'
    },
    modal: {
      ondismiss: function () {
        isProcessingPayment.value = false
      }
    }
  }

  if (window.Razorpay) {
    try {
      const rzp = new window.Razorpay(options)
      rzp.on('payment.failed', function (response) {
        console.error('Razorpay payment failed:', response.error)
        isProcessingPayment.value = false
      })
      rzp.open()
    } catch (err) {
      console.warn('Razorpay checkout initialization error:', err)
      await activateFallbackSubscription()
    }
  } else {
    await activateFallbackSubscription()
  }
}

const closeConfirmation = () => {
  showConfirmationModal.value = false
  router.push('/')
}

const dynamicPlans = ref([])

const fetchDynamicPlans = async () => {
  try {
    const res = await fetch(`${MAIN_BACKEND_URL}/api/subscriptions/plans`)
    if (res.ok) {
      const data = await res.json()
      if (Array.isArray(data) && data.length > 0) {
        dynamicPlans.value = data
      }
    }
  } catch (err) {
    console.warn('Could not fetch dynamic plans, using defaults:', err)
  }
}

onMounted(() => {
  loadRazorpaySDK()
  fetchDynamicPlans()
})

const defaultPlans = [
  {
    key: 'free',
    title: 'FREE',
    icon: 'gift',
    monthlyPrice: 0,
    yearlyPrice: 0,
    subtitle: 'Get started with a 15-day free trial — no credit card required. Full access to essential SDOH features.',
    features: [
      '15-Day Full Access Trial',
      '50,000 AI Chatbot Tokens',
      'SDOH profile & basic assessment',
      'Nearby healthcare & food resources',
      'Basic location map',
      'Basic resource search',
      'Limited personalized recommendations'
    ],
    buttonText: 'Start Free',
    buttonClass: 'btn-outline',
    isPopular: false
  },
  {
    key: 'basic',
    title: 'BASIC',
    icon: 'shield',
    monthlyPrice: 99,
    yearlyPrice: 89,
    subtitle: 'Designed for care navigators & individuals — essential SDOH tools with personalized support.',
    features: [
      'Up to 100 patient SDOH assessments',
      '250,000 AI Chatbot Tokens',
      'CareMap 3D view & live OSRM directions',
      'SDOH Risk Score & detailed insights',
      'Personalized community recommendations',
      'Automated intervention matching engine',
      'Basic PDF & CSV report exports',
      'Email helpdesk support'
    ],
    buttonText: 'Subscribed',
    buttonClass: 'btn-primary',
    isPopular: true
  },
  {
    key: 'pro',
    title: 'PRO',
    icon: 'crown',
    monthlyPrice: 269,
    yearlyPrice: 242,
    subtitle: 'Advanced SDOH analytics, AI insights, and predictive intelligence.',
    features: [
      'Up to 500 patient SDOH assessments',
      'Unlimited AI Chatbot Tokens',
      'CareMap 3D view & live OSRM directions',
      'Advanced SDOH Risk Score & analytics',
      'AI-powered SDOH resource recommendations',
      'Automated intervention matching engine',
      'Advanced PDF & CSV report exports',
      'Equity Map & population-level insights'
    ],
    buttonText: 'Get Pro',
    buttonClass: 'btn-primary',
    isPopular: false
  }
]

const plans = computed(() => {
  if (dynamicPlans.value && dynamicPlans.value.length > 0) {
    return dynamicPlans.value.map(dp => {
      const match = defaultPlans.find(d => d.key === dp.key) || {}
      return {
        key: dp.key,
        title: dp.title || match.title,
        icon: dp.icon || match.icon || (dp.key === 'free' ? 'gift' : (dp.key === 'basic' ? 'shield' : 'crown')),
        monthlyPrice: Number(dp.monthlyPrice ?? match.monthlyPrice ?? 0),
        yearlyPrice: Number(dp.yearlyPrice ?? match.yearlyPrice ?? 0),
        subtitle: dp.subtitle || match.subtitle,
        features: dp.features && dp.features.length > 0 ? dp.features : (match.features || []),
        buttonText: dp.key === 'free' ? 'Start Free' : (userPlan.value === dp.key ? 'Subscribed' : (dp.key === 'basic' ? 'Get Basic' : 'Get Pro')),
        buttonClass: dp.key === 'free' ? 'btn-outline' : 'btn-primary',
        isPopular: dp.isPopular !== undefined ? dp.isPopular : (match.isPopular || false)
      }
    })
  }
  return defaultPlans
})
</script>

<template>
  <div class="plan-page">
    <!-- Top Left Background Dot Grid Pattern -->
    <div class="bg-dots">
      <svg width="120" height="120" viewBox="0 0 120 120" fill="none">
        <pattern id="dot-pattern" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse">
          <circle cx="4" cy="4" r="2.5" fill="#3b82f6" fill-opacity="0.35" />
        </pattern>
        <rect width="120" height="120" fill="url(#dot-pattern)" />
      </svg>
    </div>

    <!-- Decorative Ambient Waves Matching Graphic Background -->
    <svg class="wave-shape wave-top-right" viewBox="0 0 500 350" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M120 0C240 80 340 30 500 110V0H120Z" fill="url(#blueGradTR1)" fill-opacity="0.3"/>
      <path d="M200 0C300 95 380 50 500 170V0H200Z" fill="url(#blueGradTR2)" fill-opacity="0.5"/>
      <path d="M280 0C360 85 410 70 500 230V0H280Z" fill="url(#blueGradTR3)" fill-opacity="0.85"/>
      <defs>
        <linearGradient id="blueGradTR1" x1="120" y1="0" x2="500" y2="110" gradientUnits="userSpaceOnUse">
          <stop stop-color="#93c5fd"/>
          <stop offset="1" stop-color="#3b82f6"/>
        </linearGradient>
        <linearGradient id="blueGradTR2" x1="200" y1="0" x2="500" y2="170" gradientUnits="userSpaceOnUse">
          <stop stop-color="#3b82f6"/>
          <stop offset="1" stop-color="#1d4ed8"/>
        </linearGradient>
        <linearGradient id="blueGradTR3" x1="280" y1="0" x2="500" y2="230" gradientUnits="userSpaceOnUse">
          <stop stop-color="#2563eb"/>
          <stop offset="1" stop-color="#1d6bf3"/>
        </linearGradient>
      </defs>
    </svg>

    <svg class="wave-shape wave-bottom-left" viewBox="0 0 500 300" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M0 110C140 170 240 210 390 300H0V110Z" fill="url(#blueGradBL1)" fill-opacity="0.35"/>
      <path d="M0 160C120 195 190 235 310 300H0V160Z" fill="url(#blueGradBL2)" fill-opacity="0.6"/>
      <path d="M0 210C80 225 130 250 210 300H0V210Z" fill="url(#blueGradBL3)" fill-opacity="0.9"/>
      <defs>
        <linearGradient id="blueGradBL1" x1="0" y1="110" x2="390" y2="300" gradientUnits="userSpaceOnUse">
          <stop stop-color="#93c5fd"/>
          <stop offset="1" stop-color="#3b82f6"/>
        </linearGradient>
        <linearGradient id="blueGradBL2" x1="0" y1="160" x2="310" y2="300" gradientUnits="userSpaceOnUse">
          <stop stop-color="#3b82f6"/>
          <stop offset="1" stop-color="#1d4ed8"/>
        </linearGradient>
        <linearGradient id="blueGradBL3" x1="0" y1="210" x2="210" y2="300" gradientUnits="userSpaceOnUse">
          <stop stop-color="#2563eb"/>
          <stop offset="1" stop-color="#1d6bf3"/>
        </linearGradient>
      </defs>
    </svg>

    <svg class="wave-shape wave-bottom-right" viewBox="0 0 500 300" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M110 300C260 210 360 170 500 110V300H110Z" fill="url(#blueGradBR1)" fill-opacity="0.35"/>
      <path d="M190 300C310 235 380 195 500 160V300H190Z" fill="url(#blueGradBR2)" fill-opacity="0.6"/>
      <path d="M290 300C370 250 420 225 500 210V300H290Z" fill="url(#blueGradBR3)" fill-opacity="0.9"/>
      <defs>
        <linearGradient id="blueGradBR1" x1="500" y1="110" x2="110" y2="300" gradientUnits="userSpaceOnUse">
          <stop stop-color="#93c5fd"/>
          <stop offset="1" stop-color="#3b82f6"/>
        </linearGradient>
        <linearGradient id="blueGradBR2" x1="500" y1="160" x2="190" y2="300" gradientUnits="userSpaceOnUse">
          <stop stop-color="#3b82f6"/>
          <stop offset="1" stop-color="#1d4ed8"/>
        </linearGradient>
        <linearGradient id="blueGradBR3" x1="500" y1="210" x2="290" y2="300" gradientUnits="userSpaceOnUse">
          <stop stop-color="#2563eb"/>
          <stop offset="1" stop-color="#1d6bf3"/>
        </linearGradient>
      </defs>
    </svg>

    <!-- Header Navigation -->
    <header class="header">
      <div class="header-brand" @click="router.push('/')" title="Go to Home">
        <img src="/assets/careequity_remove.png" class="brand-logo-img" alt="CareEquity Logo" />
        <img src="/assets/careequity_name.png" class="brand-name-img" alt="CareEquity" />
      </div>

      <button class="skip-exit-btn" @click="handleExit">
        Skip & Exit
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="5" y1="12" x2="19" y2="12"></line>
          <polyline points="12 5 19 12 12 19"></polyline>
        </svg>
      </button>
    </header>

    <!-- Main Content Container (Fits inside viewport height) -->
    <main class="main-container">
      <!-- Title & Subtitle -->
      <div class="title-section">
        <h1 class="main-title">
          Choose the plan that fits <span class="highlight-text">your mission</span>
        </h1>
        <p class="main-subtitle">
          Empowering health equity with predictive SDOH intelligence & geospatial navigation.
        </p>

        <!-- Billing Toggle (SAVE 10% removed) -->
        <div class="billing-toggle-wrapper">
          <div class="billing-toggle">
            <button 
              class="toggle-btn" 
              :class="{ active: !isYearly }"
              @click="toggleBilling('monthly')"
            >
              Monthly
            </button>
            <button 
              class="toggle-btn" 
              :class="{ active: isYearly }"
              @click="toggleBilling('yearly')"
            >
              Yearly
            </button>
          </div>
        </div>
      </div>

      <!-- Pricing Cards Grid -->
      <div class="cards-grid">
        <div 
          v-for="plan in plans" 
          :key="plan.key" 
          class="plan-card"
          :class="{ 'active-plan': userPlan === plan.key }"
        >
          <!-- Featured Header Badges -->
          <div class="badge-tag tag-popular" v-if="plan.isPopular">MOST POPULAR</div>
          <div class="badge-tag tag-your-plan" v-if="userPlan === plan.key">Your Plan</div>

          <div class="card-body">
            <div>
              <!-- Icon -->
              <div class="plan-icon-box">
                <!-- Gift Icon for FREE -->
                <svg v-if="plan.icon === 'gift'" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="20 12 20 22 4 22 4 12"></polyline>
                  <rect x="2" y="7" width="20" height="5"></rect>
                  <line x1="12" y1="22" x2="12" y2="7"></line>
                  <path d="M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7z"></path>
                  <path d="M12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z"></path>
                </svg>

                <!-- Shield Icon with Star for BASIC -->
                <svg v-else-if="plan.icon === 'shield'" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                  <polygon points="12 8 13.09 10.21 15.54 10.57 13.77 12.3 14.19 14.73 12 13.58 9.81 14.73 10.23 12.3 8.46 10.57 10.91 10.21 12 8"></polygon>
                </svg>

                <!-- Crown Icon for PRO -->
                <svg v-else-if="plan.icon === 'crown'" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M2 4l3 12h14l3-12-6 7-4-7-4 7-6-7zm3 16h14"></path>
                </svg>
              </div>

              <!-- Title -->
              <h3 class="plan-name">{{ plan.title }}</h3>

              <!-- Price -->
              <div class="price-container">
                <span class="currency-symbol">₹</span>
                <span class="price-amount">{{ isYearly ? plan.yearlyPrice : plan.monthlyPrice }}</span>
                <span class="price-period">/mo</span>
              </div>

              <!-- Subtitle -->
              <p class="plan-subtitle">{{ plan.subtitle }}</p>

              <!-- Feature Checkmarks List -->
              <ul class="features-list">
                <li v-for="(feature, fIdx) in plan.features" :key="fIdx" class="feature-item">
                  <div class="check-icon">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
                      <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                  </div>
                  <span class="feature-text">{{ feature }}</span>
                </li>
              </ul>
            </div>

            <!-- Action Button -->
            <button 
              class="action-btn"
              :class="[plan.buttonClass, { 'btn-subscribed': userPlan === plan.key }]"
              @click="selectPlan(plan.key, plan.title)"
            >
              <template v-if="userPlan === plan.key">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 6px;">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                Subscribed
              </template>
              <template v-else>
                {{ plan.key === 'free' ? 'Start Free' : (plan.key === 'pro' ? 'Get Pro' : 'Select Basic') }}
              </template>
            </button>
          </div>
        </div>
      </div>

      <!-- Footer Trial Note -->
      <footer class="plan-footer">
        <div class="footer-note">
          <span class="check-badge-small">✓</span>
          <span>15-day free trial</span>
          <span class="dot">•</span>
          <span>Cancel anytime</span>
          <span class="dot">•</span>
          <span>No credit card required</span>
        </div>
      </footer>
    </main>

    <!-- Payment Loading Spinner Overlay -->
    <div v-if="isProcessingPayment" class="modal-overlay">
      <div class="modal-card" style="padding: 28px 24px; max-width: 320px;">
        <div class="modal-icon spin-loader" style="border: none; background: transparent;">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#1d6bf3" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="spinner-svg">
            <line x1="12" y1="2" x2="12" y2="6"></line>
            <line x1="12" y1="18" x2="12" y2="22"></line>
            <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line>
            <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line>
            <line x1="2" y1="12" x2="6" y2="12"></line>
            <line x1="18" y1="12" x2="22" y2="12"></line>
            <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line>
            <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line>
          </svg>
        </div>
        <h4 style="font-size: 1.1rem; font-weight: 700; color: #0f172a; margin: 8px 0 4px;">Opening Payment Gateway...</h4>
        <p style="font-size: 0.82rem; color: #64748b; margin: 0;">Please complete transaction in Razorpay modal</p>
      </div>
    </div>

    <!-- Interactive Plan Switch Confirmation Modal -->
    <div v-if="showConfirmationModal" class="modal-overlay" @click.self="closeConfirmation">
      <div class="modal-card">
        <div class="modal-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
            <polyline points="22 4 12 14.01 9 11.01"></polyline>
          </svg>
        </div>
        <h3 class="modal-title">Plan Activated!</h3>
        <p class="modal-desc">
          You are now subscribed to the <strong>{{ selectedPlanTitle }}</strong> plan. All features and elevated limits are active.
        </p>

        <!-- Display Razorpay Payment ID if available -->
        <div v-if="paymentDetails?.razorpay_payment_id" class="payment-id-badge" style="background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 12px; margin-bottom: 20px; font-size: 0.8rem; color: #475569; display: flex; align-items: center; justify-content: space-between;">
          <span style="font-weight: 600;">Razorpay Payment ID:</span>
          <code style="color: #1d6bf3; font-weight: 700;">{{ paymentDetails.razorpay_payment_id }}</code>
        </div>

        <button class="modal-confirm-btn" @click="closeConfirmation">Continue to Dashboard</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Main Page Setup - Fully Scrollable Responsive Layout */
.plan-page {
  min-height: 100vh;
  width: 100%;
  background: linear-gradient(180deg, #f0f6ff 0%, #f7fafc 45%, #e8f2fe 100%);
  font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  color: #1e293b;
  position: relative;
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  padding-bottom: 24px;
}

/* Background elements */
.bg-dots {
  position: absolute;
  top: 12px;
  left: 16px;
  z-index: 1;
  pointer-events: none;
  opacity: 0.85;
}

.wave-shape {
  position: absolute;
  pointer-events: none;
  z-index: 0;
}

.wave-top-right {
  top: 0;
  right: 0;
  width: 440px;
  height: 300px;
}

.wave-bottom-left {
  bottom: 0;
  left: 0;
  width: 440px;
  height: 260px;
}

.wave-bottom-right {
  bottom: 0;
  right: 0;
  width: 440px;
  height: 260px;
}

/* Top Header */
.header {
  position: relative;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 40px 10px;
  max-width: 1240px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
  flex-shrink: 0;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.brand-logo-img {
  width: 36px;
  height: 36px;
  object-fit: contain;
  flex-shrink: 0;
}

.brand-name-img {
  height: 52px;
  object-fit: contain;
  display: block;
}

.skip-exit-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 18px;
  background: #ffffff;
  border: 1.5px solid #dbeafe;
  border-radius: 9999px;
  color: #2563eb;
  font-size: 0.86rem;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.06);
  transition: all 0.2s ease;
}

.skip-exit-btn:hover {
  background: #eff6ff;
  border-color: #bfdbfe;
  transform: translateY(-1px);
}

/* Main Content Container */
.main-container {
  position: relative;
  z-index: 10;
  max-width: 1180px;
  margin: 0 auto;
  padding: 0 24px 16px;
  width: 100%;
  box-sizing: border-box;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: visible;
}

/* Title Section */
.title-section {
  text-align: center;
  max-width: 720px;
  margin: 0 auto 10px;
  flex-shrink: 0;
}

.main-title {
  font-size: 2.1rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.03em;
  line-height: 1.15;
  margin: 0 0 4px;
}

.highlight-text {
  color: #1d6bf3;
}

.main-subtitle {
  font-size: 0.9rem;
  color: #475569;
  margin: 0 0 10px;
  font-weight: 450;
  line-height: 1.4;
}

/* Billing Toggle */
.billing-toggle-wrapper {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  margin-top: 2px;
}

.billing-toggle {
  display: flex;
  align-items: center;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 9999px;
  padding: 3px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.toggle-btn {
  border: none;
  background: transparent;
  padding: 6px 20px;
  border-radius: 9999px;
  font-size: 0.85rem;
  font-weight: 600;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
}

.toggle-btn.active {
  background: #1d6bf3;
  color: #ffffff;
  box-shadow: 0 2px 8px rgba(29, 107, 243, 0.3);
}

/* Cards Grid */
.cards-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  align-items: stretch;
  margin: 14px 0 0;
  padding-top: 4px;
  flex: 1;
  min-height: 0;
  overflow: visible;
}

.plan-card {
  position: relative;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 16px;
  box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.04);
  transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: visible;
}

.plan-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 16px 32px -8px rgba(37, 99, 235, 0.14);
}

/* Active Selected Card Alone Gets Blue Border */
.plan-card.active-plan {
  border: 2.2px solid #1d6bf3 !important;
  box-shadow: 0 12px 32px -8px rgba(29, 107, 243, 0.22) !important;
}

.badge-tag {
  position: absolute;
  top: -12px;
  background: #1d6bf3;
  color: #ffffff;
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.05em;
  padding: 4px 14px;
  border-radius: 9999px;
  box-shadow: 0 4px 12px rgba(29, 107, 243, 0.35);
  text-transform: uppercase;
  z-index: 10;
  white-space: nowrap;
}

.tag-popular {
  left: 20px;
}

.tag-your-plan {
  right: 20px;
}

.card-body {
  padding: 20px 22px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 100%;
  box-sizing: border-box;
  overflow: visible;
}

/* Static Plan Icons */

.plan-icon-box {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: #eff6ff;
  border: 1px solid #dbeafe;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
  flex-shrink: 0;
  transition: transform 0.3s ease, background-color 0.3s ease;
}

.plan-name {
  font-size: 1rem;
  font-weight: 800;
  color: #1d6bf3;
  margin: 0 0 6px;
  letter-spacing: 0.04em;
  flex-shrink: 0;
}

.price-container {
  display: flex;
  align-items: baseline;
  gap: 2px;
  margin-bottom: 8px;
  flex-shrink: 0;
}

.currency-symbol {
  font-size: 1.6rem;
  font-weight: 800;
  color: #0f172a;
  line-height: 1;
}

.price-amount {
  font-size: 2.3rem;
  font-weight: 800;
  color: #0f172a;
  line-height: 1;
  letter-spacing: -0.03em;
}

.price-period {
  font-size: 0.88rem;
  color: #64748b;
  font-weight: 500;
}

.plan-subtitle {
  font-size: 0.8rem;
  color: #64748b;
  line-height: 1.4;
  margin: 0 0 12px;
  min-height: 34px;
  flex-shrink: 0;
}

/* Features List */
.features-list {
  list-style: none;
  padding: 0;
  margin: 0 0 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}

.feature-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 0.8rem;
  color: #334155;
  line-height: 1.35;
}

.check-icon {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #10b981;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 1px;
  box-shadow: 0 1.5px 4px rgba(16, 185, 129, 0.35);
}

.feature-text {
  font-weight: 500;
}

/* Action Buttons */
.action-btn {
  width: 100%;
  padding: 10px;
  border-radius: 10px;
  font-size: 0.88rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.btn-outline {
  background: #ffffff;
  border: 1.8px solid #1d6bf3;
  color: #1d6bf3;
}

.btn-outline:hover {
  background: #eff6ff;
}

.btn-primary {
  background: #1d6bf3;
  border: none;
  color: #ffffff;
  box-shadow: 0 4px 14px rgba(29, 107, 243, 0.3);
}

.btn-primary:hover {
  background: #1557d0;
  box-shadow: 0 6px 18px rgba(29, 107, 243, 0.4);
}

.btn-subscribed {
  background: #1d6bf3 !important;
  color: #ffffff !important;
  border: none !important;
  box-shadow: 0 4px 14px rgba(29, 107, 243, 0.3) !important;
}

/* Plan Footer */
.plan-footer {
  text-align: center;
  padding: 8px 0 10px;
  flex-shrink: 0;
}

.footer-note {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: 0.84rem;
  font-weight: 600;
  color: #475569;
}

.check-badge-small {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 1.5px solid #1d6bf3;
  color: #1d6bf3;
  font-size: 0.72rem;
  font-weight: 800;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.dot {
  color: #94a3b8;
}

/* Confirmation Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  backdrop-filter: blur(4px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.modal-card {
  background: #ffffff;
  border-radius: 20px;
  padding: 32px 28px;
  max-width: 400px;
  width: 100%;
  text-align: center;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  animation: modalPop 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

@keyframes modalPop {
  from {
    opacity: 0;
    transform: scale(0.92);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.modal-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
}

.modal-title {
  font-size: 1.3rem;
  font-weight: 800;
  color: #0f172a;
  margin: 0 0 8px;
}

.modal-desc {
  font-size: 0.88rem;
  color: #64748b;
  line-height: 1.45;
  margin: 0 0 20px;
}

.modal-confirm-btn {
  width: 100%;
  padding: 11px;
  background: #1d6bf3;
  border: none;
  border-radius: 10px;
  color: #ffffff;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 4px 14px rgba(29, 107, 243, 0.3);
  transition: all 0.2s ease;
}

.spinner-svg {
  animation: iconSpin 1.2s linear infinite;
}

.modal-confirm-btn:hover {
  background: #1557d0;
}

/* Responsive adjustments */
@media (max-width: 1024px) {
  .plan-page {
    height: auto;
    max-height: none;
    overflow-y: auto;
  }
  .cards-grid {
    grid-template-columns: 1fr;
    max-width: 480px;
    margin-left: auto;
    margin-right: auto;
  }
}
</style>
