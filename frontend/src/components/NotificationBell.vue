<template>
  <el-popover placement="bottom-end" :width="360" trigger="click" @show="fetchNotifications">
    <template #reference>
      <el-badge :value="unreadCount" :hidden="!unreadCount" :max="99" class="bell-badge">
        <el-icon :size="20" class="bell-icon" :class="{ ringing: unreadCount > 0 }"><Bell /></el-icon>
      </el-badge>
    </template>
    <div class="notify-header">
      <span>通知中心</span>
      <el-button link type="primary" size="small" @click="fetchNotifications">刷新</el-button>
    </div>
    <div class="notify-list" v-loading="loading">
      <div v-if="!items.length && !loading" class="notify-empty">暂无通知</div>
      <div
        v-for="item in items"
        :key="item.id"
        class="notify-item"
        :class="{ unread: !item.is_read }"
        @click="handleClick(item)"
      >
        <el-icon :size="16" class="notify-type-icon" :style="{ color: typeColor(item.type) }">
          <component :is="typeIcon(item.type)" />
        </el-icon>
        <div class="notify-body">
          <div class="notify-title">{{ item.title }}</div>
          <div class="notify-content" v-if="item.content">{{ item.content }}</div>
          <div class="notify-time">{{ item.create_time }}</div>
        </div>
        <span v-if="!item.is_read" class="notify-dot"></span>
      </div>
    </div>
  </el-popover>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const items = ref([])
const unreadCount = ref(0)
const loading = ref(false)

const typeIcons = {
  warranty_expire: 'Warning',
  stock_low: 'Box',
  approval_pending: 'DocumentChecked',
  repair_complete: 'Tools'
}
function typeIcon(t) { return typeIcons[t] || 'Bell' }
function typeColor(t) {
  const m = { warranty_expire: '#f5a623', stock_low: '#f55858', approval_pending: '#5b7cfa', repair_complete: '#34c88d' }
  return m[t] || '#909399'
}

async function fetchCount() {
  try {
    const res = await api.get('/notifications/count')
    unreadCount.value = res.data?.count ?? res.data ?? 0
  } catch { /* ignore */ }
}

async function fetchNotifications() {
  loading.value = true
  try {
    const res = await api.get('/notifications', { params: { page_size: 20 } })
    items.value = res.data?.items || res.data || []
  } catch { /* ignore */ }
  finally { loading.value = false }
}

async function handleClick(item) {
  if (!item.is_read) {
    try { await api.put(`/notifications/${item.id}/read`) } catch { /* ignore */ }
    item.is_read = 1
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  }
  const routes = {
    warranty_expire: '/assets/list',
    stock_low: '/system/warnings',
    approval_pending: '/stock/approvals',
    repair_complete: '/repairs/list'
  }
  const path = routes[item.type] || '/dashboard'
  router.push(path)
}

onMounted(() => { fetchCount(); setInterval(fetchCount, 30000) })
</script>

<style scoped>
.bell-badge { cursor: pointer; }
.bell-icon { color: #666; transition: color .2s; }
.bell-icon:hover { color: #333; }
.bell-icon.ringing { color: var(--primary); animation: bellShake .5s ease-in-out infinite; }
@keyframes bellShake {
  0%, 100% { transform: rotate(0); }
  25% { transform: rotate(-8deg); }
  75% { transform: rotate(8deg); }
}
.notify-header { display: flex; justify-content: space-between; align-items: center; padding: 0 0 8px; border-bottom: 1px solid #eee; margin-bottom: 8px; font-weight: 600; }
.notify-list { max-height: 360px; overflow-y: auto; }
.notify-empty { text-align: center; color: #999; padding: 24px 0; font-size: 13px; }
.notify-item { display: flex; align-items: flex-start; gap: 10px; padding: 10px 8px; border-radius: 6px; cursor: pointer; transition: background .15s; position: relative; }
.notify-item:hover { background: #f5f7fa; }
.notify-item.unread { background: #f0f4ff; }
.notify-type-icon { margin-top: 2px; flex-shrink: 0; }
.notify-body { flex: 1; min-width: 0; }
.notify-title { font-size: 13px; font-weight: 500; color: #333; }
.notify-content { font-size: 12px; color: #888; margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.notify-time { font-size: 11px; color: #bbb; margin-top: 4px; }
.notify-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--primary); flex-shrink: 0; margin-top: 6px; }
</style>
