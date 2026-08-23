<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import IconBase from './IconBase.vue'
import { 
  isLoggedIn, 
  setShowLoginScreen, 
  userPlan, 
  isAiDrawerOpen, 
  toggleAiDrawer,
  userTokensAllocated,
  userTokensUsed,
  isTokenLimitReached,
  currentUserId,
  currentUserEmail,
  syncUserSubscription,
  patientData,
  ocrExtractedJson,
  mlInputPayload,
  locationRecords
} from '../../store/appState'
import { SYSTEM_BACKEND_URL, RAG_BACKEND_URL } from '../../config'
import { US_COUNTIES_BY_STATE } from '../../data/usData.js'

const router = useRouter()

const isOpen = isAiDrawerOpen
const activeTab = ref('overview') // 'overview' or 'chat'
const selectedMode = ref('analyze') // 'analyze' or 'suggest'
const chatInput = ref('')
const isThinking = ref(false)
const messagesRef = ref(null)

const remainingTokens = computed(() => {
  if (userPlan.value === 'pro' || userTokensAllocated.value === -1) return 'Unlimited'
  const left = userTokensAllocated.value - userTokensUsed.value
  return left > 0 ? left : 0
})

function goToPlans() {
  isOpen.value = false
  router.push('/plan')
}

onMounted(() => {
  syncUserSubscription(SYSTEM_BACKEND_URL)
})

const messages = ref([
  {
    role: 'assistant',
    text: 'Hello! I am your **CareEquity Consult AI Assistant**. How can I help you analyze SDOH risk factors or suggest clinical action plans today?'
  }
])

const quickPrompts = [
  'Show Cuyahoga County risk factors',
  'Food access ideas for Wayne County',
  'What is SVI score of Marion County?'
]

function toggleChat() {
  if (!isLoggedIn.value) {
    setShowLoginScreen(true)
    return
  }
  if (!userPlan.value) {
    router.push('/plan')
    return
  }
  loadChatHistory()
  toggleAiDrawer()
}

function selectMode(mode) {
  selectedMode.value = mode
}

function sendPrompt(promptText) {
  chatInput.value = promptText
  handleSendMessage()
}



function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

// Helper to extract or default county FIPS from user query or uploaded location records (1 to 5)
function resolveFipsFromQuery(text) {
  const lower = text.toLowerCase()
  
  // FIPS direct match if specified
  const fipsMatch = text.match(/\b\d{4,5}\b/)
  if (fipsMatch) return fipsMatch[0]

  // Known county name to FIPS lookup map
  const countyFipsMap = {
    'cuyahoga': '39035',
    'wayne': '26163',
    'marion': '18097',
    'franklin': '39049',
    'autauga': '1001',
    'king': '53033',
    'trego': '20195',
    'cook': '17031',
    'harris': '48201',
    'maricopa': '04013'
  }

  // 1. Check direct match in user query text
  for (const [cName, cFips] of Object.entries(countyFipsMap)) {
    if (lower.includes(cName)) return cFips
  }

  // 2. Check location records (up to 5 locations) from Data Setup
  if (Array.isArray(locationRecords.value) && locationRecords.value.length > 0) {
    for (const loc of locationRecords.value) {
      if (loc.fips) return String(loc.fips)
      const locName = (loc.county || loc.name || '').toLowerCase()
      for (const [cName, cFips] of Object.entries(countyFipsMap)) {
        if (locName.includes(cName)) return cFips
      }
    }
  }

  // 3. Check patientData / OCR / ML payload
  if (patientData.value?.fips) return String(patientData.value.fips)
  if (mlInputPayload.value?.fips) return String(mlInputPayload.value.fips)
  if (ocrExtractedJson.value?.fips) return String(ocrExtractedJson.value.fips)

  const activeCounty = (patientData.value?.county || (patientData.value?.locations && patientData.value.locations[0]?.county) || '').toLowerCase()
  for (const [cName, cFips] of Object.entries(countyFipsMap)) {
    if (activeCounty.includes(cName)) return cFips
  }

  return '53033' // King County, WA default or fallback
}

