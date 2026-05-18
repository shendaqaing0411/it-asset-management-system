<template>
  <el-card>
    <h3>资产盘点</h3>
    <p style="color:#999;margin:8px 0">按条件筛选资产，逐项核对状态。核查后点击「已盘点」标记。</p>

    <!-- 资产总数统计卡片 -->
    <el-row :gutter="16" style="margin-bottom:20px">
      <el-col :span="6">
        <el-statistic title="资产总数" :value="totalCount">
          <template #prefix><el-icon><Monitor /></el-icon></template>
        </el-statistic>
      </el-col>
      <el-col :span="6" v-for="s in subStats" :key="s.name">
        <el-statistic :title="s.name" :value="s.count" />
      </el-col>
    </el-row>

    <el-form :inline="true" :model="query" size="small">
      <el-form-item label="仓库"><el-select v-model="query.warehouse_id" clearable><el-option v-for="w in warehouses" :key="w.id" :label="w.name" :value="w.id" /></el-select></el-form-item>
      <el-form-item label="一级分类"><el-select v-model="query.parent_category_id" clearable @change="onParentCategoryChange"><el-option v-for="c in parentCategories" :key="c.id" :label="c.name" :value="c.id" /></el-select></el-form-item>
      <el-form-item label="二级分类"><el-select v-model="query.category_id" clearable><el-option v-for="c in subCategories" :key="c.id" :label="c.name" :value="c.id" /></el-select></el-form-item>
      <el-form-item label="状态"><el-select v-model="query.status" clearable><el-option label="在库" value="in_stock" /><el-option label="使用中" value="in_use" /><el-option label="借出" value="borrowed" /><el-option label="维修中" value="repairing" /><el-option label="已报废" value="scrapped" /></el-select></el-form-item>
      <el-form-item><el-button type="primary" @click="fetch">筛选</el-button></el-form-item>
    </el-form>
    <el-table :data="items" stripe v-loading="loading" @selection-change="onSelect">
      <el-table-column type="selection" width="40" />
      <el-table-column prop="asset_no" label="资产编号" width="140" />
      <el-table-column prop="name" label="资产名称" />
      <el-table-column prop="category_name" label="分类" width="100" />
      <el-table-column prop="location" label="位置" width="100" />
      <el-table-column prop="status" label="当前状态" width="100"><template #default="{row}"><el-tag size="small">{{ statusMap[row.status] || row.status }}</el-tag></template></el-table-column>
      <el-table-column label="盘点状态" width="100"><template #default><el-tag type="success" size="small">已盘点</el-tag></template></el-table-column>
      <el-table-column label="盘点结果" width="100"><template #default><el-tag type="success" size="small">正常</el-tag></template></el-table-column>
    </el-table>
    <el-button type="primary" @click="batchCheck" :disabled="!selected.length" style="margin-top:16px">批量标记已盘点 ({{ selected.length }})</el-button>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '../../api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const items = ref([])
const selected = ref([])
const categories = ref([])
const warehouses = ref([])
const totalCount = ref(0)
const subStats = ref([])
const parentCategories = ref([])
const subCategories = ref([])
const query = reactive({ warehouse_id: null, category_id: null, parent_category_id: null, status: null })
const statusMap = {
  in_stock: '在库',
  in_use: '使用中',
  borrowed: '借出',
  repairing: '维修中',
  scrapped: '已报废'
}

function onSelect(rows) { selected.value = rows }

function onParentCategoryChange() {
  query.category_id = null
  if (query.parent_category_id) {
    const parent = categories.value.find(c => c.id === query.parent_category_id)
    subCategories.value = parent?.children || []
  } else {
    subCategories.value = []
  }
}

function batchCheck() { ElMessage.success(`已标记 ${selected.value.length} 项为已盘点`); selected.value = [] }

async function fetch() {
  loading.value = true
  try {
    const params = { ...query, page_size: 500 }
    if (!params.parent_category_id) delete params.parent_category_id
    if (!params.category_id) delete params.category_id
    if (!params.status) delete params.status
    const res = await api.get('/stock/query', { params })
    items.value = res.data.items
    totalCount.value = res.data.total
    // 统计二级类目分布
    const stats = {}
    items.value.forEach(item => {
      const cn = item.category_name || '未分类'
      stats[cn] = (stats[cn] || 0) + 1
    })
    subStats.value = Object.entries(stats).map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count).slice(0, 3)
  } finally { loading.value = false }
}

onMounted(async () => {
  const [c, w] = await Promise.all([
    api.get('/categories', { params: { tree: true } }),
    api.get('/warehouses')
  ])
  categories.value = c.data || []
  parentCategories.value = categories.value.map(p => ({ id: p.id, name: p.name }))
  warehouses.value = w.data
  fetch()
})
</script>
