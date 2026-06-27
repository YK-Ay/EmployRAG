<template>
  <div class="dashboard">
    <!-- Welcome + Search -->
    <div class="hero">
      <h1 class="hero-title">知识库问答系统</h1>
      <p class="hero-sub">基于 RAG 技术的企业智能检索与对话平台</p>
      <div class="search-bar" :class="{ focused: searchFocused }">
        <el-icon class="search-icon"><search /></el-icon>
        <input
          v-model="searchQuery"
          class="search-input"
          placeholder="输入问题，检索知识库..."
          @focus="searchFocused = true"
          @blur="searchFocused = false"
          @keydown.enter="handleSearch"
        />
        <button class="search-submit" @click="handleSearch" :disabled="searching">
          <span v-if="!searching">检索</span>
          <span v-else class="searching-dots"><span/><span/><span/></span>
        </button>
      </div>
      <transition name="slide-up">
        <div v-if="aiAnswer" class="ai-result">
          <div class="ai-result-header">
            <span class="ai-badge">AI 回答</span>
            <button class="close-btn" @click="aiAnswer = ''">×</button>
          </div>
          <div class="ai-result-body" v-html="aiAnswer" />
        </div>
      </transition>
    </div>

    <!-- Stats -->
    <div class="stats-row">
      <div class="stat-card" v-for="s in stats" :key="s.label">
        <div class="stat-icon" :style="{ color: s.color }">
          <el-icon><component :is="s.icon" /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ s.value }}</div>
          <div class="stat-label">{{ s.label }}</div>
        </div>
      </div>
    </div>

    <div class="dashboard-grid">
      <!-- Knowledge Bases -->
      <div class="panel">
        <div class="panel-header">
          <span>知识库</span>
          <button class="panel-link" @click="$emit('navigate', 'admin-collections')">查看全部 →</button>
        </div>
        <div class="collections-list">
          <div v-for="col in collections.slice(0, 5)" :key="col.collection_name"
            class="col-row" @click="$emit('navigate', 'admin-collections')">
            <div class="col-name">{{ col.collection_name }}</div>
            <div class="col-meta">{{ col.embedding_model || 'text-embedding-v3' }}</div>
            <el-tag v-if="col.image_mode" size="small" type="primary">图文</el-tag>
          </div>
          <div v-if="collections.length === 0" class="empty-state">暂无知识库</div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="panel">
        <div class="panel-header">
          <span>快捷入口</span>
        </div>
        <div class="actions-grid">
          <button v-for="a in actions" :key="a.label" class="action-btn" @click="$emit('navigate', a.route)">
            <el-icon><component :is="a.icon" /></el-icon>
            <span>{{ a.label }}</span>
          </button>
        </div>
      </div>

      <!-- System Status -->
      <div class="panel">
        <div class="panel-header">
          <span>系统状态</span>
          <span class="live-badge" v-if="statusItems.every(s => s.ok)">正常</span>
        </div>
        <div class="status-rows">
          <div class="status-row" v-for="s in statusItems" :key="s.label">
            <span class="status-name">{{ s.label }}</span>
            <span class="status-val" :class="s.ok ? 'ok' : 'err'">
              {{ s.ok ? '正常' : '异常' }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Search, Cpu, DataAnalysis, FolderOpened, ChatDotRound, Setting, ArrowRight } from '@element-plus/icons-vue'
import axios from 'axios'
import { md } from '../utils/markdown.js'

const emit = defineEmits(['navigate'])
const API = '/api/v1'

const searchQuery = ref('')
const searchFocused = ref(false)
const searching = ref(false)
const aiAnswer = ref('')
const collections = ref([])

const stats = ref([
  { label: '知识库', value: '—', icon: 'DataAnalysis', color: '#2563eb' },
  { label: '类目',   value: '—', icon: 'FolderOpened',  color: '#16a34a' },
  { label: 'API',    value: '—', icon: 'Monitor',       color: '#7c3aed' },
  { label: '模型',   value: '—', icon: 'Cpu',           color: '#ca8a04' },
])

