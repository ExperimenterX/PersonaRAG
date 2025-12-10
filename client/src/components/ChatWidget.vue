<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'

const isOpen = ref(false)
const showInfo = ref(false)
const messages = ref([])
const userInput = ref('')
const isTyping = ref(false)
const chatBodyRef = ref(null)
const API_BASE_URL = 'http://127.0.0.1:8000'

function parseLinks(text) {
  if (!text) return text
  
  // Convert markdown links [text](url) to HTML
  let parsed = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
  
  // Convert plain URLs to clickable links (if not already part of markdown link)
  parsed = parsed.replace(/(?<!href="|">)(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>')
  
  return parsed
}

function getSupportColor(supportRate) {
  if (supportRate === null || supportRate === undefined) return 'gray'
  if (supportRate >= 0.6) return 'green'
  if (supportRate >= 0.3) return 'yellow'
  return 'red'
}

function toggleInfo() {
  showInfo.value = !showInfo.value
}

function toggleChat() {
  isOpen.value = !isOpen.value
  if (isOpen.value && messages.value.length === 0) {
    // initial welcome message
    messages.value.push({
      id: Date.now(),
      role: 'ai',
      text: "Hey! I'm Bhavani Shankar's personal AI assistant. Ask me anything about Bhavani Shankar's experience, projects, skills or interests. You can also ask for his hobbies if you'd like to know more about him! 😉",
      meta: { type: 'welcome', source: 'backend' }
    })
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (chatBodyRef.value) {
      chatBodyRef.value.scrollTop = chatBodyRef.value.scrollHeight
    }
  })
}

async function typeMessage(messageId, fullText, speed = 30) {
  const message = messages.value.find(m => m.id === messageId)
  if (!message) return
  message.text = ''
  for (let i = 0; i < fullText.length; i++) {
    message.text += fullText[i]
    scrollToBottom()
    await new Promise(resolve => setTimeout(resolve, speed))
  }
}

async function callBackendAPI(userText) {
  try {
    const response = await fetch(`${API_BASE_URL}/qa?q=${encodeURIComponent(userText)}`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const data = await response.json()
    return { 
      success: true, 
      answer: data.answer || 'No answer provided', 
      citations: data.citations || [],
      verification: data.verification || null
    }
  } catch (error) {
    console.error('API Error:', error)
    return { success: false, error: error.message }
  }
}

async function sendMessage() {
  const text = userInput.value.trim()
  if (!text || isTyping.value) return

  messages.value.push({
    id: Date.now(),
    role: 'user',
    text,
    meta: { source: 'user-input' }
  })
  userInput.value = ''
  scrollToBottom()

  isTyping.value = true
  const typingMessageId = Date.now() + 1
  messages.value.push({
    id: typingMessageId,
    role: 'ai',
    text: '●●●',
    isTypingIndicator: true
  })
  scrollToBottom()

  const result = await callBackendAPI(text)
  
  const typingIndex = messages.value.findIndex(m => m.id === typingMessageId)
  if (typingIndex !== -1) {
    messages.value.splice(typingIndex, 1)
  }
  isTyping.value = false

  const aiMessageId = Date.now() + 2
  if (result.success) {
    messages.value.push({
      id: aiMessageId,
      role: 'ai',
      text: '',
      meta: { 
        type: 'answer',
        verification: result.verification
      }
    })
    scrollToBottom()
    await typeMessage(aiMessageId, result.answer, 20)
  } else {
    const errorText = "Sorry, my personal assistant is busy taking care of other things right now. Please try again in a moment! 🤖"
    messages.value.push({
      id: aiMessageId,
      role: 'ai',
      text: '',
      meta: { type: 'error' }
    })
    scrollToBottom()
    await typeMessage(aiMessageId, errorText, 25)
  }
}

function handleEnter(event) {
  if (!event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

onMounted(() => {
  // chat starts closed; nothing else to do
})
</script>

<template>
  <!-- Floating button -->
  <div class="chat-launcher">
    <button class="chat-fab" @click="toggleChat">
      💬
    </button>

    <!-- Chat panel -->
    <transition name="fade-slide">
      <div v-if="isOpen" class="chat-panel">
        <header class="chat-header">
          <div class="chat-header-content">
            <div>
              <div class="chat-title">
                PersonaRAG – Personal AI
                <button class="info-icon" @click="toggleInfo" title="About PersonaRAG">ⓘ</button>
              </div>
              <div class="chat-subtitle">Ask about Bhavani Shankar's profile</div>
            </div>
          </div>
          <button class="chat-close" @click="toggleChat">×</button>
        </header>

        <!-- Info Modal -->
        <transition name="fade">
          <div v-if="showInfo" class="info-modal-overlay" @click="toggleInfo">
            <div class="info-modal" @click.stop>
              <div class="info-modal-header">
                <h3>About PersonaRAG</h3>
                <button class="info-modal-close" @click="toggleInfo">×</button>
              </div>
              <div class="info-modal-body">
                <p><strong>PersonaRAG</strong> is an AI-powered assistant using Retrieval-Augmented Generation (RAG) to answer questions about Bhavani Shankar's professional background.</p>
                
                <h4>How it works:</h4>
                <ul>
                  <li>🔍 <strong>Retrieval:</strong> Searches through resume data, documents, and certifications</li>
                  <li>🧠 <strong>Generation:</strong> Uses LLM to create natural, contextual answers</li>
                  <li>✅ <strong>Verification:</strong> Checks if the answer is supported by retrieved context</li>
                </ul>

                <h4>Support Rate Indicator:</h4>
                <div class="support-indicators">
                  <div class="support-item">
                    <span class="support-dot green"></span>
                    <span><strong>Green (≥60%):</strong> High confidence - answer strongly supported by data</span>
                  </div>
                  <div class="support-item">
                    <span class="support-dot yellow"></span>
                    <span><strong>Yellow (30-60%):</strong> Medium confidence - partial support</span>
                  </div>
                  <div class="support-item">
                    <span class="support-dot red"></span>
                    <span><strong>Red (&lt;30%):</strong> Low confidence - limited support</span>
                  </div>
                  <div class="support-item">
                    <span class="support-dot gray"></span>
                    <span><strong>Gray:</strong> No verification data available</span>
                  </div>
                </div>

                <p class="info-footer">💡 The colored dot next to each AI response shows how well the answer is supported by the retrieved documents. AI responses can sometimes be incorrect or incomplete, so please verify critical information independently.</p>
              </div>
            </div>
          </div>
        </transition>

        <main class="chat-body" ref="chatBodyRef">
          <div
            v-for="msg in messages"
            :key="msg.id"
            class="chat-message"
            :class="msg.role === 'user' ? 'chat-message-user' : 'chat-message-ai'"
          >
            <div class="chat-message-content">
              <div 
                class="chat-message-text"
                :class="{ 'typing-indicator': msg.isTypingIndicator }"
                v-html="parseLinks(msg.text)"
              >
              </div>
              <span 
                v-if="msg.role === 'ai' && msg.meta?.verification && !msg.isTypingIndicator"
                class="support-dot"
                :class="getSupportColor(msg.meta.verification.support_rate)"
                :title="`Support Rate: ${(msg.meta.verification.support_rate * 100).toFixed(0)}% (${msg.meta.verification.supported_sentences}/${msg.meta.verification.total_sentences} sentences)`"
              ></span>
            </div>
            <div v-if="msg.meta && !msg.isTypingIndicator" class="chat-meta">
              <span v-if="msg.role === 'ai'">AI • {{ msg.meta.intent || msg.meta.type }}</span>
              <span v-else>User</span>
            </div>
          </div>
        </main>

        <footer class="chat-footer">
          <textarea
            v-model="userInput"
            class="chat-input"
            placeholder="Type a message…"
            rows="2"
            @keydown.enter="handleEnter"
            :disabled="isTyping"
          ></textarea>
          <button 
            class="chat-send" 
            @click="sendMessage"
            :disabled="isTyping"
          >
            {{ isTyping ? '...' : 'Send' }}
          </button>
        </footer>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.chat-launcher {
  position: fixed;
  right: 1.5rem;
  bottom: 1.5rem;
  z-index: 9999;
}

/* Floating Action Button */
.chat-fab {
  width: 52px;
  height: 52px;
  border-radius: 999px;
  border: none;
  background: linear-gradient(135deg, #4f46e5, #818cf8);
  color: white;
  font-size: 1.5rem;
  box-shadow: 0 10px 25px rgba(31, 41, 55, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease, opacity 0.15s ease;
}

.chat-fab:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 30px rgba(31, 41, 55, 0.4);
}

/* Chat panel */
.chat-panel {
  position: absolute;
  bottom: 70px;
  right: 0;
  width: 420px;
  max-height: 600px;
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.4);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Header */
.chat-header {
  padding: 0.7rem 0.9rem;
  background: linear-gradient(135deg, #4673e5, #6366f1);
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.chat-title {
  font-size: 0.95rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.info-icon {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  font-size: 0.9rem;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
  padding: 0;
  line-height: 1;
}

.info-icon:hover {
  background: rgba(255, 255, 255, 0.3);
}

.chat-subtitle {
  font-size: 0.75rem;
  opacity: 0.9;
}

.chat-close {
  border: none;
  background: transparent;
  color: white;
  font-size: 1.2rem;
  cursor: pointer;
}

/* Info Modal */
.info-modal-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  border-radius: 16px;
}

.info-modal {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 360px;
  max-height: 80%;
  overflow-y: auto;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.info-modal-header {
  padding: 1rem 1.2rem;
  background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-radius: 12px 12px 0 0;
}

.info-modal-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.info-modal-close {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  font-size: 1.5rem;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  line-height: 1;
}

.info-modal-close:hover {
  background: rgba(255, 255, 255, 0.3);
}

.info-modal-body {
  padding: 1.2rem;
  font-size: 0.9rem;
  line-height: 1.6;
  color: #374151;
}

.info-modal-body h4 {
  margin: 1rem 0 0.5rem 0;
  font-size: 0.95rem;
  color: #1f2937;
  font-weight: 600;
}

.info-modal-body ul {
  margin: 0.5rem 0;
  padding-left: 1.2rem;
}

.info-modal-body li {
  margin-bottom: 0.4rem;
}

.support-indicators {
  margin: 0.8rem 0;
  padding: 0.8rem;
  background: #f9fafb;
  border-radius: 8px;
  border-left: 3px solid #4f46e5;
}

.support-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 0.6rem;
  font-size: 0.85rem;
}

.support-item:last-child {
  margin-bottom: 0;
}

.info-footer {
  margin-top: 1rem;
  padding: 0.8rem;
  background: #fef3c7;
  border-radius: 8px;
  font-size: 0.85rem;
  color: #78350f;
  border-left: 3px solid #f59e0b;
}

/* Body */
.chat-body {
  padding: 0.8rem;
  flex: 1;
  overflow-y: auto;
  background: #f9fafb;
  min-height: 400px;
}

.chat-message {
  margin-bottom: 0.6rem;
  max-width: 85%;
  display: flex;
  flex-direction: column;
}

.chat-message-ai {
  align-self: flex-start;
}

.chat-message-user {
  align-self: flex-end;
  margin-left: auto;
}

.chat-message-content {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
}

.chat-message-text {
  padding: 0.45rem 0.7rem;
  border-radius: 12px;
  font-size: 0.85rem;
  line-height: 1.35;
  flex: 1;
}

.chat-message-ai .chat-message-text {
  background: #eef2ff;
  color: #111827;
}

.chat-message-user .chat-message-text {
  background: #4f46e5;
  color: white;
}

/* Links in messages */
.chat-message-text :deep(a) {
  color: #3b82f6;
  text-decoration: underline;
  font-weight: 500;
  transition: color 0.2s;
}

.chat-message-text :deep(a):hover {
  color: #2563eb;
  text-decoration: underline;
}

.chat-message-user .chat-message-text :deep(a) {
  color: #fbbf24;
}

.chat-message-user .chat-message-text :deep(a):hover {
  color: #fde047;
}

/* Typing indicator animation */
.typing-indicator {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Support Rate Indicator */
.support-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 0.35rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  cursor: help;
}

.support-dot.green {
  background: #10b981;
}

.support-dot.yellow {
  background: #f59e0b;
}

.support-dot.red {
  background: #ef4444;
}

.support-dot.gray {
  background: #9ca3af;
}

.chat-meta {
  font-size: 0.7rem;
  margin-top: 0.15rem;
  opacity: 0.7;
}

/* Footer */
.chat-footer {
  padding: 0.55rem 0.6rem;
  border-top: 1px solid #e5e7eb;
  background: #ffffff;
  display: flex;
  gap: 0.4rem;
  align-items: flex-end;
}

.chat-input {
  flex: 1;
  resize: none;
  font-size: 0.85rem;
  border-radius: 10px;
  border: 1px solid #d1d5db;
  padding: 0.35rem 0.5rem;
  outline: none;
}

.chat-input:focus {
  border-color: #4f46e5;
  box-shadow: 0 0 0 1px rgba(79, 70, 229, 0.18);
}

.chat-input:disabled {
  background: #f3f4f6;
  cursor: not-allowed;
  opacity: 0.7;
}

.chat-send {
  border: none;
  border-radius: 999px;
  padding: 0.35rem 0.9rem;
  background: #4f46e5;
  color: white;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
}

.chat-send:disabled {
  background: #9ca3af;
  cursor: not-allowed;
  opacity: 0.7;
}

/* Animations */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}
.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
