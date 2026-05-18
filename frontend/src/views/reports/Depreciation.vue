<template>
  <div v-loading="loading">
    <!-- 汇总卡片 -->
    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-icon" style="background:#eef1fe;color:#5b7cfa"><el-icon :size="22"><Money /></el-icon></div>
        <div class="stat-info"><div class="stat-value" style="color:#5b7cfa">¥{{ fmt(summary.total_original) }}</div><div class="stat-label">原值总额</div></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:#fef7e8;color:#f5a623"><el-icon :size="22"><TrendCharts /></el-icon></div>
        <div class="stat-info"><div class="stat-value" style="color:#f5a623">¥{{ fmt(summary.total_depreciation) }}</div><div class="stat-label">累计折旧</div></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:#e8f8f2;color:#34c88d"><el-icon :size="22"><Coin /></el-icon></div>
        <div class="stat-info"><div class="stat-value" style="color:#34c88d">¥{{ fmt(summary.total_net) }}</div><div class="stat-label">净值总额</div></div>
      </div>
    </div>

    <!-- 操作栏 -->
    <div style="display:flex;justify-content:space-between;align-items:center;margin:16px 0">
      <div>
        <el-button type="primary" @click="handleCalculate" :loading="calculating">执行折旧计算</el-button>
      </div>
      <el-button @click="handleExport">导出 Excel</el-button>
    </div>

    <!-- 分类汇总表 -->
    <el-card v-if="categorySummary.length" shadow="never" style="margin-bottom:16px">
      <template #header><span style="font-weight:600">分类汇总</span></template>
      <el-table :data="categorySummary" stripe size="small">
        <el-table-column prop="category" label="资产分类" />
        <el-table-column label="原值合计" width="140">
          <template #default="{row}">¥{{ fmt(row.original) }}</template>
        </el-table-column>
        <el-table-column label="累计折旧" width="140">
          <template #default="{row}">¥{{ fmt(row.depreciation) }}</template>
        </el-table-column>
        <el-table-column label="净值合计" width="140">
          <template #default="{row}">¥{{ fmt(row.net) }}</template>
        </el-table-column>
        <el-table-column prop="count" label="数量" width="80" />
      </el-table>
    </el-card>

    <!-- 资产明细表格 -->
    <el-card shadow="never">
      <el-table :data="items" stripe>
        <el-table-column prop="asset_no" label="资产编号" width="140" />
        <el-table-column prop="name" label="资产名称" show-overflow-tooltip />
        <el-table-column prop="category_name" label="分类" width="120" show-overflow-tooltip />
        <el-table-column label="原值" width="120">
          <template #default="{row}">{{ row.purchase_price ? '¥' + fmt(row.purchase_price) : '-' }}</template>
        </el-table-column>
        <el-table-column label="月折旧额" width="120">
          <template #default="{row}">{{ row.monthly_depreciation ? '¥' + fmt(row.monthly_depreciation) : '-' }}</template>
        </el-table-column>
        <el-table-column label="累计折旧" width="120">
          <template #default="{row}">{{ fmt(row.accumulated_depreciation) ? '¥' + fmt(row.accumulated_depreciation) : '¥0.00' }}</template>
        </el-table-column>
        <el-table-column label="净值" width="120">
          <template #default="{row}">{{ row.net_value ? '¥' + fmt(row.net_value) : '¥0.00' }}</template>
        </el-table-column>
        <el-table-column label="折旧方法" width="100">
          <template #default="{row}">{{ row.method === 'once' ? '一次性' : '直线法' }}</template>
        </el-table-column>
        <el-table-column label="折旧状态" width="100">
          <template #default="{row}"><el-tag :type="row.status === '折旧中' ? '' : 'info'" size="small">{{ row.status || '—' }}</el-tag></template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api, { downloadCsv } from '../../api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const calculating = ref(false)
const items = ref([])
const categorySummary = ref([])
const summary = reactive({ total_original: 0, total_depreciation: 0, total_net: 0 })

function fmt(n) { return n ? Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00' }

async function fetch() {
  loading.value = true
  try {
    const res = await api.get('/report/depreciation')
    items.value = res.data.items || []
    categorySummary.value = res.data.category_summary || []
    if (res.data.summary) Object.assign(summary, res.data.summary)
  } finally { loading.value = false }
}

async function handleCalculate() {
  calculating.value = true
  try {
    const res = await api.post('/assets/calculate-depreciation')
    ElMessage.success(res.data?.message || '折旧计算完成')
    fetch()
  } finally { calculating.value = false }
}

function handleExport() {
  downloadCsv('/report/depreciation?format=csv')
}

onMounted(() => fetch())
</script>

<style scoped>
.stat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.stat-card { background: #fff; border-radius: var(--card-radius); padding: 20px; display: flex; align-items: center; gap: 16px; box-shadow: var(--card-shadow); }
.stat-icon { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.stat-value { font-size: 22px; font-weight: 700; }
.stat-label { font-size: 13px; color: #999; margin-top: 2px; }
</style>
