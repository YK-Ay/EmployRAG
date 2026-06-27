<template>
  <div class="chat-wrapper">
    <!-- 知识库模式：会话侧边栏 -->
    <transition name="sidebar-slide">
      <div v-if="chatMode === 'knowledge' && sidebarOpen" class="session-sidebar">
        <div class="sidebar-header">
          <span class="sidebar-title">对话列表</span>
          <button class="sidebar-new-btn" @click="createNewSession" :disabled="!selectedCollection">
            <svg viewBox="0 0 16 16" fill="none"><line x1="8" y1="2" x2="8" y2="14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><line x1="2" y1="8" x2="14" y2="8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            新建
          </button>
        </div>
        <div class="session-list">
          <div v-if="sessions.length === 0" class="session-empty">暂无会话</div>
          <div
            v-for="s in sessions" :key="s.id"
            class="session-item" :class="{ active: currentSessionId === s.id }"
            @click="switchSession(s)"
          >
            <div class="session-item-title">{{ s.title }}</div>
            <div class="session-item-meta">{{ s.message_count }} 条 · {{ formatSessionTime(s.updated_at) }}</div>
            <button class="session-delete-btn" @click.stop="deleteSession(s.id)" title="删除会话">
              <svg viewBox="0 0 10 10" fill="none"><line x1="1" y1="1" x2="9" y2="9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><line x1="9" y1="1" x2="1" y2="9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            </button>
          </div>
        </div>
      </div>
    </transition>

    <div class="chat-main" :class="{ 'sidebar-expanded': chatMode === 'knowledge' && sidebarOpen }">
    <!-- Toolbar -->
    <div class="chat-toolbar">
      <div class="mode-tabs">
        <button v-if="chatMode === 'knowledge'" class="icon-btn sidebar-toggle-btn"
          :class="{ active: sidebarOpen }" @click="sidebarOpen = !sidebarOpen" title="会话列表">
          <svg viewBox="0 0 16 16" fill="none">
            <rect x="1" y="2" width="5" height="12" rx="1" stroke="currentColor" stroke-width="1.3"/>
            <line x1="9" y1="5" x2="15" y2="5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
            <line x1="9" y1="8" x2="15" y2="8" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
            <line x1="9" y1="11" x2="13" y2="11" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
          </svg>
        </button>
        <button v-for="m in modes" :key="m.value"
          class="mode-tab" :class="{ active: chatMode === m.value }"
          @click="chatMode = m.value">
          <el-icon><component :is="m.icon" /></el-icon>
          <span>{{ m.label }}</span>
          <span v-if="chatMode === m.value" class="mode-tab-glow" />
        </button>
      </div>
      <div class="toolbar-right">
        <template v-if="chatMode === 'knowledge'">
          <div class="collection-select-wrap">
            <el-icon class="col-icon"><data-analysis /></el-icon>
            <el-select v-model="selectedCollection" size="small" placeholder="选择知识库"
              style="width:180px" @change="clearMessages">
              <el-option v-for="col in collections" :key="col.name"
                :label="col.display_name || col.name" :value="col.name" />
            </el-select>
          </div>
          <span v-if="collections.length === 0" class="no-kb-hint">暂无知识库</span>
          <div class="kb-options">
            <el-tooltip content="开启后跳过 LLM 分类，直接使用多文档分组搜索" placement="bottom" :show-after="400">
              <button class="opt-pill" :class="{ active: forceMultiDoc }" @click="forceMultiDoc = !forceMultiDoc">
                <span class="opt-pill-dot" />
                <svg class="opt-pill-icon" viewBox="0 0 16 16" fill="none">
                  <rect x="1" y="3" width="6" height="4" rx="1" stroke="currentColor" stroke-width="1.3"/>
                  <rect x="9" y="3" width="6" height="4" rx="1" stroke="currentColor" stroke-width="1.3"/>
                  <rect x="1" y="9" width="6" height="4" rx="1" stroke="currentColor" stroke-width="1.3"/>
                  <rect x="9" y="9" width="6" height="4" rx="1" stroke="currentColor" stroke-width="1.3"/>
                </svg>
                <span>多文档</span>
                <span class="opt-pill-glow" />
              </button>
            </el-tooltip>

            <el-tooltip content="开启后使用关键词精确预过滤，适合错误码、型号等精确匹配场景" placement="bottom" :show-after="400">
              <button class="opt-pill" :class="{ active: keywordFilterEnabled }" @click="toggleKeywordFilter">
                <span class="opt-pill-dot" />
                <svg class="opt-pill-icon" viewBox="0 0 16 16" fill="none">
                  <circle cx="6.5" cy="6.5" r="4" stroke="currentColor" stroke-width="1.3"/>
                  <line x1="9.5" y1="9.5" x2="14" y2="14" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
                  <line x1="4.5" y1="6.5" x2="8.5" y2="6.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
                  <line x1="6.5" y1="4.5" x2="6.5" y2="8.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
                </svg>
                <span>关键词</span>
                <span class="opt-pill-glow" />
              </button>
            </el-tooltip>

            <transition name="kw-slide">
              <div v-if="keywordFilterEnabled" class="kw-input-wrap">
                <svg class="kw-input-icon" viewBox="0 0 16 16" fill="none">
                  <path d="M2 4h12M4 8h8M6 12h4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
                </svg>
                <input
                  v-model="keywordFilter"
                  class="kw-input"
                  placeholder="精确匹配词…"
                  @keydown.escape="toggleKeywordFilter"
                />
                <button v-if="keywordFilter" class="kw-clear" @click="keywordFilter = ''">
                  <svg viewBox="0 0 10 10" fill="none"><line x1="1" y1="1" x2="9" y2="9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><line x1="9" y1="1" x2="1" y2="9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
                </button>
              </div>
            </transition>
          </div>
        </template>
        <div class="mode-badge" :class="chatMode">
          {{ chatMode === 'general' ? '多 Agent' : 'RAG 检索' }}
        </div>
        <button class="icon-btn" @click="clearMessages" title="清空对话">
          <el-icon><delete /></el-icon>
        </button>
      </div>
    </div>

    <!-- Messages -->
    <div class="messages" ref="messagesContainer" @click="e => { if (e.target.tagName === 'IMG') openLightbox(e.target.src) }">
      <!-- Welcome screen -->
      <transition name="fade">
        <div v-if="messages.length === 0" class="welcome-screen">
          <div class="welcome-orb">
            <div class="orb-ring" />
            <div class="orb-ring orb-ring-2" />
            <el-icon class="orb-icon"><cpu /></el-icon>
          </div>
          <h2 class="welcome-title">{{ chatMode === 'knowledge' ? 'Knowledge Assistant' : 'AI Assistant' }}</h2>
          <p class="welcome-sub">{{ chatMode === 'knowledge' ? '基于企业知识库，智能检索 + Rerank 重排序' : '多工具智能体，支持邮件、搜索等工具调用' }}</p>
          <div class="suggestion-grid">
            <button v-for="s in suggestions[chatMode]" :key="s" class="suggestion-card" @click="useSuggestion(s)">
              <el-icon><arrow-right /></el-icon>
              <span>{{ s }}</span>
            </button>
          </div>
        </div>
      </transition>

      <!-- Message list -->
      <transition-group name="msg" tag="div">
        <div v-for="(msg, i) in messages" :key="i" :class="['msg-row', msg.role]">
          <div v-if="msg.role === 'assistant'" class="ai-avatar">
            <div class="ai-avatar-ring" />
            <div class="ai-avatar-bg" />
            <el-icon class="ai-avatar-icon"><cpu /></el-icon>
          </div>
          <div v-else class="user-avatar"><span>我</span></div>

          <div class="bubble-wrap">
            <div class="bubble" :class="msg.role">
              <div class="bubble-text" v-if="!msg.isHtml" style="white-space:pre-wrap">
                <img v-if="msg.queryImagePreview" :src="msg.queryImagePreview" style="max-width:120px;border-radius:6px;margin-bottom:4px;display:block" />
                {{ msg.content }}
              </div>
              <div class="bubble-text" v-else-if="msg.isHtml">
                <!-- 知识库流式：首字到达前在同一气泡内显示「思考中」波浪，避免单独第二条空对话框 -->
                <div v-if="msg._streamThinking" class="typing-bubble stream-thinking-inline">
                  <div class="wave-bar" /><div class="wave-bar" /><div class="wave-bar" />
                </div>
                <div v-else v-html="msg.content" />
              </div>

              <!-- Tools -->
              <div v-if="msg.tools_used?.length" class="meta-row">
                <el-icon style="font-size:10px"><tools /></el-icon>
                <span class="meta-label">Tools:</span>
                <span v-for="t in msg.tools_used" :key="t" class="tool-chip">{{ t }}</span>
              </div>

              <!-- Sources collapsible -->
              <div v-if="msg.sources?.length" class="sources-section">
                <button class="sources-toggle" @click="msg._showSources = !msg._showSources">
                  <el-icon><document /></el-icon>
                  <span>{{ uniqueFileNames(msg.sources).length }} 个来源</span>
                  <span class="sources-count">{{ msg.sources.length }} 切片</span>
                  <el-icon class="toggle-arrow" :class="{ open: msg._showSources }"><arrow-down /></el-icon>
                </button>
                <transition name="expand">
                  <div v-if="msg._showSources" class="sources-list">
                    <div v-for="(name, si) in uniqueFileNames(msg.sources)" :key="si" class="source-card">
                      <div class="source-dot" />
                      <span class="source-name">{{ name }}</span>
                    </div>
                  </div>
                </transition>
              </div>

              <!-- Confidence arc -->
              <div v-if="msg.confidence !== undefined && msg.confidence !== null && msg.role === 'assistant'" class="confidence-row">
                <svg class="conf-arc" viewBox="0 0 60 34" fill="none">
                  <path d="M5 30 A25 25 0 0 1 55 30" stroke="rgba(255,255,255,0.08)" stroke-width="5" stroke-linecap="round"/>
                  <path d="M5 30 A25 25 0 0 1 55 30"
                    :stroke="confColor(msg.confidence)" stroke-width="5" stroke-linecap="round"
                    :stroke-dasharray="`${msg.confidence * 78.5} 78.5`" style="transition:stroke-dasharray 1s ease"/>
                  <text x="30" y="30" text-anchor="middle" font-size="9" :fill="confColor(msg.confidence)" font-weight="700">
                    {{ Math.round(msg.confidence * 100) }}%
                  </text>
                </svg>
                <span class="conf-label">置信度</span>
              </div>
            </div>
            <div class="msg-time">{{ formatTime(msg.timestamp) }}</div>
          </div>
        </div>
      </transition-group>

      <!-- Typing indicator（知识库流式已在消息列表里插入 assistant 气泡，不再显示下方占位，避免双气泡） -->
      <transition name="fade">
        <div v-if="loading && chatMode !== 'knowledge'" class="msg-row assistant">
          <div class="ai-avatar">
            <div class="ai-avatar-ring pulsing" />
            <div class="ai-avatar-bg" />
            <el-icon class="ai-avatar-icon"><cpu /></el-icon>
          </div>
          <div class="bubble-wrap">
            <div class="bubble assistant typing-bubble">
              <div class="wave-bar" /><div class="wave-bar" /><div class="wave-bar" />
            </div>
          </div>
        </div>
      </transition>
    </div>

    <!-- Input area -->
    <div class="input-area" :class="{ focused: inputFocused }">
      <!-- 多模态图片预览 -->
      <div v-if="queryImagePreview" class="query-image-preview">
        <img :src="queryImagePreview" class="query-img-thumb" />
        <button class="query-img-remove" @click="clearQueryImage" title="移除图片">
          <svg viewBox="0 0 10 10" fill="none"><line x1="1" y1="1" x2="9" y2="9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><line x1="9" y1="1" x2="1" y2="9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
        </button>
      </div>
      <div class="input-wrap">
        <el-input v-model="inputMessage" type="textarea"
          :autosize="{ minRows: 1, maxRows: 5 }"
          placeholder="输入消息...（Enter 发送，Shift+Enter 换行）"
          :disabled="loading"
          @keydown.enter.exact.prevent="sendMessage"
          @focus="inputFocused = true" @blur="inputFocused = false"
          resize="none" />
        <span class="char-count" :class="{ warn: inputMessage.length > 800 }">{{ inputMessage.length }}</span>
      </div>
      <!-- 多模态图片上传按钮（仅多模态知识库显示） -->
      <template v-if="chatMode === 'knowledge' && isMultimodalKb">
        <input ref="queryImageInput" type="file" accept="image/*" style="display:none" @change="onQueryImageChange" />
        <button class="icon-btn img-upload-btn" :class="{ active: !!queryImagePreview }" @click="queryImageInput.click()" title="上传查询图片（多模态知识库）">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
            <rect x="3" y="3" width="18" height="18" rx="3"/>
            <circle cx="8.5" cy="8.5" r="1.5"/>
            <polyline points="21 15 16 10 5 21"/>
          </svg>
        </button>
      </template>
      <button class="send-btn" :class="{ loading, disabled: !canSend }" :disabled="!canSend" @click="sendMessage">
        <transition name="icon-swap" mode="out-in">
          <span v-if="!loading" key="send" class="send-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="22" y1="2" x2="11" y2="13"/>
              <polygon points="22 2 15 22 11 13 2 9 22 2"/>
            </svg>
          </span>
          <span v-else key="spin" class="spin-ring" />
        </transition>
      </button>
    </div>
  </div><!-- end chat-main -->
  </div><!-- end chat-wrapper -->

  <!-- Lightbox -->
  <teleport to="body">
    <transition name="lightbox-fade">
      <div v-if="lightbox.show" class="lightbox-overlay" @click="lightbox.show = false">
        <button class="lightbox-close" @click="lightbox.show = false">
          <svg viewBox="0 0 16 16" fill="none"><line x1="2" y1="2" x2="14" y2="14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="14" y1="2" x2="2" y2="14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
        </button>
        <img :src="lightbox.src" class="lightbox-img" @click.stop />
      </div>
    </transition>
  </teleport>
