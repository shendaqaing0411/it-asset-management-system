<template>
  <div class="dashboard">
    <!-- stat cards -->
    <div class="stat-grid">
      <div class="stat-card" v-for="card in statCards" :key="card.label">
        <div class="stat-icon" :style="{ background: card.bg, color: card.color }"><el-icon :size="22"><component :is="card.icon" /></el-icon></div>
        <div class="stat-info">
          <div class="stat-value" :style="{ color: card.color }">{{ card.value }}</div>
          <div class="stat-label">{{ card.label }}</div>
        </div>
      </div>
    </div>

    <!-- charts row -->
    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="14">
        <el-card header="资产状态分布" shadow="never"><v-chart :option="statusChartOption" style="height:320px" autoresize /></el-card>
      </el-col>
      <el-col :span="10">
        <el-card header="分类占比" shadow="never"><v-chart :option="categoryChartOption" style="height:320px" autoresize /></el-card>
      </el-col>
    </el-row>

    <!-- recent logs & warnings -->
    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="12">
        <el-card header="最近操作" shadow="never">
          <div v-for="l in recentLogs" :key="l.id" class="log-item">
            <el-avatar :size="28" icon="UserFilled" style="flex-shrink:0" />
            <div class="log-body">
              <span class="log-user">{{ l.real_name || l.username }}</span>
              <span class="log-desc">{{ l.description }}</span>
            </div>
            <span class="log-time">{{ l.create_time }}</span>
          </div>
          <el-empty v-if="!recentLogs.length" description="暂无操作记录" :image-size="60" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card header="库存预警" shadow="never">
          <div v-if="warnings.length" class="warn-list">
            <div v-for="w in warnings" :key="w.id" class="warn-item" :class="w.warning">
              <span class="warn-dot"></span>
              <span>{{ w.warehouse_name }} · {{ w.category_name }}</span>
              <el-tag :type="w.warning === 'low' ? 'danger' : 'warning'" size="small" effect="plain" round>
                {{ w.warning === 'low' ? `库存不足 (${w.current_stock})` : `库存过高 (${w.current_stock})` }}
              </el-tag>
            </div>
          </div>
          <el-empty v-else description="暂无预警" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
// 仪表盘：6 个统计卡片 + ECharts 柱状图（状态分布）+ 环形图（分类占比）+ 最近操作日志 + 库存预警
import { ref, computed, onMounted } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, BarChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import api from '../api'

use([CanvasRenderer, PieChart, BarChart, TooltipComponent, LegendComponent, GridComponent])

const statCards = ref([
  { label: '资产总数', value: 0, color: '#5b7cfa', bg: '#eef1fe', icon: 'Monitor' },
  { label: '在库', value: 0, color: '#34c88d', bg: '#e8f8f2', icon: 'Box' },
  { label: '使用中', value: 0, color: '#f5a623', bg: '#fef7e8', icon: 'User' },
  { label: '维修中', value: 0, color: '#f55858', bg: '#feecec', icon: 'Tools' },
  { label: '借出', value: 0, color: '#909399', bg: '#f0f0f0', icon: 'Share' },
  { label: '已报废', value: 0, color: '#b0b3ba', bg: '#f5f5f5', icon: 'Delete' }
])
const recentLogs = ref([])
const warnings = ref([])
const statusData = ref({ in_stock: 0, in_use: 0, borrowed: 0, repairing: 0, scrapped: 0 })
const categoryData = ref([])

const statusChartOption = computed(() => ({
  // ECharts 柱状图：按状态统计资产数量
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: ['在库', '使用中', '借出', '维修中', '已报废'], axisLine: { lineStyle: { color: '#ddd' } } },
  yAxis: { type: 'value', splitLine: { lineStyle: { color: '#f0f0f0' } } },
  series: [{
    type: 'bar', barWidth: 32, itemStyle: { borderRadius: [6, 6, 0, 0] },
    data: [
      { value: statusData.value.in_stock, itemStyle: { color: '#34c88d' } },
      { value: statusData.value.in_use, itemStyle: { color: '#5b7cfa' } },
      { value: statusData.value.borrowed, itemStyle: { color: '#f5a623' } },
      { value: statusData.value.repairing, itemStyle: { color: '#f55858' } },
      { value: statusData.value.scrapped, itemStyle: { color: '#b0b3ba' } }
    ]
  }]
}))

const categoryChartOption = computed(() => ({
  // ECharts 环形图：按分类统计资产占比
  tooltip: { trigger: 'item' },
  series: [{
    type: 'pie', radius: ['50%', '75%'], center: ['50%', '50%'], itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 3 },
    label: { show: true, formatter: '{b}\n{d}%' },
    data: categoryData.value.map((c, i) => ({ name: c.name, value: c.count, itemStyle: { color: ['#5b7cfa','#34c88d','#f5a623','#f55858','#909399'][i % 5] } }))
  }]
}))

onMounted(async () => {
  try {
    const [s, l, stock] = await Promise.all([
      api.get('/report/summary'),
      api.get('/logs', { params: { page_size: 8 } }),
      api.get('/report/stock')
    ])
    const d = s.data
    statCards.value[0].value = d.total
    statCards.value[1].value = d.in_stock
    statCards.value[2].value = d.in_use || 0
    statCards.value[3].value = d.repairing || 0
    statCards.value[4].value = d.borrowed || 0
    statCards.value[5].value = d.scrapped || 0
    recentLogs.value = l.data.items
    statusData.value = { in_stock: d.in_stock, in_use: d.in_use || 0, borrowed: d.borrowed || 0, repairing: d.repairing || 0, scrapped: d.scrapped || 0 }
    categoryData.value = stock.data.by_category || []
    try {
      const w = await api.get('/stock/warnings')
      warnings.value = w.data.filter(x => x.warning)
    } catch {}
  } catch {}
})
</script>

<style scoped>
.stat-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 16px; }
.stat-card { background: #fff; border-radius: var(--card-radius); padding: 20px; display: flex; align-items: center; gap: 16px; box-shadow: var(--card-shadow); transition: transform .2s, box-shadow .2s; }
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,.08); }
.stat-icon { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.stat-value { font-size: 24px; font-weight: 700; }
.stat-label { font-size: 13px; color: #999; margin-top: 2px; }

.log-item { display: flex; align-items: center; gap: 10px; padding: 10px 0; border-bottom: 1px solid #f5f5f5; }
.log-item:last-child { border-bottom: none; }
.log-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 4px; }
.log-user { font-size: 12px; color: #999; }
.log-desc { font-size: 13px; color: #333; }
.log-time { font-size: 12px; color: #bbb; white-space: nowrap; }

.warn-list { display: flex; flex-direction: column; gap: 10px; }
.warn-item { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: 6px; background: #fafafa; font-size: 13px; }
.warn-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.warn-item.low { background: #fff5f5; } .warn-item.low .warn-dot { background: #f55858; }
.warn-item.high { background: #fffbe8; } .warn-item.high .warn-dot { background: #f5a623; }
.warn-item span:nth-child(2) { flex: 1; }

@media (max-width: 1200px) { .stat-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 768px) { .stat-grid { grid-template-columns: repeat(2, 1fr); } }
</style>