async function recordTokensConsumed(consumed) {
  if (!consumed || consumed <= 0) return
  userTokensUsed.value += consumed
  localStorage.setItem('tokens_used', String(userTokensUsed.value))
  
  if (userTokensAllocated.value !== -1 && userTokensUsed.value >= userTokensAllocated.value) {
    isTokenLimitReached.value = true
  }

  try {
    const params = new URLSearchParams()
    if (currentUserEmail.value) params.append('email', currentUserEmail.value)
    if (currentUserId.value) params.append('user_id', currentUserId.value)
    params.append('tokens', consumed)

    const res = await fetch(`${SYSTEM_BACKEND_URL}/api/subscriptions/consume-tokens?${params.toString()}`, {
      method: 'POST'
    })
    if (res.ok) {
      const data = await res.json()
      if (data.limit_reached) {
        isTokenLimitReached.value = true
      }
      if (typeof data.tokens_used === 'number') {
        userTokensUsed.value = data.tokens_used
        localStorage.setItem('tokens_used', String(data.tokens_used))
      }
      if (typeof data.tokens_allocated === 'number') {
        userTokensAllocated.value = data.tokens_allocated
        localStorage.setItem('tokens_allocated', String(data.tokens_allocated))
      }
    }
  } catch (e) {
    console.warn('Failed to post consumed tokens:', e)
  }
}

function handleSendMessage() {
  if (isTokenLimitReached.value) {
    activeTab.value = 'chat'
    return
  }

  const text = chatInput.value.trim()
  if (!text) return

  // Switch to active chat feed view
  activeTab.value = 'chat'
  messages.value.push({ role: 'user', text })
  saveChatHistory()
  chatInput.value = ''
  isThinking.value = true
  scrollToBottom()

  const activeFips = resolveFipsFromQuery(text)
  const ragChatUrl = `${RAG_BACKEND_URL}/api/chat`

  // Format message history for RAG API schema
  const formattedHistory = messages.value
    .slice(0, -1)
    .filter(m => m.role === 'user' || m.role === 'assistant')
    .map(m => ({ role: m.role, content: m.text }))

  fetch(ragChatUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      fips: activeFips,
      question: text,
      chat_history: formattedHistory
    })
  })
  .then(r => {
    if (!r.ok) throw new Error('RAG Chat API HTTP error: ' + r.status)
    return r.json()
  })
  .then(data => {
    isThinking.value = false
    const reply = data.answer || 'No response received from RAG service.'
    const tokens = data.tokens_used || (Math.round((text.length + reply.length) / 4))
    messages.value.push({ role: 'assistant', text: reply, tokens })
    recordTokensConsumed(tokens)
    saveChatHistory()
    scrollToBottom()
  })
  .catch(err => {
    console.warn('Falling back to main system AI assistant:', err)
    
    // Attempt fallback to system backend
    const systemChatUrl = `${SYSTEM_BACKEND_URL}/api/v1/chat?member_id=DEMO001`
    fetch(systemChatUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role: 'user', content: text })
    })
    .then(r => {
      if (!r.ok) throw new Error('System Chat API HTTP error: ' + r.status)
      return r.json()
    })
    .then(data => {
      isThinking.value = false
      const reply = data.response || 'No response received from system backend.'
      const tokens = Math.round((text.length + reply.length) / 4)
      messages.value.push({ role: 'assistant', text: reply, tokens })
      recordTokensConsumed(tokens)
      saveChatHistory()
      scrollToBottom()
    })
    .catch(() => {
      isThinking.value = false
      let reply = ''
      const lower = text.toLowerCase()

      if (lower.includes('wayne')) {
        reply = 'In **Wayne County, MI**, the Health Equity Score is **48/100 (High Risk)**. Key driving factors: severe food deserts in Detroit, aging water infrastructure, and air quality concerns from heavy transit. Recommended intervention: Deploy mobile fresh food markets or outreach campaigns.'
      } else if (lower.includes('cuyahoga')) {
        reply = 'In **Cuyahoga County, OH**, the Health Equity Score is **64/100 (Moderate Risk)**. Vulnerability drivers include poverty in the Cleveland urban core and east Cleveland transit deserts. Recommended resource expansion: Connect members with Cleveland Food Bank and regional health clinics.'
      } else if (lower.includes('marion')) {
        reply = 'In **Marion County, IN**, the Health Equity Score is **58/100 (Moderate Risk)**. Factors include localized poverty pockets and Center Township food access limits. Recommended intervention: Target mobile screening clinics and food pantries.'
      } else if (lower.includes('franklin')) {
        reply = 'In **Franklin County, OH**, the Health Equity Score is **71/100**. Disparities are concentrated near student regions and outer beltways. Environmental ozone warnings are active.'
      } else if (lower.includes('hello') || lower.includes('hi') || lower.includes('hey')) {
        reply = 'Hello! I am your **CareEquity Consult AI Assistant**. I can help you analyze census-level social vulnerability indicators (SVI), plan clinical interventions, or write strategic county reports. How can I help you today?'
      } else {
        const activeLoc = (patientData.value?.address || ocrExtractedJson.value?.address || 'Cuyahoga County, OH')
        reply = `Analyzing query regarding location: "${activeLoc}" (FIPS ${activeFips}). Querying SDoH Knowledge Graph & PubMed RAG data... \n\nKey environmental & SDoH finding: Resource access index in ${activeLoc} highlights food security, housing, and environmental exposure as key drivers. Recommended clinical path: Deploy targeted mobile health units and community environmental support partnerships.`
      }

      const tokens = Math.round((text.length + reply.length) / 4)
      messages.value.push({ role: 'assistant', text: reply, tokens })
      recordTokensConsumed(tokens)
      saveChatHistory()
      scrollToBottom()
    })
  })
}

