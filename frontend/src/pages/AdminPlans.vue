<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import IconBase from '../components/dashboard/IconBase.vue'
import { MAIN_BACKEND_URL } from '../config'

const router = useRouter()

// Toast State
const showToast = ref(false)
const toastMsg = ref('')
const triggerToast = (msg) => {
  toastMsg.value = msg
  showToast.value = true
  setTimeout(() => {
    showToast.value = false
  }, 3500)
}

// Plan & Billing State
const isYearly = ref(false)
const selectedPlanKey = ref('basic')
const plans = ref([])
const isLoading = ref(true)
const savingKey = ref(null)
const isResetting = ref(false)

// New feature input state for each card
const newFeatureInputs = ref({
  free: '',
  basic: '',
  pro: ''
})

const toggleBilling = (mode) => {
  isYearly.value = mode === 'yearly'
}

const handleExit = () => {
  router.push('/admin')
}

// Fetch live plans from backend
const fetchPlans = async () => {
  try {
    const res = await fetch(`${MAIN_BACKEND_URL}/api/admin/plans`)
    if (res.ok) {
      const data = await res.json()
      plans.value = data.map(p => ({
        ...p,
        features: [...(p.features || [])]
      }))
    }
  } catch (err) {
    console.error('Failed to load plans:', err)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchPlans()
})

// Add feature to a specific plan
const addFeature = (planKey) => {
  const text = (newFeatureInputs.value[planKey] || '').trim()
  if (!text) return

  const targetPlan = plans.value.find(p => p.key === planKey)
  if (targetPlan) {
    targetPlan.features.push(text)
    newFeatureInputs.value[planKey] = ''
    triggerToast(`Added feature to ${targetPlan.title} plan. Click "Save Plan" to publish.`)
  }
}

// Remove feature from a specific plan
const removeFeature = (planKey, index) => {
  const targetPlan = plans.value.find(p => p.key === planKey)
  if (targetPlan) {
    const removed = targetPlan.features.splice(index, 1)
    triggerToast(`Removed "${removed[0]}". Click "Save Plan" to publish.`)
  }
}

// Toggle Most Popular status (can be enabled for more than one plan)
const togglePopular = (targetPlan) => {
  if (targetPlan.isPopular) {
    triggerToast(`"${targetPlan.title}" marked as Most Popular. Click "Save Plan" to publish.`)
  } else {
    triggerToast(`"${targetPlan.title}" removed from Most Popular. Click "Save Plan" to publish.`)
  }
}

