<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import IconBase from './IconBase.vue'
import { isLoggedIn, setShowLoginScreen, userPlan } from '../../store/appState'
import { SYSTEM_BACKEND_URL } from '../../config'

const router = useRouter()

const isOpen = ref(false)
const activeTab = ref('overview') // 'overview' or 'chat'
const selectedMode = ref('analyze') // 'analyze' or 'suggest'
const chatInput = ref('')
const isThinking = ref(false)
const messagesRef = ref(null)

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
  isOpen.value = !isOpen.value
}

function selectMode(mode) {
  selectedMode.value = mode
}

function sendPrompt(promptText) {
  chatInput.value = promptText
  handleSendMessage()
}

function formatMessageText(text) {
  if (!text) return ''
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br/>')
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

function handleSendMessage() {
  const text = chatInput.value.trim()
  if (!text) return

  // Switch to active chat feed view
  activeTab.value = 'chat'
  messages.value.push({ role: 'user', text })
  chatInput.value = ''
  isThinking.value = true
  scrollToBottom()

  // Try live FastAPI chat endpoint, fallback to intelligent simulation
  const chatUrl = `${SYSTEM_BACKEND_URL}/api/v1/chat?member_id=DEMO001`
  fetch(chatUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ role: 'user', content: text })
  })
  .then(r => {
    if (!r.ok) throw new Error('Live Chat API HTTP error: ' + r.status)
    return r.json()
  })
  .then(data => {
    isThinking.value = false
    const reply = data.response || 'No response received from AI service.'
    messages.value.push({ role: 'assistant', text: reply })
    scrollToBottom()
  })
  .catch(err => {
    console.warn('Falling back to local AI assistant response:', err)
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
      reply = `Thank you for asking! Regarding "${text}", I am analyzing the SVI dataset across Cuyahoga, Wayne, Marion, and Franklin counties. Please specify which county or risk factor you would like to drill down into.`
    }

    messages.value.push({ role: 'assistant', text: reply })
    scrollToBottom()
  })
}
</script>

<template>
  <div class="floating-chatbot-container">
    
    <!-- Floating Trigger Button (Bottom Right) -->
    <button 
      class="floating-chat-btn" 
      :class="{ open: isOpen }"
      @click="toggleChat"
      title="Open Consult AI Assistant"
    >
      <div class="btn-glow-ring"></div>
      <img src="/assets/assistance.gif" alt="AI Assistant" class="chat-gif-icon" />
      <span class="online-indicator"></span>
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
            <button v-if="activeTab === 'chat'" class="back-btn" @click="activeTab = 'overview'" title="Back to Consult AI Screen">
              ←
            </button>
            <h4 class="header-title">Consult AI Assistant</h4>
          </div>
          <button class="close-chat-btn" @click="isOpen = false" title="Close">&times;</button>
        </div>

        <!-- Consult AI Overview / Welcome Screen -->
        <div v-if="activeTab === 'overview'" class="consult-overview-body">
          
          <!-- Blue Heart Icon Badge -->
          <div class="blue-icon-badge">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
            </svg>
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

          <!-- "Great for:" bullet section -->
          <div class="great-for-section">
            <h5 class="great-for-title">Great for:</h5>
            <ul class="great-for-list">
              <li>Identifying community disparities</li>
              <li>Targeting preventative care outreach</li>
              <li>Recommending local support programs</li>
            </ul>
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
            <button class="bottom-floating-chat-icon" @click="handleSendMessage" title="Send message">
              <img src="/assets/assistance.gif" alt="AI Assistant" />
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
              <div class="msg-bubble" :class="msg.role" v-html="formatMessageText(msg.text)"></div>
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
              <IconBase name="trend" :size="14" style="transform: rotate(45deg);" />
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
}

/* Backdrop Blur Overlay */
.chat-drawer-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(15, 23, 42, 0.15);
  backdrop-filter: blur(2px);
  z-index: 9999;
}

/* Full Height Right Drawer Panel */
.chat-popup-card {
  position: fixed;
  top: 0;
  right: 0;
  width: 440px;
  max-width: 100vw;
  height: 100vh;
  background: #ffffff;
  border-left: 1px solid #e2e8f0;
  box-shadow: -12px 0 40px rgba(15, 23, 42, 0.16);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 10000;
}

/* Clean Header */
.chat-header {
  background: #ffffff;
  padding: 18px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #f1f5f9;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.back-btn {
  background: #f1f5f9;
  border: none;
  color: #475569;
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
  font-size: 1.1rem;
  font-weight: 700;
  color: #0f172a;
}

.close-chat-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 1.4rem;
  line-height: 1;
  padding: 4px;
  cursor: pointer;
  transition: color 0.15s ease;
}

.close-chat-btn:hover {
  color: #334155;
}

/* Consult AI Overview Body */
.consult-overview-body {
  flex: 1;
  padding: 24px 28px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  background: #ffffff;
}

/* Blue Heart Icon Badge */
.blue-icon-badge {
  width: 56px;
  height: 56px;
  background: #3b82f6;
  border-radius: 16px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 25px rgba(59, 130, 246, 0.35);
}

.consult-title {
  margin: 16px 0 2px 0;
  font-size: 1.85rem;
  font-weight: 800;
  color: #2563eb;
  text-align: center;
  letter-spacing: -0.5px;
}

.consult-subtitle {
  margin: 0 0 24px 0;
  font-size: 0.88rem;
  font-weight: 500;
  color: #64748b;
  text-align: center;
}

/* Action Mode Cards Grid */
.action-cards-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-bottom: 24px;
}

.action-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 16px 14px;
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
  font-size: 0.9rem;
  font-weight: 700;
  color: #1e293b;
}

.card-desc {
  font-size: 0.75rem;
  color: #64748b;
  line-height: 1.35;
}

/* Great For Section */
.great-for-section {
  border-left: 3px solid #3b82f6;
  padding-left: 14px;
  margin-bottom: 24px;
  text-align: left;
}

.great-for-title {
  margin: 0 0 6px 0;
  font-size: 0.9rem;
  font-weight: 700;
  color: #1e293b;
}

.great-for-list {
  margin: 0;
  padding-left: 16px;
  color: #475569;
  font-size: 0.84rem;
  line-height: 1.65;
}

/* Quick Prompt Pills */
.quick-prompts-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 24px;
}

.quick-prompt-pill {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px 18px;
  font-size: 0.86rem;
  font-weight: 500;
  color: #334155;
  text-align: left;
  cursor: pointer;
  transition: all 0.15s ease;
  width: 100%;
}

.quick-prompt-pill:hover {
  background: #eff6ff;
  border-color: #3b82f6;
  color: #2563eb;
}

/* Bottom Ask Box Container */
.bottom-ask-box {
  position: relative;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  min-height: 110px;
  margin-top: auto;
}

.bottom-ask-box textarea {
  width: 100%;
  border: none;
  outline: none;
  background: transparent;
  font-size: 0.86rem;
  color: #1e293b;
  resize: none;
  font-family: inherit;
  line-height: 1.4;
  padding-right: 50px;
}

.bottom-floating-chat-icon {
  position: absolute;
  right: 12px;
  bottom: 12px;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: #ffffff;
  border: 2px solid #6366f1;
  padding: 3px;
  cursor: pointer;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  transition: transform 0.2s ease;
}

.bottom-floating-chat-icon:hover {
  transform: scale(1.08);
}

.bottom-floating-chat-icon img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
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
  max-width: 82%;
  padding: 11px 15px;
  border-radius: 14px;
  font-size: 0.82rem;
  line-height: 1.45;
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