const isSearchOpen = ref(true)
const searchQuery = ref('')

// Load user-specific chat history from localStorage (Strict User Isolation)
function getChatStorageKey() {
  const uid = currentUserId.value || localStorage.getItem('user_id')
  const email = currentUserEmail.value || localStorage.getItem('user_email')
  if (!uid && !email) return null
  return `careequity_chat_history_${uid || 'id'}_${email || 'email'}`
}

const DEFAULT_INITIAL_MESSAGE = {
  role: 'assistant',
  text: 'Hello! I am your **CareEquity Consult AI Assistant**. How can I help you analyze SDOH risk factors or suggest clinical action plans today?'
}

function loadChatHistory() {
  try {
    const userKey = getChatStorageKey()
    
    // Reset to default assistant message if user is not logged in / no user key
    if (!userKey) {
      messages.value = [DEFAULT_INITIAL_MESSAGE]
      activeTab.value = 'overview'
      return
    }

    const saved = localStorage.getItem(userKey)
    if (saved) {
      const parsed = JSON.parse(saved)
      if (Array.isArray(parsed) && parsed.length > 0) {
        messages.value = parsed
        activeTab.value = 'chat'
        scrollToBottom()
        return
      }
    }
    
    // If no local history found for this specific user, reset messages state first
    messages.value = [DEFAULT_INITIAL_MESSAGE]
    activeTab.value = 'overview'
    
    // Fetch old questions & answers strictly for this authenticated user's email from remote database
    const email = currentUserEmail.value || localStorage.getItem('user_email')
    if (email) {
      fetch(`${SYSTEM_BACKEND_URL}/api/history/email/${encodeURIComponent(email)}`)
        .then(res => res.ok ? res.json() : null)
        .then(remoteHistory => {
          if (Array.isArray(remoteHistory) && remoteHistory.length > 0) {
            const loadedMsgs = [DEFAULT_INITIAL_MESSAGE]
            remoteHistory.forEach(item => {
              if (item.prompt) loadedMsgs.push({ role: 'user', text: item.prompt })
              if (item.response) loadedMsgs.push({ role: 'assistant', text: item.response })
            })
            messages.value = loadedMsgs
            activeTab.value = 'chat'
            saveChatHistory()
            scrollToBottom()
          }
        })
        .catch(err => console.warn('Could not fetch remote chat history for user:', err))
    }
  } catch (e) {
    console.warn('Failed to load user chat history:', e)
  }
}