const actions = [
  { label: '智能对话',   route: 'chat',               icon: 'ChatDotRound' },
  { label: '类目管理',   route: 'kb-categories',      icon: 'FolderOpened' },
  { label: '知识库列表', route: 'admin-collections',  icon: 'DataAnalysis' },
  { label: '系统配置',   route: 'admin-config',        icon: 'Setting' },
]

const statusItems = ref([
  { label: 'API 服务',  ok: false },
  { label: '后端连接',  ok: false },
  { label: 'API Key',   ok: false },
])

const handleSearch = async () => {
  if (!searchQuery.value.trim() || searching.value) return
  searching.value = true
  aiAnswer.value = ''
  try {
    const res = await axios.post(`${API}/knowledge/`, { query: searchQuery.value, session_id: 'dashboard' })
    aiAnswer.value = md.render(res.data?.answer || '未找到相关内容')
  } catch {
    aiAnswer.value = md.render('暂时无法连接知识库，请稍后重试。')
  } finally {
    searching.value = false
  }
}

onMounted(async () => {
  try {
    const [colRes, healthRes] = await Promise.allSettled([
      axios.get(`${API}/admin/collections`),
      axios.get(`${API}/health`),
    ])
    if (colRes.status === 'fulfilled') {
      collections.value = colRes.value.data?.data?.collections || []
      stats.value[0].value = collections.value.length
      statusItems.value[0].ok = true
    }
    if (healthRes.status === 'fulfilled') {
      const h = healthRes.value.data
      statusItems.value[1].ok = h?.status === 'healthy'
      statusItems.value[2].ok = h?.api_key_configured ?? false
      stats.value[2].value = h?.status === 'healthy' ? '在线' : '离线'
      stats.value[3].value = h?.default_model || '—'
    }
    try {
      const catRes = await axios.get(`${API}/categories`)
      stats.value[1].value = catRes.data?.data?.total ?? '—'
    } catch {}
  } catch {}
})
</script>

<style scoped>
.dashboard { max-width: 1200px; }

