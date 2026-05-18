<template>
  <el-card>
    <h3 style="margin-bottom:16px">入库管理</h3>
    <el-form :model="form" ref="formRef" :rules="rules" label-width="100px" style="max-width:600px">
      <el-form-item label="资产" prop="asset_id">
        <el-select v-model="form.asset_id" filterable remote :remote-method="searchAssets" :loading="searching" placeholder="搜索资产编号/名称" style="width:100%">
          <el-option v-for="a in assetOptions" :key="a.id" :label="`${a.asset_no} - ${a.name}`" :value="a.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="入库类型" prop="type"><el-select v-model="form.type" style="width:100%"><el-option label="采购入库" value="采购入库" /><el-option label="借调入库" value="借调入库" /><el-option label="盘盈入库" value="盘盈入库" /></el-select></el-form-item>
      <el-form-item label="目标仓库"><el-select v-model="form.to_warehouse_id" style="width:100%"><el-option v-for="w in warehouses" :key="w.id" :label="w.name" :value="w.id" /></el-select></el-form-item>
      <el-form-item label="数量"><el-input-number v-model="form.quantity" :min="1" style="width:100%" /></el-form-item>
      <el-form-item label="备注"><el-input v-model="form.remark" type="textarea" /></el-form-item>
      <el-form-item><el-button type="primary" @click="submit" :loading="saving">确认入库</el-button></el-form-item>
      <el-form-item><el-button @click="handleExport"><el-icon style="margin-right:4px"><Download /></el-icon>导出</el-button></el-form-item>
    </el-form>
    <el-divider />
    <h4 style="margin-bottom:8px">最近入库记录</h4>
    <el-table :data="records" size="small">
      <el-table-column prop="asset_no" label="资产编号" width="140" />
      <el-table-column prop="type" label="类型" width="100" />
      <el-table-column prop="operate_date" label="日期" width="120" />
      <el-table-column prop="remark" label="备注" show-overflow-tooltip />
    </el-table>
  </el-card>
</template>

<script setup>
// 入库管理：远程搜索资产、选择入库类型和目标仓库、展示最近入库记录
import { ref, reactive, onMounted } from 'vue'
import api, { downloadCsv } from '../../api'
import { ElMessage } from 'element-plus'

const formRef = ref(null)
const saving = ref(false)
const searching = ref(false)
const assetOptions = ref([])
const warehouses = ref([])
const records = ref([])
const form = reactive({ asset_id: null, type: '采购入库', quantity: 1, to_warehouse_id: null, remark: '' })
const rules = { asset_id: [{ required: true, message: '请选择资产', trigger: 'change' }], type: [{ required: true, message: '请选择类型', trigger: 'change' }] }

async function searchAssets(q) {
  if (!q) return
  searching.value = true
  try { const res = await api.get('/assets', { params: { keyword: q, page_size: 20 } }); assetOptions.value = res.data.items }
  finally { searching.value = false }
}

async function submit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try { await api.post('/stock/in', form); ElMessage.success('入库成功'); form.asset_id = null; form.remark = ''; loadRecords() }
  finally { saving.value = false }
}

async function loadRecords() {
  const res = await api.get('/stock/records', { params: { type: '采购入库,借调入库', page_size: 10 } })
  records.value = res.data.items
}

function handleExport() { downloadCsv('/stock/records?format=csv') }

onMounted(async () => {
  const w = await api.get('/warehouses'); warehouses.value = w.data
  loadRecords()
})
</script>