</template>

<script setup>
import { ref, computed, nextTick, watch, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { apiService } from '../services/api'
import { docApi } from '../services/docApi'
import axios from 'axios'
import { md } from '../utils/markdown.js'

const API = '/api/v1'
const props = defineProps({ model: { type: String, default: 'qwen-turbo' } })

const chatMode = ref('general')
const selectedCollection = ref('')
const collections = ref([])
const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const inputFocused = ref(false)
const messagesContainer = ref(null)

// knowledge 模式选项
const forceMultiDoc = ref(false)
const keywordFilterEnabled = ref(false)
const keywordFilter = ref('')
const toggleKeywordFilter = () => {
  keywordFilterEnabled.value = !keywordFilterEnabled.value
  if (!keywordFilterEnabled.value) keywordFilter.value = ''
}

// 多模态查询图片
const queryImage = ref(null)      // File 对象
const queryImagePreview = ref('') // base64 预览
const queryImageInput = ref(null)
const onQueryImageChange = (e) => {
  const file = e.target.files[0]
  if (!file) return
  queryImage.value = file
  const reader = new FileReader()
  reader.onload = (ev) => { queryImagePreview.value = ev.target.result }
  reader.readAsDataURL(file)
}
const clearQueryImage = () => {
  queryImage.value = null
  queryImagePreview.value = ''
  if (queryImageInput.value) queryImageInput.value.value = ''
}

// 压缩图片并返回 base64（不含 data:xxx;base64, 前缀）
const compressImageToBase64 = (file, maxSize = 800, quality = 0.7) => {
  return new Promise((resolve) => {
    const img = new Image()
    const url = URL.createObjectURL(file)
    img.onload = () => {
      URL.revokeObjectURL(url)
      let { width, height } = img
      if (width > maxSize || height > maxSize) {
        if (width > height) { height = Math.round(height * maxSize / width); width = maxSize }
        else { width = Math.round(width * maxSize / height); height = maxSize }
      }
      const canvas = document.createElement('canvas')
      canvas.width = width; canvas.height = height
      canvas.getContext('2d').drawImage(img, 0, 0, width, height)
      const dataUrl = canvas.toDataURL('image/jpeg', quality)
      resolve(dataUrl.split(',')[1] || null)
    }
    img.onerror = () => { URL.revokeObjectURL(url); resolve(null) }
    img.src = url
  })
}

// 会话管理
const sidebarOpen = ref(true)
const sessions = ref([])
const currentSessionId = ref('')

// SSE 流请求的 AbortController（组件卸载时自动中断）
let currentAbortController = null

// 消息唯一计数器（用于 v-for key 避免用数组索引）
let msgIdCounter = 0

// Lightbox
const lightbox = ref({ show: false, src: '' })
const openLightbox = (src) => { lightbox.value = { show: true, src } }

// 键盘关闭 lightbox + 组件卸载时清理
const onKeydown = (e) => { if (e.key === 'Escape') lightbox.value.show = false }
onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  if (currentAbortController) currentAbortController.abort()
})