/* ── Hero ── */
.hero { margin-bottom: 32px; }
.hero-title { font-size: 28px; font-weight: 800; color: var(--text-primary); margin-bottom: 6px; }
.hero-sub { font-size: 14px; color: var(--text-muted); margin-bottom: 20px; }
.search-bar {
  display: flex; align-items: center; gap: 10px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 8px 12px;
  max-width: 600px;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.search-bar.focused {
  border-color: var(--blue);
  box-shadow: 0 0 0 3px rgba(37,99,235,0.1);
}
.search-icon { font-size: 16px; color: var(--text-muted); flex-shrink: 0; }
.search-input {
  flex: 1; border: none; outline: none; background: transparent;
  font-size: 14px; color: var(--text-primary);
}
.search-input::placeholder { color: var(--text-muted); }
.search-submit {
  background: var(--blue); border: none; border-radius: var(--radius-sm);
  padding: 6px 16px; color: #fff; font-size: 13px; font-weight: 500; cursor: pointer;
  transition: background 0.15s;
}
.search-submit:hover { background: var(--blue-hover); }
.search-submit:disabled { opacity: 0.5; cursor: not-allowed; }
.searching-dots { display: flex; gap: 3px; align-items: center; }
.searching-dots span {
  width: 4px; height: 4px; border-radius: 50%; background: #fff;
  animation: dot-bounce 1.2s infinite;
}
.searching-dots span:nth-child(2) { animation-delay: 0.2s; }
.searching-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes dot-bounce { 0%,80%,100%{transform:translateY(0)} 40%{transform:translateY(-5px)} }

/* AI Result */
.ai-result {
  margin-top: 12px; max-width: 600px;
  background: var(--bg-surface); border: 1px solid var(--border);
  border-radius: var(--radius-md); padding: 14px 16px;
}
.ai-result-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.ai-badge { font-size: 11px; font-weight: 600; color: var(--blue); text-transform: uppercase; letter-spacing: 0.5px; }
.close-btn { background: none; border: none; color: var(--text-muted); font-size: 16px; cursor: pointer; padding: 0; line-height: 1; }
.close-btn:hover { color: var(--text-primary); }
.ai-result-body { font-size: 14px; line-height: 1.6; color: var(--text-secondary); }
.ai-result-body :deep(p) { margin: 4px 0; }
.ai-result-body :deep(code) { background: var(--bg-elevated); border-radius: 3px; padding: 1px 4px; font-size: 12px; color: var(--blue); }

/* ── Stats ── */
.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
.stat-card {
  background: var(--bg-surface); border: 1px solid var(--border);
  border-radius: var(--radius-lg); padding: 16px;
  display: flex; align-items: center; gap: 14px;
  transition: box-shadow 0.15s;
}
.stat-card:hover { box-shadow: var(--shadow-md); }
.stat-icon { font-size: 20px; opacity: 0.8; flex-shrink: 0; }
.stat-info { min-width: 0; }
.stat-value { font-size: 22px; font-weight: 700; color: var(--text-primary); line-height: 1.2; }
.stat-label { font-size: 11px; color: var(--text-muted); margin-top: 2px; text-transform: uppercase; letter-spacing: 0.3px; }

/* ── Grid ── */
.dashboard-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.dashboard-grid > :last-child { grid-column: span 2; }

/* ── Panel ── */
.panel {
  background: var(--bg-surface); border: 1px solid var(--border);
  border-radius: var(--radius-lg); padding: 16px;
}
.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 12px; font-size: 13px; font-weight: 600; color: var(--text-primary);
}
.panel-link { background: none; border: none; color: var(--blue); font-size: 12px; cursor: pointer; padding: 0; }
.panel-link:hover { color: var(--blue-hover); }

/* Collections */
.collections-list { display: flex; flex-direction: column; gap: 4px; }
.col-row {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 10px; border-radius: var(--radius-sm); cursor: pointer;
  transition: background 0.1s;
  border: 1px solid transparent;
  font-size: 13px;
}
.col-row:hover { background: var(--bg-elevated); }
.col-name { font-weight: 500; color: var(--text-primary); flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.col-meta { font-size: 11px; color: var(--text-muted); flex-shrink: 0; }
.empty-state { font-size: 13px; color: var(--text-muted); padding: 20px 0; text-align: center; }

/* Actions */
.actions-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.action-btn {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 12px; border-radius: var(--radius-md);
  cursor: pointer; font-size: 13px; font-weight: 500;
  background: var(--bg-elevated); border: 1px solid var(--border-light);
  color: var(--text-secondary);
  transition: background 0.15s, color 0.15s;
}
.action-btn:hover { background: var(--blue-bg); color: var(--blue); border-color: #bfdbfe; }

/* Status */
.live-badge { font-size: 11px; color: var(--green); font-weight: 500; }
.status-rows { display: flex; flex-direction: column; gap: 8px; }
.status-row { display: flex; align-items: center; justify-content: space-between; }
.status-name { font-size: 13px; color: var(--text-secondary); }
.status-val { font-size: 12px; font-weight: 500; }
.status-val.ok { color: var(--green); }
.status-val.err { color: var(--red); }

/* Transitions */
.slide-up-enter-active { transition: all 0.25s ease; }
.slide-up-leave-active { transition: all 0.2s ease; }
.slide-up-enter-from { opacity: 0; transform: translateY(8px); }
.slide-up-leave-to { opacity: 0; transform: translateY(-4px); }

@media (max-width: 1024px) {
  .stats-row { grid-template-columns: repeat(2, 1fr); }
  .dashboard-grid { grid-template-columns: 1fr; }
  .dashboard-grid > :last-child { grid-column: span 1; }
  .hero-title { font-size: 22px; }
}
</style>
