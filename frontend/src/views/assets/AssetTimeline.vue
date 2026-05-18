<template>
  <el-card v-loading="loading">
    <div style="margin-bottom:16px;display:flex;align-items:center;gap:12px">
      <el-button @click="$router.back()"><el-icon style="margin-right:4px"><ArrowLeft /></el-icon>返回</el-button>
      <span style="font-size:16px;font-weight:600">{{ asset.asset_no }} - {{ asset.name }}</span>
      <el-tag :type="statusType(asset.status)" size="small">{{ statusLabel(asset.status) }}</el-tag>
    </div>
    <div style="display:flex;gap:24px;margin-bottom:20px;color:#666;font-size:13px">
      <span>分类：{{ asset.category_name }}</span>
      <span>品牌/型号：{{ asset.brand }} / {{ asset.model }}</span>
      <span>采购日期：{{ asset.purchase_date }}</span>
      <span>价格：¥{{ asset.purchase_price }}</span>
    </div>

    <el-timeline v-if="timeline.length">
      <el-timeline-item
        v-for="(item, i) in timeline"
        :key="i"
        :timestamp="item.time"
        placement="top"
        :color="typeColor(item.type)"
        :icon="typeIcon(item.type)"
        :size="'large'"
      >
        <div style="display:flex;align-items:center;gap:8px">
          <el-tag :type="typeTag(item.type)" size="small" effect="plain">{{ item.type }}</el-tag>
          <span>{{ item.detail }}</span>
        </div>
        <span style="color:#999;font-size:12px">操作人：{{ item.operator }}</span>
      </el-timeline-item>
    </el-timeline>
    <el-empty v-else description="暂无时间线数据" :image-size="80" />
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../../api'

const route = useRoute()
const loading = ref(false)
const timeline = ref([])
const asset = reactive({ asset_no: '', name: '', status: '', category_name: '', brand: '', model: '', purchase_date: '', purchase_price: '' })

const statusMap = { in_stock: '在库', in_use: '使用中', borrowed: '借出', repairing: '维修中', scrapped: '已报废' }
const statusTypeMap = { in_stock: 'success', in_use: '', borrowed: 'warning', repairing: 'danger', scrapped: 'info' }
function statusLabel(s) { return statusMap[s] || s }
function statusType(s) { return statusTypeMap[s] || '' }

const colorMap = { '入库': '#34c88d', '出库': '#5b7cfa', '维修': '#f5a623', '返修入库': '#34c88d', '报废': '#f55858' }
function typeColor(t) { return colorMap[t] || '#909399' }
function typeTag(t) { const m = { '入库': 'success', '出库': '', '维修': 'warning', '返修入库': 'success', '报废': 'danger' }; return m[t] || 'info' }
function typeIcon(t) { const m = { '入库': 'Box', '出库': 'Upload', '维修': 'Tools', '返修入库': 'Download', '报废': 'Delete' }; return m[t] || 'MoreFilled' }

onMounted(async () => {
  loading.value = true
  try {
    const id = route.params.id
    const [a, t] = await Promise.all([
      api.get(`/assets/${id}`),
      api.get(`/assets/${id}/timeline`)
    ])
    Object.assign(asset, a.data)
    timeline.value = t.data || []
  } finally { loading.value = false }
})
</script>