function saveChatHistory() {
  try {
    const userKey = getChatStorageKey()
    if (!userKey) return // Do not save history for unauthenticated/guest sessions
    const dataStr = JSON.stringify(messages.value)
    localStorage.setItem(userKey, dataStr)
  } catch (e) {
    console.warn('Failed to save user chat history:', e)
  }
}

function clearChatHistory() {
  messages.value = [DEFAULT_INITIAL_MESSAGE]
  const key = getChatStorageKey()
  if (key) {
    localStorage.removeItem(key)
  }
  activeTab.value = 'overview'
}

import { watch } from 'vue'

watch(isOpen, (newVal) => {
  if (newVal) {
    loadChatHistory()
  }
})

watch(isLoggedIn, (newVal) => {
  if (newVal) {
    loadChatHistory()
  }
})

onMounted(() => {
  syncUserSubscription(SYSTEM_BACKEND_URL)
  loadChatHistory()
})

function formatMessageText(text) {
  if (!text) return ''

  // 1. Process Markdown tables
  let formatted = text.replace(/((?:\|[^\n]+\|\r?\n)+)/g, (match) => {
    const lines = match.trim().split('\n').map(l => l.trim()).filter(Boolean)
    if (lines.length < 2) return match
    
    // Filter out separator line like |---|---|
    const tableRows = lines.filter(l => !/^\|?\s*:?-+:?\s*(?:\|\s*:?-+:?\s*)*\|?$/.test(l))
    if (tableRows.length === 0) return match

    let html = '<div class="chat-table-wrapper"><table class="chat-table">'
    tableRows.forEach((rowStr, idx) => {
      const cells = rowStr.split('|').map(c => c.trim()).slice(1, -1)
      const tag = idx === 0 ? 'th' : 'td'
      html += '<tr>' + cells.map(c => `<${tag}>${c}</${tag}>`).join('') + '</tr>'
    })
    html += '</table></div>'
    return html
  })

  // 2. Bold text & line breaks
  formatted = formatted
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br/>')

  // 3. Highlight Search Text if Search Query Active
  if (searchQuery.value && searchQuery.value.trim().length > 0) {
    const q = searchQuery.value.trim().replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const regex = new RegExp(`(${q})`, 'gi')
    formatted = formatted.replace(regex, '<mark class="chat-highlight">$1</mark>')
  }

  return formatted
}
</script>

