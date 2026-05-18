<template>
  <el-card>
    <el-form :inline="true" :model="query" size="small">
      <el-form-item label="关键字"><el-input v-model="query.keyword" placeholder="编号/名称" clearable /></el-form-item>
      <el-form-item label="分类"><el-select v-model="query.category_id" clearable><el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" /></el-select></el-form-item>
      <el-form-item label="状态"><el-select v-model="query.status" clearable><el-option label="在库" value="in_stock" /><el-option label="使用中" value="in_use" /><el-option label="借出" value="borrowed" /><el-option label="维修中" value="repairing" /><el-option label="已报废" value="scrapped" /></el-select></el-form-item>
      <el-form-item label="仓库"><el-select v-model="query.warehouse_id" clearable><el-option v-for="w in warehouses" :key="w.id" :label="w.name" :value="w.id" /></el-select></el-form-item>
      <el-form-item><el-button type="primary" @click="fetch">查询</el-button><el-button @click="reset">重置</el-button><el-button @click="handleExport"><el-icon style="margin-right:4px"><Download /></el-icon>导出</el-button></el-form-item>
    </el-form>
    <el-table :data="items" stripe v-loading="loading">
      <el-table-column prop="asset_no" label="资产编号" width="140" />
      <el-table-column prop="name" label="资产名称" show-overflow-tooltip />
      <el-table-column prop="category_name" label="分类" width="100" />
      <el-table-column prop="status" label="状态" width="80"><template #default="{row}"><el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag></template></el-table-column>
      <el-table-column prop="warehouse_name" label="仓库" width="100" />
      <el-table-column prop="location" label="位置" width="100" />
      <el-table-column label="操作" width="180">
        <template #default="{row}">
          <el-button link type="primary" @click="handleAction(row, 'in')" v-if="row.status !== 'in_stock'">入库</el-button>
          <el-button link type="warning" @click="handleAction(row, 'out')" v-if="row.status === 'in_stock'">出库</el-button>
          <el-button link type="success" @click="handleAction(row, 'return')" v-if="row.status === 'in_use' || row.status === 'borrowed'">归还</el-button>
          <el-button link type="danger" @click="handleAction(row, 'scrap')">报废</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination v-model:current-page="query.page" :total="total" :page-size="20" layout="total, prev, pager, next" @current-change="fetch" style="margin-top:16px" />
  </el-card>
</template>

<script setup>
// 库存查询：多维筛选（关键字/分类/状态/仓库），行内快捷操作（入库/出库/归还/报废）
import { ref, reactive, onMounted } from 'vue'
import api from '../../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const items = ref([])
const total = ref(0)
const categories = ref([])
const warehouses = ref([])
const query = reactive({ keyword: '', category_id: null, status: '', warehouse_id: null, page: 1 })

const statusMap = { in_stock: '在库', in_use: '使用中', borrowed: '借出', repairing: '维修中', scrapped: '已报废' }
const statusTypeMap = { in_stock: 'success', in_use: '', borrowed: 'warning', repairing: 'danger', scrapped: 'info' }
function statusLabel(s) { return statusMap[s] || s }
function statusType(s) { return statusTypeMap[s] || '' }

async function fetch() {
  loading.value = true
  try {
    const res = await api.get('/stock/query', { params: { ...query, category_id: query.category_id || undefined, status: query.status || undefined, warehouse_id: query.warehouse_id || undefined } })
    items.value = res.data.items
    total.value = res.data.total
  } finally { loading.value = false }
}

function reset() { query.keyword = ''; query.category_id = null; query.status = ''; query.warehouse_id = null; fetch() }

function handleExport() { window.open('/api/stock/records?format=csv', '_blank') }

async function handleAction(row, action) {
  if (action === 'in') {
    await api.post('/stock/in', { asset_id: row.id, type: '采购入库', to_warehouse_id: row.warehouse_id })
    ElMessage.success('入库成功')
  } else if (action === 'out') {
    const { value } = await ElMessageBox.prompt('请输入领用/借用说明', '出库', { inputType: 'textarea' })
    await api.post('/stock/out', { asset_id: row.id, type: '领用出库', remark: value || '' })
    ElMessage.success('出库成功')
  } else if (action === 'return') {
    await api.post(`/stock/return/${row.id}`)
    ElMessage.success('归还成功')
  } else if (action === 'scrap') {
    await ElMessageBox.confirm('确认报废该资产？', '报废确认', { type: 'warning' })
    await api.post('/scraps', { asset_id: row.id })
    ElMessage.success('报废完成')
  }
  fetch()
}

onMounted(async () => {
  const [c, w] = await Promise.all([api.get('/categories'), api.get('/warehouses')])
  categories.value = c.data; warehouses.value = w.data
  fetch()
})
</script>