const formatSessionTime = (ts) => {
  if (!ts) return ''
  const d = new Date(ts)
  const now = new Date()
  const diff = now - d
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  return d.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
}

// 图片 URL 缓存，key=placeholder，value={url, expiresAt}
// 使用 sessionStorage 持久化到标签页生命周期，关闭即清空
const IMAGE_CACHE_TTL = 50 * 60 * 1000 // 50分钟，比 OSS 预签名 1小时短

const getCachedUrl = (ph) => {
  try {
    const raw = sessionStorage.getItem(`img_cache:${ph}`)
    if (!raw) return null
    const { url, expiresAt } = JSON.parse(raw)
    if (Date.now() > expiresAt) { sessionStorage.removeItem(`img_cache:${ph}`); return null }
    return url
  } catch { return null }
}

const setCachedUrl = (ph, url) => {
  try {
    sessionStorage.setItem(`img_cache:${ph}`, JSON.stringify({ url, expiresAt: Date.now() + IMAGE_CACHE_TTL }))
  } catch {} // sessionStorage 满了也不影响功能
}

const loadSessions = async () => {
  if (!selectedCollection.value) return
  try {
    const res = await docApi.listSessions(selectedCollection.value)
    sessions.value = res.data.data?.sessions || []
  } catch (e) {
    console.warn('加载会话列表失败:', e)
  }
}