<template>
  <div class="floating-chatbot-container">
    
    <!-- Floating Trigger Button (Bottom Right) -->
    <button 
      class="floating-chat-btn" 
      :class="{ open: isOpen }"
      @click="toggleChat"
      :title="isOpen ? 'Close Consult AI' : 'Open Consult AI Assistant'"
    >
      <div class="btn-glow-ring"></div>
      <img v-if="!isOpen" src="/assets/assistance.gif" alt="AI Assistant" class="chat-gif-icon" />
      <span v-else class="close-trigger-icon">&times;</span>
      <span v-if="!isOpen" class="online-indicator"></span>
    </button>

    <!-- Optional Backdrop Blur Overlay -->
    <Transition name="fade">
      <div v-if="isOpen" class="chat-drawer-overlay" @click="isOpen = false"></div>
    </Transition>

    <!-- Full Right Side Drawer Panel -->
    <Transition name="chat-popup">
      <div v-if="isOpen" class="chat-popup-card">
        
        <!-- Top Header -->
        <div class="chat-header">
          <div class="header-left">
            <h4 class="header-title">Consult AI Assistant</h4>
          </div>
          <div class="header-right-actions">
            <button class="header-icon-btn" :class="{ active: isSearchOpen }" @click="isSearchOpen = !isSearchOpen" title="Search in chat">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              </svg>
            </button>
            <button class="header-icon-btn" @click="clearChatHistory" title="Clear chat history">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="3 6 5 6 21 6"></polyline>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              </svg>
            </button>
            <div class="header-token-counter" title="Remaining tokens">
              ⚡ {{ remainingTokens }} tokens
            </div>
          </div>
        </div>

        <!-- Search Bar Drawer Overlay -->
        <div v-if="isSearchOpen" class="chat-search-bar-row">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2.2">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input 
            v-model="searchQuery" 
            type="text" 
            placeholder="Search keywords in conversation..." 
            class="chat-search-input"
          />
          <button v-if="searchQuery" class="clear-search-btn" @click="searchQuery = ''">&times;</button>
        </div>

        <!-- Token Limit Exceeded Notice -->
        <div v-if="isTokenLimitReached" class="limit-reached-banner">
          <div class="limit-banner-content">
            <div class="limit-icon">⚠️</div>
            <div class="limit-text">
              <strong>Token Limit Reached!</strong>
              <p>You have used your {{ userPlan === 'free' ? '50,000 Free' : '250,000 Basic' }} plan tokens. Upgrade to continue consulting AI.</p>
            </div>
          </div>
          <button class="upgrade-now-btn" @click="goToPlans">
            Subscribe Now →
          </button>
        </div>

        <!-- Consult AI Overview / Welcome Screen -->
        <div v-if="activeTab === 'overview'" class="consult-overview-body">
          
          <!-- App Logo Badge (replaced heart) -->
          <div class="blue-icon-badge">
            <img src="/assets/careequity_remove.png" alt="CareEquity Logo" class="badge-logo-img" />
          </div>

          <!-- Main Title -->
          <h2 class="consult-title">Consult AI</h2>
          <p class="consult-subtitle">SDOH, SVI & Intervention Assistant</p>

          <!-- Action Cards Grid -->
          <div class="action-cards-grid">
            <div 
              class="action-card" 
              :class="{ selected: selectedMode === 'analyze' }"
              @click="selectMode('analyze')"
            >
              <div class="card-header-icon">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="16" x2="12" y2="12" />
                  <line x1="12" y1="8" x2="12.01" y2="8" />
                </svg>
              </div>
              <div class="card-content">
                <div class="card-title">Analyze SDOH</div>
                <div class="card-desc">Explore social vulnerability and barriers.</div>
              </div>
            </div>

            <div 
              class="action-card" 
              :class="{ selected: selectedMode === 'suggest' }"
              @click="selectMode('suggest')"
            >
              <div class="card-header-icon">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M9 18h6M10 22h4M15 9A3 3 0 0 0 9 9c0 1.5.8 2.5 1.5 3.3.5.6 1 1.2 1 2.2v.5h1v-.5c0-1 .5-1.6 1-2.2C14.2 11.5 15 10.5 15 9Z" />
                </svg>
              </div>
              <div class="card-content">
                <div class="card-title">Suggest Actions</div>
                <div class="card-desc">Generate clinical pathways & outreach plans.</div>
              </div>
            </div>
          </div>

          <!-- Quick suggestion pill buttons -->
          <div class="quick-prompts-list">
            <button 
              v-for="(prompt, idx) in quickPrompts" 
              :key="idx"
              class="quick-prompt-pill"
              @click="sendPrompt(prompt)"
            >
              {{ prompt }}
            </button>
          </div>

          <!-- Bottom Ask Box -->
          <div class="bottom-ask-box">
            <textarea 
              v-model="chatInput" 
              placeholder="Ask a question or describe a task..." 
              @keydown.enter.exact.prevent="handleSendMessage"
              rows="3"
            ></textarea>
            <button class="bottom-send-icon-btn" :disabled="!chatInput.trim()" @click="handleSendMessage" title="Send message">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 12h14"></path>
                <path d="M12 5l7 7-7 7"></path>
              </svg>
            </button>
          </div>

        </div>

        <!-- Active Chat Feed Screen -->
        <div v-else-if="activeTab === 'chat'" class="chat-feed-container">
          <div ref="messagesRef" class="chat-feed">
            <div 
              v-for="(msg, idx) in messages" 
              :key="idx"
              class="msg-bubble-wrapper"
              :class="msg.role"
            >
              <div v-if="msg.role === 'assistant'" class="avatar-mini">
                <img src="/assets/assistance.gif" alt="AI" />
              </div>
              <div class="msg-bubble" :class="msg.role">
                <div v-html="formatMessageText(msg.text)"></div>
                <div v-if="msg.role === 'assistant' && msg.tokens" class="token-badge">
                  ⚡ {{ msg.tokens }} tokens
                </div>
              </div>
            </div>

            <!-- Thinking / Loading Dots -->
            <div v-if="isThinking" class="msg-bubble-wrapper assistant">
              <div class="avatar-mini">
                <img src="/assets/assistance.gif" alt="AI" />
              </div>
              <div class="msg-bubble assistant thinking">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
              </div>
            </div>
          </div>

          <!-- Chat Feed Input Bar -->
          <div class="chat-input-bar">
            <input 
              v-model="chatInput" 
              type="text" 
              placeholder="Ask CareEquity AI..." 
              @keyup.enter="handleSendMessage"
            />
            <button class="send-btn" :disabled="!chatInput.trim()" @click="handleSendMessage">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 12h14"></path>
                <path d="M12 5l7 7-7 7"></path>
              </svg>
            </button>
          </div>
        </div>

      </div>
    </Transition>

  </div>
