<template>
  <div>
    <el-card>
      <el-form :inline="true" :model="query" size="small">
        <el-form-item label="关键字"><el-input v-model="query.keyword" placeholder="编号/名称/序列号" clearable /></el-form-item>
        <el-form-item label="分类"><el-select v-model="query.category_id" clearable><el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" /></el-select></el-form-item>
        <el-form-item label="状态"><el-select v-model="query.status" clearable><el-option label="在库" value="in_stock" /><el-option label="使用中" value="in_use" /><el-option label="借出" value="borrowed" /><el-option label="维修中" value="repairing" /><el-option label="已报废" value="scrapped" /></el-select></el-form-item>
        <el-form-item><el-button type="primary" @click="fetch">查询</el-button><el-button @click="reset">重置</el-button><el-button type="success" @click="$router.push('/assets/form')">新增资产</el-button></el-form-item>
      </el-form>
      <el-table :data="items" stripe v-loading="loading">
        <el-table-column prop="asset_no" label="资产编号" width="140" />
        <el-table-column prop="name" label="资产名称" show-overflow-tooltip />
        <el-table-column prop="category_name" label="分类" width="100" />
        <el-table-column prop="brand" label="品牌" width="80" />
        <el-table-column prop="model" label="型号" width="120" />
        <el-table-column prop="serial_no" label="序列号" width="120" />
        <el-table-column prop="purchase_price" label="价格" width="100" />
        <el-table-column prop="status" label="状态" width="80"><template #default="{row}"><el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag></template></el-table-column>
        <el-table-column prop="dept_name" label="使用部门" width="100" />
        <el-table-column prop="warehouse_name" label="仓库" width="80" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{row}">
            <el-button link type="primary" @click="$router.push(`/assets/form/${row.id}`)">编辑</el-button>
            <el-button link type="success" @click="handleQrcode(row)">二维码</el-button>
            <el-popconfirm title="确认删除？" @confirm="handleDelete(row.id)"><template #reference><el-button link type="danger">删除</el-button></template></el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination v-model:current-page="query.page" :total="total" :page-size="20" layout="total, prev, pager, next" @current-change="fetch" style="margin-top:16px" />
    </el-card>
    <el-dialog v-model="qrVisible" title="资产二维码" width="300px"><img v-if="qrSrc" :src="qrSrc" style="width:100%" /><p style="text-align:center;margin-top:8px">{{ qrLabel }}</p></el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '../../api'

const loading = ref(false)
const items = ref([])
const total = ref(0)
const categories = ref([])
const query = reactive({ keyword: '', category_id: null, status: '', page: 1 })
const qrVisible = ref(false)
const qrSrc = ref('')
const qrLabel = ref('')

const statusMap = { in_stock: '在库', in_use: '使用中', borrowed: '借出', repairing: '维修中', scrapped: '已报废' }
const statusTypeMap = { in_stock: 'success', in_use: '', borrowed: 'warning', repairing: 'danger', scrapped: 'info' }
function statusLabel(s) { return statusMap[s] || s }
function statusType(s) { return statusTypeMap[s] || '' }

async function fetch() {
  loading.value = true
  try {
    const res = await api.get('/assets', { params: { ...query, category_id: query.category_id || undefined, status: query.status || undefined } })
    items.value = res.data.items
    total.value = res.data.total
  } finally { loading.value = false }
}

function reset() { query.keyword = ''; query.category_id = null; query.status = ''; fetch() }

async function handleDelete(id) {
  await api.delete(`/assets/${id}`)
  fetch()
}

async function handleQrcode(row) {
  qrLabel.value = `${row.asset_no} - ${row.name}`
  qrSrc.value = `/api/assets/qrcode/${row.id}`
  qrVisible.value = true
}

onMounted(async () => {
  const res = await api.get('/categories')
  categories.value = res.data
  fetch()
})
</script>