const createNewSession = async () => {
  if (!selectedCollection.value) return
  try {
    const res = await docApi.createSession(selectedCollection.value)
    const session = res.data.data
    sessions.value.unshift(session)
    await switchSession(session)
  } catch (e) {
    ElMessage.error('创建会话失败')
  }
}

const switchSession = async (session) => {
  if (currentSessionId.value === session.id) return
  currentSessionId.value = session.id
  messages.value = []
  // 加载历史消息
  try {
    const res = await docApi.getSessionMessages(session.id)
    const histMsgs = res.data.data?.messages || []
    if (!histMsgs.length) return

    // 收集所有占位符，批量 resolve（优先读缓存，只请求后端未缓存的）
    const allPhs = []
    for (const m of histMsgs) {
      if (m.image_placeholders?.length) allPhs.push(...m.image_placeholders)
    }
    let urlMap = {}
    if (allPhs.length) {
      const uniquePhs = [...new Set(allPhs)]
      const missedPhs = []
      for (const ph of uniquePhs) {
        const cached = getCachedUrl(ph)
        if (cached) urlMap[ph] = cached
        else missedPhs.push(ph)
      }
      if (missedPhs.length) {
        try {
          const rr = await docApi.resolveImages(missedPhs)
          const fresh = rr.data.data || {}
          for (const [ph, url] of Object.entries(fresh)) {
            urlMap[ph] = url
            setCachedUrl(ph, url)
          }
        } catch {}
      }
    }

    // 批量 resolve 用户查询图片（query_image_oss_key → 预签名 URL）
    const queryImgOssKeys = histMsgs
      .filter(m => m.role === 'user' && m.query_image_oss_key)
      .map(m => m.query_image_oss_key)
    let queryImgUrlMap = {}
    if (queryImgOssKeys.length) {
      try {
        const rr = await docApi.resolveQueryImages(queryImgOssKeys)
        queryImgUrlMap = rr.data.data || {}
      } catch {}
    }

    for (const m of histMsgs) {
      let content = m.content
      // 替换占位符为图片 markdown
      if (m.image_placeholders?.length) {
        for (const ph of m.image_placeholders) {
          if (urlMap[ph]) content = content.split(ph).join(`\n![image](${urlMap[ph]})\n`)
        }
      }
      // 用户查询图片拼在消息内容前
      let queryImgHtml = ''
      if (m.role === 'user' && m.query_image_oss_key && queryImgUrlMap[m.query_image_oss_key]) {
        queryImgHtml = `<img src="${queryImgUrlMap[m.query_image_oss_key]}" style="max-width:120px;border-radius:6px;margin-bottom:4px;display:block" />`
      }
      messages.value.push({
        role: m.role,
        isHtml: m.role === 'assistant' || !!queryImgHtml,
        content: m.role === 'assistant' ? md.render(content) : (queryImgHtml + content),
        confidence: m.confidence,
        sources: m.sources || [],
        _showSources: false,
        timestamp: new Date(m.created_at),
        _id: ++msgIdCounter,
      })
    }
    scrollToBottom()
  } catch (e) {
    console.warn('加载历史消息失败:', e)
  }
}