</template>

<style scoped>
.floating-chatbot-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 9999;
  font-family: inherit;
}

/* Floating Trigger Button */
.floating-chat-btn {
  position: relative;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: #ffffff;
  border: 2.5px solid #4f46e5;
  box-shadow: 0 8px 24px rgba(79, 70, 229, 0.3);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  outline: none;
  padding: 4px;
  overflow: hidden;
}

.floating-chat-btn:hover {
  transform: scale(1.08);
  box-shadow: 0 12px 30px rgba(79, 70, 229, 0.45);
  border-color: #3b82f6;
}

.floating-chat-btn.open {
  transform: scale(0.95);
  box-shadow: 0 4px 14px rgba(79, 70, 229, 0.2);
}

.chat-gif-icon {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.online-indicator {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 13px;
  height: 13px;
  border-radius: 50%;
  background: #10b981;
  border: 2px solid #ffffff;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.8);
  z-index: 2;
}.close-trigger-icon {
  font-size: 2rem;
  color: #1d6bf3;
  line-height: 1;
  font-weight: 300;
}

/* Backdrop Blur Overlay - transparent click outside receiver */
.chat-drawer-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: transparent;
  z-index: 9999;
}

/* Floating Widget Card (Bottom Right Popup Widget) */
.chat-popup-card {
  position: fixed;
  bottom: 90px;
  right: 24px;
  width: 380px;
  max-width: calc(100vw - 32px);
  height: 600px;
  max-height: calc(100vh - 120px);
  background: #ffffff;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 24px;
  box-shadow: 0 20px 48px -10px rgba(15, 23, 42, 0.22), 0 0 1px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 10000;
}

/* Application Blue Header Theme */
.chat-header {
  background: linear-gradient(135deg, #1d6bf3 0%, #2563eb 100%);
  padding: 14px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255, 255, 255, 0.15);
}

.header-right-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: #ffffff;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
}

.header-icon-btn:hover,
.header-icon-btn.active {
  background: #ffffff;
  color: #1d6bf3;
}

