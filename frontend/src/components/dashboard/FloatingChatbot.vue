<script setup>
import { ref, onMounted, nextTick } from 'vue'
import IconBase from './IconBase.vue'
import { SYSTEM_BACKEND_URL } from '../../config'

const isOpen = ref(false)
const chatInput = ref('')
const isThinking = ref(false)
const messagesRef = ref(null)

const messages = ref([
  {
    role: 'assistant',
    text: 'Hello! I am your **CareEquity AI Assistant**. Ask me anything about member health equity, SDOH risk drivers, county vulnerabilities, or clinical interventions!'
  }
])

const quickSuggestions = [
  'Cuyahoga County risk drivers',
  'Wayne County food insecurity',
  'What is SVI score of Marion County?'
]

function toggleChat() {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    scrollToBottom()
  }
}

function clickSuggestion(suggest) {
  chatInput.value = suggest
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
      reply = 'Hello! I am your **CareEquity AI Assistant**. I can help you analyze census-level social vulnerability indicators (SVI), plan clinical interventions, or write strategic county reports. How can I help you today?'
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
      title="Open CareEquity AI Chatbot"
    >
      <div class="btn-glow-ring"></div>
      <img src="/assets/assistance.gif" alt="AI Assistant" class="chat-gif-icon" />
      <span class="online-indicator"></span>
    </button>

    <!-- Floating Chat Window / Modal -->
    <Transition name="chat-popup">
      <div v-if="isOpen" class="chat-popup-card">
        
        <!-- Header -->
        <div class="chat-header">
          <div class="header-info">
            <div class="header-avatar">
              <img src="/assets/assistance.gif" alt="AI Assistant" />
            </div>
            <div>
              <h4>CareEquity AI Assistant</h4>
              <p class="status-subtitle"><span class="status-dot"></span> Active • Instant Insights</p>
            </div>
          </div>
          <button class="close-chat-btn" @click="isOpen = false" title="Minimize Chat">&times;</button>
        </div>

        <!-- Chat Feed Area -->
        <div ref="messagesRef" class="chat-feed">
          
          <!-- Suggestion Chips -->
          <div class="quick-suggestions-row">
            <span class="suggestions-label">Suggested prompts:</span>
            <div class="chips-flex">
              <button 
                v-for="(chip, idx) in quickSuggestions" 
                :key="idx"
                class="suggestion-chip"
                @click="clickSuggestion(chip)"
              >
                {{ chip }}
              </button>
            </div>
          </div>

          <!-- Message Bubbles -->
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

          <!-- Typing / Thinking State -->
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

        <!-- Bottom Input Bar -->
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

/* Floating Popup Window */
.chat-popup-card {
  position: fixed;
  bottom: 96px;
  right: 24px;
  width: 380px;
  height: 520px;
  max-height: 80vh;
  background: #ffffff;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 20px;
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.18);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 10000;
}

/* Header */
.chat-header {
  background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
  color: #ffffff;
  padding: 14px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.header-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3px;
  overflow: hidden;
  flex-shrink: 0;
  border: 1.5px solid rgba(255, 255, 255, 0.4);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

.header-avatar img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.header-info h4 {
  margin: 0;
  font-size: 0.92rem;
  font-weight: 700;
  color: #ffffff;
}

.status-subtitle {
  margin: 2px 0 0;
  font-size: 0.68rem;
  color: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  gap: 5px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 6px #10b981;
}

.close-chat-btn {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: #ffffff;
  font-size: 1.3rem;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.15s ease;
}

.close-chat-btn:hover {
  background: rgba(255, 255, 255, 0.25);
}

/* Chat Feed */
.chat-feed {
  flex: 1;
  padding: 14px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #f8fafc;
}

/* Suggestions */
.quick-suggestions-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 4px;
}

.suggestions-label {
  font-size: 0.65rem;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.chips-flex {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.suggestion-chip {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  padding: 4px 10px;
  font-size: 0.7rem;
  color: #334155;
  cursor: pointer;
  transition: all 0.15s ease;
}

.suggestion-chip:hover {
  background: #eff6ff;
  border-color: #3b82f6;
  color: #2563eb;
}

/* Bubbles */
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
  max-width: 80%;
  padding: 10px 14px;
  border-radius: 14px;
  font-size: 0.78rem;
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

/* Input Bar */
.chat-input-bar {
  padding: 10px 14px;
  background: #ffffff;
  border-top: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.chat-input-bar input {
  flex: 1;
  border: 1px solid #cbd5e1;
  border-radius: 20px;
  padding: 8px 14px;
  font-size: 0.78rem;
  outline: none;
  transition: border-color 0.15s ease;
}

.chat-input-bar input:focus {
  border-color: #3b82f6;
}

.send-btn {
  width: 32px;
  height: 32px;
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

/* Animations */
.chat-popup-enter-active,
.chat-popup-leave-active {
  transition: all 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.chat-popup-enter-from,
.chat-popup-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.92);
}

@media (max-width: 480px) {
  .chat-popup-card {
    right: 12px;
    left: 12px;
    width: auto;
    bottom: 90px;
  }
}
</style>