// Save single plan
const savePlan = async (plan) => {
  savingKey.value = plan.key
  try {
    const payload = {
      key: plan.key,
      title: plan.title,
      monthlyPrice: Number(plan.monthlyPrice),
      yearlyPrice: Number(plan.yearlyPrice),
      subtitle: plan.subtitle,
      features: plan.features.filter(f => f && f.trim().length > 0),
      isPopular: Boolean(plan.isPopular)
    }

    const res = await fetch(`${MAIN_BACKEND_URL}/api/admin/plans/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })

    if (res.ok) {
      const data = await res.json()
      triggerToast(`Plan "${plan.title}" saved successfully!`)
      if (data.plan && data.plan.updatedAt) {
        plan.updatedAt = data.plan.updatedAt
      }
    } else {
      triggerToast('Could not save plan changes.')
    }
  } catch (err) {
    console.error('Save plan error:', err)
    triggerToast('Network error while saving plan.')
  } finally {
    savingKey.value = null
  }
}

// Save all plans
const saveAllPlans = async () => {
  for (const p of plans.value) {
    await savePlan(p)
  }
  triggerToast('All plans and features published live!')
}

// Reset all plans to system defaults
const resetAllPlans = async () => {
  if (!confirm('Are you sure you want to reset all plan costs and features to default values?')) {
    return
  }

  isResetting.value = true
  try {
    const res = await fetch(`${MAIN_BACKEND_URL}/api/admin/plans/reset`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })

    if (res.ok) {
      await fetchPlans()
      triggerToast('All plans reset to system default pricing & features.')
    }
  } catch (err) {
    console.error('Reset error:', err)
  } finally {
    isResetting.value = false
  }
}
</script>

<template>
  <div class="plan-page admin-plans-container">
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

    <!-- Top Toast Popup -->
    <Transition name="fade">
      <div v-if="showToast" class="toast-popup">
        <IconBase name="shield" :size="15" />
        <span>{{ toastMsg }}</span>
      </div>
    </Transition>

    <!-- Header Navigation with Admin Tools -->
    <header class="header">

      <div class="header-admin-actions">
        <button class="btn-admin-reset" @click="resetAllPlans" :disabled="isResetting" title="Reset all plans to defaults">
          <IconBase name="close" :size="14" />
          <span>Reset Defaults</span>
        </button>
        <button class="btn-admin-save" @click="saveAllPlans" title="Publish all changes live">
          <IconBase name="download" :size="15" />
          <span>Save All Changes</span>
        </button>
   
      </div>
    </header>

    <!-- Main Content Container (Matching Plan.vue visual hierarchy) -->
    <main class="main-container">
      <!-- Title & Subtitle -->
      <div class="title-section">
        <h1 class="main-title">
          Choose the plan that fits <span class="highlight-text">your mission</span>
        </h1>
        <p class="main-subtitle">
          Empowering health equity with predictive SDOH intelligence & geospatial navigation.
        </p>

        <!-- Billing Toggle -->
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

      <!-- Loading State -->
      <div v-if="isLoading" class="loading-state">
        <div class="spinner"></div>
        <p>Loading plan configurations...</p>
      </div>

      <!-- Pricing Cards Grid (Free, Basic, Pro) -->
      <div v-else class="cards-grid">
        <div 
          v-for="plan in plans" 
          :key="plan.key" 
          class="plan-card"
          :class="{ 'selected-plan': selectedPlanKey === plan.key, [`card-tier-${plan.key}`]: true }"
          @click="selectedPlanKey = plan.key"
        >
          <!-- Featured Header Badges (Shown ONLY when checked as Most Popular) -->
          <div v-if="plan.isPopular" class="badge-tag tag-popular">
            MOST POPULAR
          </div>

          <div class="card-body">
            <div>
              <!-- Top Row: Icon + Popular Checkbox -->
              <div class="plan-top-row">
                <div class="plan-icon-box">
                  <!-- Gift Icon for FREE -->
                  <svg v-if="plan.key === 'free'" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20 12 20 22 4 22 4 12"></polyline>
                    <rect x="2" y="7" width="20" height="5"></rect>
                    <line x1="12" y1="22" x2="12" y2="7"></line>
                    <path d="M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7z"></path>
                    <path d="M12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z"></path>
                  </svg>

                  <!-- Shield Icon with Star for BASIC -->
                  <svg v-else-if="plan.key === 'basic'" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                    <polygon points="12 8 13.09 10.21 15.54 10.57 13.77 12.3 14.19 14.73 12 13.58 9.81 14.73 10.23 12.3 8.46 10.57 10.91 10.21 12 8"></polygon>
                  </svg>

                  <!-- Crown Icon for PRO -->
                  <svg v-else width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M2 4l3 12h14l3-12-6 7-4-7-4 7-6-7zm3 16h14"></path>
                  </svg>
                </div>

                <!-- Admin Popular Toggle -->
                <label class="admin-popular-toggle" title="Toggle Most Popular badge" @click.stop>
                  <input type="checkbox" v-model="plan.isPopular" @change="togglePopular(plan)" />
                  <span>Popular</span>
                </label>
              </div>

              <!-- Editable Plan Title -->
              <input 
                v-model="plan.title" 
                type="text" 
                class="plan-name-input font-bold" 
                placeholder="Plan Name"
              />

              <!-- Editable Price Display -->
              <div class="price-container-editable">
                <span class="currency-symbol">₹</span>
                <input 
                  v-if="isYearly"
                  v-model.number="plan.yearlyPrice" 
                  type="number" 
                  min="0" 
                  class="price-number-input font-bold"
                  title="Yearly price per month" 
                />
                <input 
                  v-else
                  v-model.number="plan.monthlyPrice" 
                  type="number" 
                  min="0" 
                  class="price-number-input font-bold"
                  title="Monthly price" 
                />
                <span class="price-period">/mo</span>
                <span class="mode-tag">{{ isYearly ? '(Yearly)' : '(Monthly)' }}</span>
              </div>

              <!-- Editable Subtitle Description -->
              <textarea 
                v-model="plan.subtitle" 
                rows="2" 
                class="plan-subtitle-editable" 
                placeholder="Plan subtitle description..."
              ></textarea>

              <!-- Feature Checkmarks List with Add/Remove -->
              <ul class="features-list-editable">
                <li v-for="(feature, fIdx) in plan.features" :key="fIdx" class="feature-item-editable">
                  <div class="check-icon">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
                      <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                  </div>
                  <input 
                    v-model="plan.features[fIdx]" 
                    type="text" 
                    class="feature-inline-input" 
                    placeholder="Feature name..."
                  />
                  <button 
                    class="btn-del-feature" 
                    @click="removeFeature(plan.key, fIdx)" 
                    title="Remove this feature"
                  >
                    &times;
                  </button>
                </li>
              </ul>

              <!-- Add New Feature Row -->
              <div class="add-feature-inline">
                <div class="add-feature-input-wrap">
                  <span class="plus-icon-bullet">+</span>
                  <input 
                    v-model="newFeatureInputs[plan.key]" 
                    type="text" 
                    class="add-feature-field" 
                    placeholder="Add new feature..."
                    @keyup.enter="addFeature(plan.key)"
                  />
                </div>
                <button class="btn-add-feature-ok" @click="addFeature(plan.key)" title="Add feature to plan">
                  Add
                </button>
              </div>
            </div>

            <!-- Save Plan Action Button -->
            <button 
              class="action-btn btn-primary"
              @click="savePlan(plan)"
              :disabled="savingKey === plan.key"
            >
              <template v-if="savingKey === plan.key">
                Saving Changes...
              </template>
              <template v-else>
                Save Plan
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
  </div>
</template>

<style scoped>
/* Main Page Setup - Clean Full-screen Layout matching Plan.vue */
.admin-plans-container {
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
  justify-content: space-between;
  box-sizing: border-box;
  padding-bottom: 24px;
}

/* Background waves & dots matching Plan.vue */
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
  width: 28vw;
  max-width: 440px;
  opacity: 0.9;
}

.wave-bottom-left {
  bottom: 0;
  left: 0;
  width: 24vw;
  max-width: 380px;
  opacity: 0.85;
}

.wave-bottom-right {
  bottom: 0;
  right: 0;
  width: 26vw;
  max-width: 400px;
  opacity: 0.9;
}

/* Header */
.header {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 8px 36px 4px;
  position: relative;
  z-index: 10;
  flex-shrink: 0;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.brand-logo-img {
  width: 32px;
  height: 32px;
  object-fit: contain;
}

.brand-name-img {
  height: 20px;
  object-fit: contain;
}

.header-admin-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn-admin-reset {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #ffffff;
  border: 1.5px solid #cbd5e1;
  border-radius: 9999px;
  padding: 6px 14px;
  font-size: 0.82rem;
  font-weight: 600;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-admin-reset:hover {
  border-color: #fca5a5;
  color: #ef4444;
  background: #fef2f2;
}

.btn-admin-save {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #1d6bf3;
  color: #ffffff;
  border: none;
  border-radius: 9999px;
  padding: 6px 16px;
  font-size: 0.84rem;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(29, 107, 243, 0.25);
  transition: all 0.2s ease;
}

.btn-admin-save:hover {
  background: #1754c7;
  transform: translateY(-1px);
}

.skip-exit-btn {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  padding: 6px 14px;
  border-radius: 9999px;
  color: #475569;
  font-size: 0.84rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s ease;
}

.skip-exit-btn:hover {
  background: #f1f5f9;
  border-color: #94a3b8;
  color: #0f172a;
}

/* Main Container */
.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  align-items: center;
  padding: 0 24px 10px;
  position: relative;
  z-index: 2;
  box-sizing: border-box;
}

/* Title Section */
.title-section {
  text-align: center;
  max-width: 720px;
  margin: 0 auto 20px;
  flex-shrink: 0;
}

.main-title {
  font-size: 2.1rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.03em;
  line-height: 1.15;
  margin: 0 0 3px;
}

.highlight-text {
  color: #1d6bf3;
}

.main-subtitle {
  font-size: 0.9rem;
  color: #475569;
  margin: 0 0 8px;
  font-weight: 450;
  line-height: 1.4;
}

/* Billing Toggle */
.billing-toggle-wrapper {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  margin-top: 0;
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
  box-shadow: 0 2px 6px rgba(29, 107, 243, 0.25);
}

/* Loading */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 0;
  gap: 12px;
  color: #64748b;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e2e8f0;
  border-top-color: #1d6bf3;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Cards Grid */
.cards-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 22px;
  width: 100%;
  max-width: 1100px;
  align-items: stretch;
}

.plan-card {
  background: #ffffff;
  border: 1.5px solid #e2e8f0;
  border-radius: 20px;
  padding: 22px 20px 20px;
  position: relative;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 24px rgba(30, 41, 59, 0.04);
  transition: all 0.25s ease;
  box-sizing: border-box;
}

.plan-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 16px 36px rgba(29, 107, 243, 0.09);
  border-color: #93c5fd;
}

.selected-plan {
  border: 2px solid #1d6bf3 !important;
  box-shadow: 0 14px 34px rgba(29, 107, 243, 0.18) !important;
}

.card-popular {
  border-color: #1d6bf3 !important;
  box-shadow: 0 14px 34px rgba(29, 107, 243, 0.12) !important;
}

/* Most Popular Badge */
.badge-tag {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  padding: 4px 14px;
  border-radius: 9999px;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.05em;
  z-index: 10;
  white-space: nowrap;
}

.tag-popular {
  background: #1d6bf3;
  color: #ffffff;
  box-shadow: 0 4px 10px rgba(29, 107, 243, 0.35);
}

.card-body {
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.plan-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.plan-icon-box {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: #eff6ff;
  border: 1px solid #dbeafe;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.admin-popular-toggle {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.74rem;
  font-weight: 700;
  color: #64748b;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 9999px;
  padding: 3px 9px;
  cursor: pointer;
}

.admin-popular-toggle input {
  accent-color: #1d6bf3;
}

/* Editable Plan Name */
.plan-name-input {
  font-size: 1.05rem;
  font-weight: 800;
  color: #1d6bf3;
  margin: 0 0 6px;
  letter-spacing: 0.04em;
  border: 1px solid transparent;
  border-radius: 6px;
  padding: 2px 4px;
  background: transparent;
  outline: none;
  width: calc(100% - 8px);
}

.plan-name-input:focus {
  border-color: #bfdbfe;
  background: #eff6ff;
}

/* Editable Price Container */
.price-container-editable {
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

.price-number-input {
  font-size: 2.2rem;
  font-weight: 800;
  color: #0f172a;
  line-height: 1;
  letter-spacing: -0.03em;
  border: 1px solid transparent;
  border-radius: 6px;
  background: transparent;
  outline: none;
  max-width: 130px;
  padding: 0 4px;
}

.price-number-input:focus {
  border-color: #bfdbfe;
  background: #eff6ff;
}

.price-period {
  font-size: 0.88rem;
  color: #64748b;
  font-weight: 500;
}

.mode-tag {
  font-size: 0.72rem;
  color: #94a3b8;
  margin-left: 6px;
  font-weight: 600;
}

/* Editable Subtitle */
.plan-subtitle-editable {
  font-size: 0.8rem;
  color: #334155;
  line-height: 1.4;
  margin: 0 0 10px;
  min-height: 42px;
  width: 100%;
  border: 1.5px solid #bfdbfe;
  background: #f8fbff;
  border-radius: 8px;
  padding: 6px 8px;
  outline: none;
  resize: vertical;
  font-family: inherit;
  box-sizing: border-box;
  transition: all 0.2s ease;
}

.plan-subtitle-editable:hover {
  border-color: #60a5fa;
  background: #ffffff;
}

.plan-subtitle-editable:focus {
  border-color: #1d6bf3;
  background: #ffffff;
  box-shadow: 0 0 0 3px rgba(29, 107, 243, 0.12);
  color: #0f172a;
}

/* Features List Editable */
.features-list-editable {
  list-style: none;
  padding: 0;
  margin: 0 0 10px;
  display: flex;
  flex-direction: column;
  gap: 7px;
  max-height: 280px;
  overflow-y: auto;
  padding-right: 4px;
}

.feature-item-editable {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8rem;
  color: #334155;
  padding: 2px 4px;
  border-radius: 6px;
  transition: background 0.15s ease;
}

.feature-item-editable:hover {
  background: #f8fafc;
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
  box-shadow: 0 1.5px 4px rgba(16, 185, 129, 0.35);
}

.feature-inline-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 0.8rem;
  color: #334155;
  font-weight: 500;
  outline: none;
  padding: 2px 4px;
  border-radius: 4px;
}

.feature-inline-input:focus {
  background: #ffffff;
  box-shadow: 0 0 0 1px #93c5fd;
  color: #0f172a;
}

.btn-del-feature {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 1.1rem;
  line-height: 1;
  cursor: pointer;
  padding: 0 4px;
  opacity: 0;
  transition: opacity 0.15s ease, color 0.15s ease;
}

.feature-item-editable:hover .btn-del-feature {
  opacity: 1;
}

.btn-del-feature:hover {
  color: #ef4444;
}

/* Add Feature Inline */
.add-feature-inline {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
  margin-bottom: 14px;
  background: #f8fafc;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  padding: 4px 6px;
  transition: all 0.2s ease;
}

.add-feature-inline:focus-within {
  background: #ffffff;
  border-color: #1d6bf3;
  box-shadow: 0 0 0 3px rgba(29, 107, 243, 0.1);
}

.add-feature-input-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
}

.plus-icon-bullet {
  font-size: 1.1rem;
  font-weight: 700;
  color: #1d6bf3;
  line-height: 1;
  padding-left: 6px;
}

.add-feature-field {
  flex: 1;
  border: none;
  background: transparent;
  padding: 6px 4px;
  font-size: 0.82rem;
  color: #0f172a;
  outline: none;
  font-family: inherit;
}

.add-feature-field::placeholder {
  color: #94a3b8;
  font-size: 0.8rem;
}

.btn-add-feature-ok {
  background: #1d6bf3;
  color: #ffffff;
  border: none;
  font-size: 0.78rem;
  font-weight: 700;
  border-radius: 8px;
  padding: 6px 14px;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(29, 107, 243, 0.2);
  transition: all 0.15s ease;
}

.btn-add-feature-ok:hover {
  background: #1754c7;
  transform: scale(1.02);
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
  margin-top: auto;
}

.btn-primary {
  background: #1d6bf3;
  color: #ffffff;
  border: none;
  box-shadow: 0 4px 12px rgba(29, 107, 243, 0.25);
}

.btn-primary:hover {
  background: #1656c9;
  transform: translateY(-1px);
}

.btn-outline {
  background: transparent;
  color: #1d6bf3;
  border: 1.5px solid #1d6bf3;
}

.btn-outline:hover {
  background: #eff6ff;
  transform: translateY(-1px);
}

/* Footer Trial Note */
.plan-footer {
  text-align: center;
  margin-top: 14px;
  flex-shrink: 0;
}

.footer-note {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 0.78rem;
  color: #64748b;
  font-weight: 500;
  background: rgba(255, 255, 255, 0.7);
  padding: 4px 14px;
  border-radius: 9999px;
  border: 1px solid rgba(226, 232, 240, 0.8);
}

.check-badge-small {
  width: 13px;
  height: 13px;
  background: #10b981;
  color: #fff;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 8px;
  font-weight: 800;
}

.dot {
  color: #94a3b8;
}

/* Toast */
.toast-popup {
  position: fixed;
  top: 20px;
  right: 24px;
  background: #0f172a;
  color: #ffffff;
  padding: 10px 18px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  z-index: 9999;
}

@media (max-width: 1024px) {
  .cards-grid {
    grid-template-columns: 1fr;
    max-width: 480px;
  }
}
</style>