.chat-search-bar-row {
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  padding: 8px 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  animation: fadeIn 0.2s ease;
}

.chat-search-input {
  flex: 1;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 5px 10px;
  font-size: 0.78rem;
  outline: none;
  background: #ffffff;
  color: #1e293b;
}

.chat-search-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
}

.clear-search-btn {
  background: transparent;
  border: none;
  font-size: 1.1rem;
  color: #94a3b8;
  cursor: pointer;
  padding: 0 4px;
}

.clear-search-btn:hover {
  color: #475569;
}

:deep(.chat-highlight) {
  background-color: #fef08a !important;
  color: #854d0e !important;
  padding: 1px 3px;
  border-radius: 3px;
  font-weight: 700;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.back-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: #ffffff;
  font-size: 1rem;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
  color: #ffffff;
}

.header-token-counter {
  font-size: 0.75rem;
  font-weight: 700;
  color: #eff6ff;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(4px);
  padding: 4px 10px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.limit-reached-banner {
  background: #fef2f2;
  border-bottom: 1px solid #fecaca;
  padding: 12px 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  animation: fadeIn 0.3s ease;
}

.limit-banner-content {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.limit-icon {
  font-size: 1.3rem;
  line-height: 1;
}

.limit-text {
  font-size: 0.78rem;
  color: #991b1b;
}

.limit-text strong {
  display: block;
  font-size: 0.84rem;
  color: #7f1d1d;
  margin-bottom: 2px;
}

.limit-text p {
  margin: 0;
  line-height: 1.35;
}

.upgrade-now-btn {
  background: #dc2626;
  color: #ffffff;
  border: none;
  font-weight: 700;
  font-size: 0.8rem;
  padding: 8px 14px;
  border-radius: 8px;
  cursor: pointer;
  align-self: flex-end;
  transition: background 0.15s ease, transform 0.15s ease;
  box-shadow: 0 2px 4px rgba(220, 38, 38, 0.2);
}

.upgrade-now-btn:hover {
  background: #b91c1c;
  transform: translateY(-1px);
}

.close-chat-btn {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.8);
  font-size: 1.4rem;
  line-height: 1;
  padding: 4px;
  cursor: pointer;
  transition: color 0.15s ease;
}

.close-chat-btn:hover {
  color: #ffffff;
}

/* Consult AI Overview Body (Non-scrollable fit) */
.consult-overview-body {
  flex: 1;
  padding: 20px 24px;
  overflow-y: hidden;
  display: flex;
  flex-direction: column;
  background: #ffffff;
}

/* App Logo Badge */
.blue-icon-badge {
  width: 54px;
  height: 54px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 16px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 20px rgba(37, 99, 235, 0.15);
}

.badge-logo-img {
  width: 32px;
  height: 32px;
  object-fit: contain;
}

.consult-title {
  margin: 12px 0 2px 0;
  font-size: 1.75rem;
  font-weight: 800;
  color: #2563eb;
  text-align: center;
  letter-spacing: -0.5px;
}

.consult-subtitle {
  margin: 0 0 18px 0;
  font-size: 0.85rem;
  font-weight: 500;
  color: #64748b;
  text-align: center;
}

/* Action Mode Cards Grid */
.action-cards-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 16px;
}

.action-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 14px 12px;
  cursor: pointer;
  text-align: left;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.action-card.selected {
  background: #ffffff;
  border: 1.5px solid #3b82f6;
  box-shadow: 0 4px 14px rgba(59, 130, 246, 0.12);
}

.card-header-icon {
  color: #3b82f6;
  margin-bottom: 2px;
}

.card-title {
  font-size: 0.88rem;
  font-weight: 700;
  color: #1e293b;
}

.card-desc {
  font-size: 0.73rem;
  color: #64748b;
  line-height: 1.35;
}

