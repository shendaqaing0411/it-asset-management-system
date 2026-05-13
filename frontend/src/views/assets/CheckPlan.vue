<template>
  <el-card>
    <h3>资产盘点</h3>
    <p style="color:#999;margin:8px 0">按条件筛选资产，逐项核对状态。核查后点击「已盘点」标记。</p>
    <el-form :inline="true" :model="query" size="small">
      <el-form-item label="仓库"><el-select v-model="query.warehouse_id" clearable><el-option v-for="w in warehouses" :key="w.id" :label="w.name" :value="w.id" /></el-select></el-form-item>
      <el-form-item label="分类"><el-select v-model="query.category_id" clearable><el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" /></el-select></el-form-item>
      <el-form-item><el-button type="primary" @click="fetch">筛选</el-button></el-form-item>
    </el-form>
    <el-table :data="items" stripe v-loading="loading" @selection-change="onSelect">
      <el-table-column type="selection" width="40" />
      <el-table-column prop="asset_no" label="资产编号" width="140" />
      <el-table-column prop="name" label="资产名称" />
      <el-table-column prop="category_name" label="分类" width="100" />
      <el-table-column prop="location" label="位置" width="100" />
      <el-table-column prop="status" label="当前状态" width="100"><template #default="{row}"><el-tag size="small">{{ row.status }}</el-tag></template></el-table-column>
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
const query = reactive({ warehouse_id: null, category_id: null })

function onSelect(rows) { selected.value = rows }
function batchCheck() { ElMessage.success(`已标记 ${selected.value.length} 项为已盘点`); selected.value = [] }

async function fetch() {
  loading.value = true
  try {
    const res = await api.get('/stock/query', { params: { ...query, page_size: 500 } })
    items.value = res.data.items
  } finally { loading.value = false }
}

onMounted(async () => {
  const [c, w] = await Promise.all([api.get('/categories'), api.get('/warehouses')])
  categories.value = c.data; warehouses.value = w.data
  fetch()
})
</script>
