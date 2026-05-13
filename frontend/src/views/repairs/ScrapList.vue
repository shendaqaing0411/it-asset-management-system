<template>
  <el-card>
    <h3 style="margin-bottom:16px">报废管理</h3>
    <el-form :inline="true" :model="form" size="small" style="margin-bottom:16px">
      <el-form-item label="资产"><el-select v-model="form.asset_id" filterable remote :remote-method="searchAssets" placeholder="搜索资产" style="width:300px"><el-option v-for="a in assetOptions" :key="a.id" :label="`${a.asset_no} - ${a.name}`" :value="a.id" /></el-select></el-form-item>
      <el-form-item label="备注"><el-input v-model="form.remark" /></el-form-item>
      <el-form-item><el-button type="danger" @click="handleScrap" :loading="saving">确认报废</el-button></el-form-item>
    </el-form>
    <el-table :data="items" stripe v-loading="loading">
      <el-table-column prop="asset_no" label="资产编号" width="140" />
      <el-table-column prop="asset_name" label="资产名称" />
      <el-table-column prop="operate_date" label="报废日期" width="120" />
      <el-table-column prop="remark" label="备注" show-overflow-tooltip />
      <el-table-column prop="create_time" label="操作时间" width="160" />
    </el-table>
    <el-pagination v-model:current-page="page" :total="total" :page-size="20" layout="total, prev, pager, next" @current-change="fetch" style="margin-top:16px" />
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '../../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const saving = ref(false)
const items = ref([])
const total = ref(0)
const page = ref(1)
const assetOptions = ref([])
const form = reactive({ asset_id: null, remark: '' })

async function fetch() {
  loading.value = true
  try { const res = await api.get('/scraps', { params: { page: page.value } }); items.value = res.data.items; total.value = res.data.total }
  finally { loading.value = false }
}

async function searchAssets(q) {
  if (!q) return
  const res = await api.get('/assets', { params: { keyword: q, page_size: 20 } })
  assetOptions.value = res.data.items
}

async function handleScrap() {
  if (!form.asset_id) { ElMessage.warning('请选择资产'); return }
  await ElMessageBox.confirm('确认报废该资产？此操作不可撤销。', '报废确认', { type: 'warning' })
  saving.value = true
  try { await api.post('/scraps', { asset_id: form.asset_id, remark: form.remark }); ElMessage.success('报废完成'); form.asset_id = null; form.remark = ''; fetch() }
  finally { saving.value = false }
}

onMounted(() => fetch())
</script>