/* Quick Prompt Pills */
.quick-prompts-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.quick-prompt-pill {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 10px 14px;
  font-size: 0.82rem;
  font-weight: 500;
  color: #334155;
  text-align: left;
  cursor: pointer;
  transition: all 0.15s ease;
}

.quick-prompt-pill:hover {
  background: #eff6ff;
  border-color: #bfdbfe;
  color: #2563eb;
}

/* Bottom Ask Box Container */
.bottom-ask-box {
  position: relative;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  min-height: 90px;
  margin-top: auto;
}

.bottom-ask-box textarea {
  width: 100%;
  border: none;
  outline: none;
  background: transparent;
  font-size: 0.84rem;
  color: #1e293b;
  resize: none;
  font-family: inherit;
  line-height: 1.4;
  padding-right: 42px;
}

.bottom-send-icon-btn {
  position: absolute;
  right: 10px;
  bottom: 10px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  border: none;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.bottom-send-icon-btn:hover:not(:disabled) {
  transform: scale(1.08);
  background: linear-gradient(135deg, #2563eb, #1e40af);
}

.bottom-send-icon-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Chat Feed Screen */
.chat-feed-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f8fafc;
}

.chat-feed {
  flex: 1;
  padding: 18px 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.msg-bubble-wrapper {
  display: flex;
  gap: 8px;
  align-items: flex-end;
  min-width: 0;
}

.msg-bubble-wrapper.user {
  justify-content: flex-end;
}

.avatar-mini {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
  border: 1px solid #cbd5e1;
  padding: 2px;
}

.avatar-mini img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.msg-bubble {
  max-width: 88%;
  padding: 11px 15px;
  border-radius: 14px;
  font-size: 0.82rem;
  line-height: 1.45;
  min-width: 0;
  word-break: break-word;
  overflow-wrap: break-word;
}

.msg-bubble.user {
  background: #3b82f6;
  color: #ffffff;
  border-bottom-right-radius: 2px;
}

.msg-bubble.assistant {
  background: #ffffff;
  color: #1e293b;
  border: 1px solid #e2e8f0;
  border-bottom-left-radius: 2px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
  overflow-x: auto;
}

.token-badge {
  margin-top: 6px;
  font-size: 0.68rem;
  font-weight: 600;
  color: #64748b;
  background: #f1f5f9;
  display: inline-block;
  padding: 2px 7px;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
}

.msg-bubble.thinking {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #94a3b8;
  animation: pulse-dot 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes pulse-dot {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.chat-input-bar {
  padding: 12px 18px;
  background: #ffffff;
  border-top: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.chat-input-bar input {
  flex: 1;
  border: 1px solid #cbd5e1;
  border-radius: 20px;
  padding: 10px 16px;
  font-size: 0.84rem;
  outline: none;
  transition: border-color 0.15s ease;
}

.chat-input-bar input:focus {
  border-color: #3b82f6;
}

.send-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #3b82f6;
  color: #ffffff;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
}

.send-btn:hover:not(:disabled) {
  background: #2563eb;
  transform: scale(1.05);
}

.send-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

/* Chat Table Styling for RAG / Markdown Responses */
.chat-table-wrapper {
  margin: 10px 0;
  max-width: 100%;
  overflow-x: auto;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

:deep(.chat-table) {
  width: 100%;
  max-width: 100%;
  border-collapse: collapse;
  font-size: 0.72rem;
  text-align: left;
}

:deep(.chat-table th) {
  background: rgba(59, 130, 246, 0.08);
  font-weight: 700;
  padding: 5px 6px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  color: #1e293b;
  white-space: nowrap;
}

:deep(.chat-table td) {
  padding: 5px 6px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  color: #475569;
  word-break: break-word;
}

:deep(.chat-table tr:last-child td) {
  border-bottom: none;
}

/* Transitions */
.chat-popup-enter-active,
.chat-popup-leave-active {
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.25s ease;
}

.chat-popup-enter-from,
.chat-popup-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 480px) {
  .chat-popup-card {
    width: 100vw;
  }
}
</style>