const deleteSession = async (sessionId) => {
  try {
    await docApi.deleteSession(sessionId)
    sessions.value = sessions.value.filter(s => s.id !== sessionId)
    if (currentSessionId.value === sessionId) {
      currentSessionId.value = ''
      messages.value = []
    }
    ElMessage.success('会话已删除')
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

const modes = [
  { value: 'general',   label: '普通对话', icon: 'Cpu' },
  { value: 'knowledge', label: '知识库',   icon: 'Document' },
]
const suggestions = {
  general:   ['你能做什么？', '帮我搜索最新资讯', '发一封邮件'],
  knowledge: ['你能做什么？', '鸡蛋可以用来做什么菜？', '鱼可以用来做什么菜？'],
}

const canSend = computed(() =>
  inputMessage.value.trim() && !loading.value &&
  !(chatMode.value === 'knowledge' && !selectedCollection.value)
)

// 当前选中知识库是否为多模态
const isMultimodalKb = computed(() => {
  const col = collections.value.find(c => c.name === selectedCollection.value)
  return col?.kb_type === 'multimodal'
})
const confColor = (c) => c > 0.7 ? '#2dd4a0' : c > 0.4 ? '#f5c842' : '#f06b6b'
const scrollToBottom = () => nextTick(() => {
  if (messagesContainer.value) messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
})
const useSuggestion = (text) => { inputMessage.value = text; sendMessage() }

/** 与后端 _sanitize_image_placeholders 一致：仅保留 image_map 中存在的占位符 */
const sanitizeImagePlaceholders = (text, imageMap) => {
  if (!text) return ''
  if (!imageMap || !Object.keys(imageMap).length) return text
  const valid = new Set(Object.keys(imageMap))
  return text.replace(/<<IMAGE:[0-9a-fA-F]{8}>>/g, (m) => (valid.has(m) ? m : ''))
}

const toMarkdownWithImages = (raw, imageMap) => {
  const sanitized = sanitizeImagePlaceholders(raw, imageMap)
  let s = sanitized
  if (imageMap) {
    Object.entries(imageMap).forEach(([ph, url]) => { s = s.split(ph).join(`\n![image](${url})\n`) })
  }
  return s
}

let streamRenderRaf = null
/** 通过 RAF 合并渲染；必须从 messages[idx] 读写字段以保证 Vue 追踪到响应式对象 */
const scheduleStreamRender = (assistantIdx, getRawState) => {
  if (streamRenderRaf) return
  streamRenderRaf = requestAnimationFrame(() => {
    streamRenderRaf = null
    const row = messages.value[assistantIdx]
    if (!row || row.role !== 'assistant') return
    const { streamRaw, imageMap } = getRawState()
    row.content = md.render(toMarkdownWithImages(streamRaw, imageMap))
    scrollToBottom()
  })
}

const sendMessage = async () => {
  const text = inputMessage.value.trim()
  if (!canSend.value || !text) return
  // 中止上一次未完成的流请求（防止卸载后继续更新 DOM）
  if (currentAbortController) currentAbortController.abort()
  currentAbortController = new AbortController()
  const abortSignal = currentAbortController.signal

  // 用户消息：若有查询图片，把预览 URL 一起存入消息对象用于实时显示
  const userMsg = { role: 'user', content: text, timestamp: new Date(), _id: ++msgIdCounter }
  if (queryImagePreview.value) userMsg.queryImagePreview = queryImagePreview.value
  messages.value.push(userMsg)
  inputMessage.value = ''
  loading.value = true
  scrollToBottom()
  try {
    if (chatMode.value === 'knowledge') {
      // 多模态：图片压缩后转 base64（最大 800px，质量 0.7，减小传输体积）
      let queryImageBase64 = null
      if (queryImage.value) {
        queryImageBase64 = await compressImageToBase64(queryImage.value, 800, 0.7)
      }
      messages.value.push({
        role: 'assistant', isHtml: true, content: '',
        _streamThinking: true,
        confidence: null, sources: [], _showSources: false, timestamp: new Date(),
        _id: ++msgIdCounter,
      })
      const assistantIdx = messages.value.length - 1
      let streamRaw = ''
      let imageMap = {}
      const rawState = () => ({ streamRaw, imageMap })
      await apiService.knowledgeQueryStream(
        {
          query: text,
          session_id: currentSessionId.value || 'default',
          model: props.model,
          collection: selectedCollection.value || null,
          force_multi_doc: forceMultiDoc.value || null,
          keyword_filter: (keywordFilterEnabled.value && keywordFilter.value) ? keywordFilter.value : null,
          query_image: queryImageBase64,
        },
        {
          onMeta: (m) => {
            imageMap = m.image_map || {}
            const row = messages.value[assistantIdx]
            if (row) row.sources = [...(m.sources || [])]
          },
          onDelta: (d) => {
            streamRaw += d.text || ''
            const row = messages.value[assistantIdx]
            if (row && row._streamThinking && streamRaw.length > 0) {
              row._streamThinking = false
            }
            scheduleStreamRender(assistantIdx, rawState)
          },
          onDone: (d) => {
            if (streamRenderRaf) {
              cancelAnimationFrame(streamRenderRaf)
              streamRenderRaf = null
            }
            streamRaw = d.answer != null ? d.answer : streamRaw
            imageMap = d.image_map || imageMap
            const row = messages.value[assistantIdx]
            if (row) {
              row._streamThinking = false
              row.confidence = d.confidence
              row.sources = d.sources?.length ? [...d.sources] : row.sources
              row.content = md.render(toMarkdownWithImages(streamRaw, imageMap))
            }
          },
          onError: (err) => { throw err },
        },
        abortSignal,
      )
      clearQueryImage()
    } else {
      const apiMsgs = messages.value.map(m => ({ role: m.role, content: m.content }))
      const res = await apiService.chat(apiMsgs, props.model)
      const last = res.messages?.[res.messages.length - 1]
      const toolsUsed = res.usage?.tools_used || []
      messages.value.push({
        role: 'assistant', isHtml: true,
        content: md.render(last?.content || '抱歉，未收到有效回复。'),
        tools_used: toolsUsed, timestamp: new Date(),
      })
      if (toolsUsed.length) ElMessage.success(`调用工具: ${toolsUsed.join(', ')}`)
    }
  } catch (e) {
    console.error(e); ElMessage.error('发送失败')
    if (chatMode.value === 'knowledge') {
      const last = messages.value[messages.value.length - 1]
      if (last?.role === 'assistant') {
        last._streamThinking = false
        last.isHtml = false
        last.content = '抱歉，发生错误，请稍后重试。'
      } else {
        messages.value.push({ role: 'assistant', content: '抱歉，发生错误，请稍后重试。', timestamp: new Date() })
      }
    } else {
      messages.value.push({ role: 'assistant', content: '抱歉，发生错误，请稍后重试。', timestamp: new Date() })
    }
  } finally { loading.value = false; currentAbortController = null; scrollToBottom() }
}

const clearMessages = () => { messages.value = []; currentSessionId.value = '' }
watch(chatMode, () => { messages.value = []; currentSessionId.value = '' })
watch(selectedCollection, async (val) => {
  messages.value = []
  currentSessionId.value = ''
  clearQueryImage()
  if (val) await loadSessions()
})
const formatTime = (t) => new Date(t).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
const uniqueFileNames = (sources) => {
  const seen = new Set()
  return sources.reduce((acc, s) => {
    const name = s.file_name || s.title || s.id || '未知来源'
    if (!seen.has(name)) { seen.add(name); acc.push(name) }
    return acc
  }, [])
}

onMounted(async () => {
  try {
    const { data } = await axios.get(`${API}/admin/collections`)
    collections.value = data.data?.collections || []
    if (collections.value.length > 0) {
      selectedCollection.value = collections.value[0].name
      await loadSessions()
    }
  } catch {}
})
defineExpose({ clearMessages })
</script>

<style scoped>
/* ── Layout ── */
.chat-wrapper {
  display: flex; flex-direction: row;
  height: calc(100vh - 100px);
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}
.chat-main {
  display: flex; flex-direction: column; flex: 1; min-width: 0;
}

/* ── Session Sidebar ── */
.session-sidebar {
  width: 200px; flex-shrink: 0;
  display: flex; flex-direction: column;
  background: var(--bg-elevated);
  border-right: 1px solid var(--border);
}
.sidebar-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 10px;
  border-bottom: 1px solid var(--border);
}
.sidebar-title { font-size: 11px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }
.sidebar-new-btn {
  display: flex; align-items: center; gap: 4px;
  padding: 3px 8px; border-radius: var(--radius-sm); border: none; cursor: pointer;
  font-size: 11px; font-weight: 500; color: var(--blue);
  background: var(--blue-bg);
}
.sidebar-new-btn:hover { background: #dbeafe; }
.sidebar-new-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.sidebar-new-btn svg { width: 10px; height: 10px; }
.session-list { flex: 1; overflow-y: auto; padding: 4px 6px; }
.session-empty { font-size: 11px; color: var(--text-muted); text-align: center; padding: 20px 0; }
.session-item {
  padding: 8px 10px; border-radius: var(--radius-sm); cursor: pointer;
  transition: background 0.1s;
  position: relative;
}
.session-item:hover { background: var(--bg-elevated); }
.session-item.active { background: var(--blue-bg); }
.session-item-title { font-size: 12px; font-weight: 500; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.session-item-meta { font-size: 10px; color: var(--text-muted); margin-top: 2px; }
.session-delete-btn {
  position: absolute; right: 6px; top: 50%; transform: translateY(-50%);
  width: 18px; height: 18px; border-radius: 4px; border: none; cursor: pointer;
  background: transparent; color: var(--text-muted);
  opacity: 0; transition: opacity 0.1s;
  display: flex; align-items: center; justify-content: center; font-size: 13px;
}
.session-item:hover .session-delete-btn { opacity: 1; }
.session-delete-btn:hover { color: var(--red); }
.sidebar-toggle-btn.active { color: var(--blue); }

/* sidebar slide transition */
.sidebar-slide-enter-active { transition: width 0.2s ease, opacity 0.15s; }
.sidebar-slide-leave-active { transition: width 0.15s ease, opacity 0.1s; }
.sidebar-slide-enter-from { width: 0; opacity: 0; }
.sidebar-slide-leave-to { width: 0; opacity: 0; }

/* ── Toolbar ── */
.chat-toolbar {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.mode-tabs { display: flex; gap: 2px; }
.mode-tab {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 12px; border-radius: var(--radius-sm); border: none; cursor: pointer;
  font-size: 13px; font-weight: 500; color: var(--text-muted);
  background: transparent; transition: all 0.15s;
}
.mode-tab:hover { color: var(--text-primary); background: var(--bg-elevated); }
.mode-tab.active { color: var(--blue); background: var(--blue-bg); }
.toolbar-right { display: flex; align-items: center; gap: 8px; }
.collection-select-wrap { display: flex; align-items: center; gap: 6px; }
.col-icon { color: var(--text-muted); font-size: 14px; }
.no-kb-hint { font-size: 11px; color: var(--red); }
.kb-options { display: flex; align-items: center; gap: 6px; }

/* opt-pill */
.opt-pill {
  padding: 4px 10px; border-radius: 99px; border: none; cursor: pointer;
  font-size: 11px; font-weight: 500;
  color: var(--text-muted);
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  transition: all 0.15s;
}
.opt-pill:hover { color: var(--text-primary); }
.opt-pill.active {
  color: var(--blue); background: var(--blue-bg);
  border-color: #bfdbfe;
}

/* keyword input */
.kw-input-wrap {
  display: flex; align-items: center; gap: 6px;
  padding: 3px 8px; border-radius: 99px;
  background: var(--blue-bg);
  border: 1px solid #bfdbfe;
}
.kw-input {
  border: none; outline: none; background: transparent;
  font-size: 11px; color: var(--text-primary); width: 120px; font-family: inherit;
}
.kw-input::placeholder { color: var(--text-muted); font-size: 11px; }
.kw-clear { background: none; border: none; cursor: pointer; color: var(--text-muted); font-size: 13px; padding: 0; }
.kw-clear:hover { color: var(--red); }
.img-upload-btn { color: var(--text-muted); }
.img-upload-btn.active { color: var(--blue); }

/* kw-slide transition */
.kw-slide-enter-active { transition: all 0.2s ease; }
.kw-slide-leave-active { transition: all 0.15s ease; }
.kw-slide-enter-from { opacity: 0; transform: translateX(-4px); }
.kw-slide-leave-to { opacity: 0; transform: translateX(-4px); }

.mode-badge {
  font-size: 10px; font-weight: 600; padding: 3px 8px; border-radius: 99px;
  text-transform: uppercase; letter-spacing: 0.5px;
}
.mode-badge.general { background: var(--bg-elevated); color: var(--text-muted); }
.mode-badge.knowledge { background: var(--green-bg); color: var(--green); }

.icon-btn {
  width: 30px; height: 30px; border-radius: var(--radius-sm); border: none; cursor: pointer;
  background: transparent; color: var(--text-muted);
  display: flex; align-items: center; justify-content: center; font-size: 14px;
}
.icon-btn:hover { background: var(--bg-elevated); color: var(--text-primary); }

/* ── Messages ── */
.messages {
  flex: 1; overflow-y: auto; padding: 20px 16px;
  display: flex; flex-direction: column; gap: 0;
}

/* Welcome screen */
.welcome-screen {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: 40px 20px; text-align: center;
}
.welcome-icon {
  width: 48px; height: 48px; border-radius: 50%;
  background: var(--blue-bg); color: var(--blue);
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; margin-bottom: 16px;
}
.welcome-title { font-size: 20px; font-weight: 700; color: var(--text-primary); margin-bottom: 6px; }
.welcome-sub { font-size: 13px; color: var(--text-muted); margin-bottom: 24px; max-width: 340px; }
.suggestion-grid { display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; }
.suggestion-card {
  padding: 8px 14px; border-radius: var(--radius-sm); cursor: pointer;
  background: var(--bg-elevated); border: 1px solid var(--border-light);
  color: var(--text-secondary); font-size: 12px;
  transition: all 0.1s;
}
.suggestion-card:hover { background: var(--blue-bg); border-color: #bfdbfe; color: var(--blue); }

/* Message rows */
.msg-row { display: flex; gap: 10px; margin-bottom: 16px; align-items: flex-start; }
.msg-row.user { flex-direction: row-reverse; }

.ai-avatar {
  width: 28px; height: 28px; border-radius: 50%; flex-shrink: 0;
  background: var(--blue-bg); color: var(--blue);
  display: flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: 700;
}
.user-avatar {
  width: 28px; height: 28px; border-radius: 50%; flex-shrink: 0;
  background: var(--blue); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: 700;
}

/* Bubble wrap */
.bubble-wrap { max-width: 70%; display: flex; flex-direction: column; }
.msg-row.user .bubble-wrap { align-items: flex-end; }

/* Bubbles */
.bubble {
  border-radius: var(--radius-md); padding: 10px 14px;
  word-break: break-word;
}
.bubble.assistant {
  background: var(--bg-elevated);
  border: 1px solid var(--border-light);
}
.bubble.user {
  background: var(--blue);
  color: #fff;
}

/* Bubble text / markdown */
.bubble-text { font-size: 14px; line-height: 1.6; color: var(--text-primary); }
.bubble.user .bubble-text { color: #fff; }
.bubble-text :deep(p) { margin: 4px 0; }
.bubble-text :deep(h1),.bubble-text :deep(h2),.bubble-text :deep(h3) { margin: 8px 0 4px; font-weight: 600; }
.bubble-text :deep(h1) { font-size: 16px; } .bubble-text :deep(h2) { font-size: 15px; } .bubble-text :deep(h3) { font-size: 14px; }
.bubble-text :deep(ul),.bubble-text :deep(ol) { padding-left: 18px; margin: 4px 0; }
.bubble-text :deep(li) { margin: 2px 0; }
.bubble-text :deep(code) { background: rgba(37,99,235,0.08); border-radius: 3px; padding: 1px 4px; font-size: 12px; color: var(--blue); font-family: 'SF Mono', monospace; }
.bubble-text :deep(pre) { background: #f0f1f3; border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 10px; overflow-x: auto; margin: 6px 0; }
.bubble-text :deep(pre code) { background: none; color: var(--text-primary); padding: 0; }
.bubble-text :deep(blockquote) { border-left: 2px solid var(--border); margin: 4px 0; padding: 2px 10px; color: var(--text-secondary); }
.bubble-text :deep(table) { border-collapse: collapse; width: 100%; margin: 6px 0; font-size: 13px; }
.bubble-text :deep(th),.bubble-text :deep(td) { border: 1px solid var(--border); padding: 4px 8px; }
.bubble-text :deep(th) { background: var(--bg-elevated); font-weight: 600; }
.bubble-text :deep(a) { color: var(--blue); text-decoration: none; }
.bubble-text :deep(a:hover) { text-decoration: underline; }
.bubble-text :deep(img) { max-width: 100%; max-height: 280px; border-radius: 8px; margin: 6px 0; display: block; border: 1px solid var(--border); }
.bubble.user .bubble-text :deep(code) { background: rgba(255,255,255,0.15); color: #fff; }

/* Meta row (tools) */
.meta-row {
  display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
  margin-top: 6px; padding-top: 6px; border-top: 1px solid var(--border);
}
.meta-label { font-size: 10px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.3px; }
.tool-chip { font-size: 10px; font-weight: 600; padding: 2px 6px; border-radius: 3px; background: var(--yellow-bg); color: var(--yellow); }

/* Sources */
.sources-section { margin-top: 6px; padding-top: 6px; border-top: 1px solid var(--border); }
.sources-toggle {
  display: flex; align-items: center; gap: 6px;
  background: none; border: none; cursor: pointer; padding: 0;
  color: var(--text-muted); font-size: 12px;
}
.sources-toggle:hover { color: var(--blue); }
.sources-count { font-size: 10px; padding: 1px 5px; border-radius: 3px; background: var(--bg-elevated); color: var(--text-muted); }
.sources-list { margin-top: 6px; display: flex; flex-direction: column; gap: 3px; }
.source-card { padding: 5px 8px; border-radius: var(--radius-sm); background: var(--blue-bg); }
.source-name { font-size: 12px; color: var(--blue); }

/* Confidence */
.confidence-row { margin-top: 6px; padding-top: 6px; border-top: 1px solid var(--border); }
.conf-label { font-size: 11px; color: var(--text-muted); }

/* Msg time */
.msg-time { font-size: 10px; color: var(--text-muted); margin-top: 4px; padding: 0 4px; }

/* Typing */
.typing-bubble { display: flex; align-items: flex-end; gap: 3px; padding: 12px 14px; min-width: 50px; }
.stream-thinking-inline { padding: 10px 12px; min-width: 44px; margin: -2px 0; }
.wave-bar { width: 3px; border-radius: 99px; background: var(--blue); animation: wave 1.2s ease-in-out infinite; }
.wave-bar:nth-child(1) { height: 8px; animation-delay: 0s; }
.wave-bar:nth-child(2) { height: 14px; animation-delay: 0.15s; }
.wave-bar:nth-child(3) { height: 8px; animation-delay: 0.3s; }
@keyframes wave { 0%,100% { transform: scaleY(0.5); opacity: 0.4; } 50% { transform: scaleY(1); opacity: 1; } }

/* ── Input area ── */
.input-area {
  display: flex; gap: 8px; padding: 12px 14px; align-items: flex-end;
  border-top: 1px solid var(--border);
  flex-shrink: 0;
}
.input-wrap { flex: 1; position: relative; }
.input-wrap :deep(.el-textarea__inner) { border-radius: var(--radius-md) !important; resize: none !important; padding-right: 40px !important; }
.char-count { position: absolute; bottom: 6px; right: 8px; font-size: 10px; color: var(--text-muted); pointer-events: none; }
.char-count.warn { color: var(--red); }

.query-image-preview { display: flex; align-items: center; gap: 6px; padding: 4px 12px 0; }
.query-img-thumb { width: 40px; height: 40px; object-fit: cover; border-radius: var(--radius-sm); border: 1px solid var(--border); }
.query-img-remove { width: 18px; height: 18px; border-radius: 50%; border: none; cursor: pointer; background: var(--red-bg); color: var(--red); display: flex; align-items: center; justify-content: center; font-size: 12px; padding: 0; }

/* Send button */
.send-btn {
  width: 40px; height: 40px; border-radius: 50%; border: none; cursor: pointer;
  background: var(--blue); color: #fff;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; transition: background 0.15s;
}
.send-btn:hover:not(.disabled) { background: var(--blue-hover); }
.send-btn.disabled { opacity: 0.3; cursor: not-allowed; }
.send-icon { display: flex; align-items: center; justify-content: center; }
.spin-ring { width: 16px; height: 16px; border-radius: 50%; border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff; animation: spin 0.7s linear infinite; display: block; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Transitions ── */
.fade-enter-active,.fade-leave-active { transition: opacity 0.25s; }
.fade-enter-from,.fade-leave-to { opacity: 0; }
.msg-enter-active { transition: all 0.3s ease; }
.msg-enter-from { opacity: 0; transform: translateY(12px); }
.msg-leave-active { transition: all 0.2s ease; }
.msg-leave-to { opacity: 0; }

/* Lightbox */
.lightbox-overlay {
  position: fixed; inset: 0; z-index: 9999;
  background: rgba(0,0,0,0.6);
  display: flex; align-items: center; justify-content: center;
  cursor: zoom-out;
}
.lightbox-img { max-width: 90vw; max-height: 90vh; object-fit: contain; border-radius: var(--radius-md); cursor: default; }
.lightbox-close {
  position: fixed; top: 20px; right: 24px;
  width: 32px; height: 32px; border-radius: 50%;
  background: rgba(255,255,255,0.15); border: none;
  color: #fff; font-size: 18px; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}
.lightbox-fade-enter-active, .lightbox-fade-leave-active { transition: opacity 0.2s ease; }
.lightbox-fade-enter-from, .lightbox-fade-leave-to { opacity: 0; }
</style>
