<template>
  <div id="app">
    <div class="app-layout">
      <!-- Sidebar -->
      <aside class="sidebar">
        <div class="sidebar-logo">
          <div class="logo-mark">
            <el-icon><cpu /></el-icon>
          </div>
          <span class="logo-text">EmployRAG</span>
        </div>

        <nav class="nav-list">
          <el-tooltip v-for="item in navItems" :key="item.key"
            :content="item.label" placement="right" effect="dark">
            <button
              class="nav-item"
              :class="{ active: activeMenu === item.key || (item.match && activeMenu.startsWith(item.match)) }"
              @click="handleMenuSelect(item.key)"
            >
              <el-icon><component :is="item.icon" /></el-icon>
              <span class="nav-label">{{ item.label }}</span>
            </button>
          </el-tooltip>
        </nav>
      </aside>

      <!-- Main -->
      <div class="main-wrap">
        <!-- Topbar -->
        <header class="topbar">
          <div class="topbar-left">
            <span class="page-title">{{ pageTitle }}</span>
            <span v-if="pageSubtitle" class="page-subtitle">{{ pageSubtitle }}</span>
          </div>
          <div class="topbar-right">
            <div class="model-select-wrap">
              <el-icon class="model-icon"><cpu /></el-icon>
              <el-select v-model="selectedModel" size="small" style="width:150px" placeholder="模型">
                <el-option v-for="m in availableModels" :key="m.name" :label="m.name" :value="m.name" />
              </el-select>
            </div>
            <div class="status-pill" :class="apiStatus ? 'online' : 'offline'">
              <span class="pulse-dot" />
              {{ apiStatus ? '已连接' : '离线' }}
            </div>
          </div>
        </header>

        <!-- Content -->
        <main class="content">
          <div v-show="activeMenu === 'dashboard'"><DashboardView @navigate="handleMenuSelect" /></div>
          <div v-show="activeMenu === 'chat'"><SimpleChat :model="selectedModel" /></div>
          <div v-show="activeMenu === 'kb-categories'"><CategoryManager /></div>
          <div v-show="activeMenu.startsWith('admin')"><AdminPanel :active-tab="adminTab" /></div>
          <div v-show="activeMenu === 'devtools'"><DevTools /></div>
        </main>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { apiService } from './services/api'
import SimpleChat from './components/SimpleChat.vue'
import CategoryManager from './components/doc/CategoryManager.vue'
import AdminPanel from './components/AdminPanel.vue'
import DevTools from './components/DevTools.vue'
import DashboardView from './views/DashboardView.vue'

const activeMenu = ref('dashboard')
const selectedModel = ref('qwen-turbo')
const availableModels = ref([])
const apiStatus = ref(false)

const navItems = [
  { key: 'dashboard', label: '工作台', icon: 'HomeFilled' },
  { key: 'chat', label: '智能对话', icon: 'ChatDotRound' },
  { key: 'kb-categories', label: '类目管理', icon: 'FolderOpened' },
  { key: 'admin-collections', label: '知识库', icon: 'DataAnalysis', match: 'admin' },
  { key: 'devtools', label: '开发工具', icon: 'Monitor' },
]

const adminTabMap = { 'admin-collections': 'collections', 'admin-create': 'create', 'admin-config': 'config' }
const adminTab = computed(() => adminTabMap[activeMenu.value] || 'namespace')

const pageMeta = {
  dashboard:          { title: '工作台', sub: '企业知识库' },
  chat:               { title: '智能对话', sub: 'AI 知识问答' },
  'kb-categories':    { title: '类目管理', sub: '文档分类管理' },
  'admin-collections':{ title: '知识库列表', sub: '向量集合管理' },
  'admin-create':     { title: '创建知识库', sub: '新建集合' },
  'admin-config':     { title: '配置信息', sub: '系统配置' },
  devtools:           { title: '开发工具', sub: 'API 调试' },
}
const pageTitle    = computed(() => pageMeta[activeMenu.value]?.title || '')
const pageSubtitle = computed(() => pageMeta[activeMenu.value]?.sub || '')

const handleMenuSelect = (key) => { activeMenu.value = key }

onMounted(async () => {
  try {
    const res = await apiService.getModels()
    availableModels.value = res.models
    selectedModel.value = res.default_model
    apiStatus.value = true
  } catch {
    availableModels.value = [
      { name: 'qwen-turbo' }, { name: 'qwen-plus' }, { name: 'qwen-max' }
    ]
  }
})
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #f5f6f8; }
</style>

<style scoped>
/* ── Layout ── */
#app { height: 100vh; overflow: hidden; }
.app-layout {
  display: flex; height: 100vh; overflow: hidden;
}

/* ── Sidebar ── */
.sidebar {
  width: 200px; flex-shrink: 0;
  display: flex; flex-direction: column;
  background: var(--bg-surface);
  border-right: 1px solid var(--border);
}
.sidebar-logo {
  height: 56px; display: flex; align-items: center; gap: 10px;
  padding: 0 16px;
  border-bottom: 1px solid var(--border);
}
.logo-mark {
  width: 28px; height: 28px; border-radius: 7px;
  background: var(--blue);
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; color: #fff;
  flex-shrink: 0;
}
.logo-text {
  font-size: 14px; font-weight: 700; color: var(--text-primary);
  letter-spacing: -0.3px;
}
.nav-list {
  flex: 1; display: flex; flex-direction: column;
  padding: 8px; gap: 2px;
}
.nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 12px; border-radius: var(--radius-sm);
  cursor: pointer; color: var(--text-secondary); font-size: 13px; font-weight: 500;
  background: transparent; border: none; outline: none;
  transition: all 0.15s;
  text-align: left;
}
.nav-item:hover { background: var(--bg-elevated); color: var(--text-primary); }
.nav-item.active {
  background: var(--blue-bg); color: var(--blue);
  font-weight: 600;
}
.nav-item .el-icon { font-size: 16px; flex-shrink: 0; }
.nav-label { flex: 1; }
/* ── Main wrap ── */
.main-wrap { flex: 1; display: flex; flex-direction: column; overflow: hidden; }

/* ── Topbar ── */
.topbar {
  height: 56px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px;
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border);
}
.topbar-left { display: flex; align-items: baseline; gap: 8px; }
.page-title { font-size: 15px; font-weight: 700; color: var(--text-primary); }
.page-subtitle { font-size: 12px; color: var(--text-muted); }
.topbar-right { display: flex; align-items: center; gap: 12px; }
.model-select-wrap { display: flex; align-items: center; gap: 6px; }
.model-icon { color: var(--text-muted); font-size: 14px; }

.status-pill {
  display: flex; align-items: center; gap: 6px;
  padding: 4px 10px; border-radius: 99px;
  font-size: 11px; font-weight: 500;
  border: 1px solid var(--border);
  color: var(--text-muted);
}
.status-pill.online { color: var(--green); border-color: #bbf7d0; background: var(--green-bg); }
.pulse-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--text-muted);
}
.status-pill.online .pulse-dot {
  background: var(--green);
}

/* ── Content ── */
.content {
  flex: 1; overflow-y: auto; padding: 24px 32px;
}
.content::-webkit-scrollbar { width: 4px; }
.content::-webkit-scrollbar-thumb { background: var(--border); border-radius: 99px; }
</style>
