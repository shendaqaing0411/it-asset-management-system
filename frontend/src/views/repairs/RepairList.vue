<template>
  <el-card>
    <el-tag v-if="filterAssetId" type="warning" closable @close="$router.replace('/repairs/list')" style="margin-bottom:12px">筛选资产ID: {{ filterAssetId }}（点击 × 清除筛选）</el-tag>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <el-button type="primary" @click="showDialog = true">新增维修</el-button>
      <el-button @click="handleExport"><el-icon style="margin-right:4px"><Download /></el-icon>导出</el-button>
    </div>
    <el-table :data="items" stripe v-loading="loading">
      <el-table-column prop="asset_no" label="资产编号" width="140" />
      <el-table-column prop="asset_name" label="资产名称" />
      <el-table-column prop="fault_desc" label="故障描述" show-overflow-tooltip />
      <el-table-column prop="repair_type" label="维修类型" width="120" />
      <el-table-column prop="repair_method" label="维修方式" width="120" />
      <el-table-column prop="repair_cost" label="费用" width="100" />
      <el-table-column prop="repair_date" label="报修日期" width="120" />
      <el-table-column prop="finish_date" label="完成日期" width="120" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{row}"><el-tag :type="row.status === 'finished' ? 'success' : row.status === 'fixing' ? 'warning' : 'info'" size="small">{{ row.status === 'finished' ? '已完成' : row.status === 'fixing' ? '维修中' : '待处理' }}</el-tag></template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{row}">
          <el-button link type="primary" @click="editRepair(row)">编辑</el-button>
          <el-button link type="success" @click="finishRepair(row.id)" v-if="row.status !== 'finished'">完成</el-button>
          <el-button link type="warning" @click="handleReturn(row)" v-if="row.status === 'finished' && !row.return_confirmed">返修入库</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination v-model:current-page="page" :total="total" :page-size="20" layout="total, prev, pager, next" @current-change="fetch" style="margin-top:16px" />

    <el-dialog v-model="showDialog" :title="editing ? '编辑维修' : '新增维修'" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="资产"><el-select v-model="form.asset_id" filterable remote :remote-method="searchAssets" placeholder="搜索资产" style="width:100%"><el-option v-for="a in assetOptions" :key="a.id" :label="`${a.asset_no} - ${a.name}`" :value="a.id" /></el-select></el-form-item>
        <el-form-item label="故障描述"><el-input v-model="form.fault_desc" type="textarea" /></el-form-item>
        <el-form-item label="维修类型">
          <el-select v-model="form.repair_type" style="width:100%">
            <el-option label="保修期内维修" value="保修期内维修" />
            <el-option label="保外维修" value="保外维修" />
            <el-option label="厂商送修" value="厂商送修" />
            <el-option label="自行维修" value="自行维修" />
          </el-select>
        </el-form-item>
        <el-form-item label="维修方式">
          <el-select v-model="form.repair_method" style="width:100%" clearable>
            <el-option label="更换配件" value="更换配件" />
            <el-option label="软件修复" value="软件修复" />
            <el-option label="清洁保养" value="清洁保养" />
            <el-option label="返厂维修" value="返厂维修" />
          </el-select>
        </el-form-item>
        <el-form-item label="费用"><el-input-number v-model="form.repair_cost" :min="0" :precision="2" style="width:100%" /></el-form-item>
        <el-form-item label="报修日期"><el-date-picker v-model="form.repair_date" type="date" style="width:100%" value-format="YYYY-MM-DD" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showDialog = false">取消</el-button><el-button type="primary" @click="submitRepair" :loading="saving">保存</el-button></template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api, { downloadCsv } from '../../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const loading = ref(false)
const saving = ref(false)
const items = ref([])
const total = ref(0)
const page = ref(1)
const showDialog = ref(false)
const editing = ref(false)
const assetOptions = ref([])
const filterAssetId = ref(route.query.asset_id ? Number(route.query.asset_id) : null)
const form = reactive({ asset_id: filterAssetId.value || null, fault_desc: '', repair_type: '', repair_method: '', repair_cost: 0, repair_date: null })

async function fetch() {
  loading.value = true
  try {
    const params = { page: page.value }
    if (filterAssetId.value) params.asset_id = filterAssetId.value
    const res = await api.get('/repairs', { params })
    items.value = res.data.items; total.value = res.data.total
  }
  finally { loading.value = false }
}

async function searchAssets(q) {
  if (!q) return
  const res = await api.get('/assets', { params: { keyword: q, page_size: 20 } })
  assetOptions.value = res.data.items
}

function editRepair(row) {
  Object.assign(form, { asset_id: row.asset_id, fault_desc: row.fault_desc, repair_type: row.repair_type, repair_method: row.repair_method || '', repair_cost: row.repair_cost, repair_date: row.repair_date })
  editing.value = { id: row.id }
  showDialog.value = true
}

async function submitRepair() {
  saving.value = true
  try {
    const payload = { ...form }
    if (!payload.repair_method) delete payload.repair_method
    if (editing.value) {
      await api.put(`/repairs/${editing.value.id}`, payload)
    } else {
      await api.post('/repairs', payload)
    }
    ElMessage.success('保存成功'); showDialog.value = false; editing.value = false
    Object.assign(form, { asset_id: null, fault_desc: '', repair_type: '', repair_method: '', repair_cost: 0, repair_date: null })
    fetch()
  } finally { saving.value = false }
}

async function finishRepair(id) {
  await api.put(`/repairs/${id}`, { status: 'finished', finish_date: new Date().toISOString().slice(0, 10) })
  ElMessage.success('维修已完成'); fetch()
}

async function handleReturn(row) {
  try {
    await ElMessageBox.confirm('确认该资产已维修完成并返修入库？', '返修入库确认', { type: 'info' })
    await api.post(`/repairs/${row.id}/return`, { return_date: new Date().toISOString().slice(0, 10) })
    ElMessage.success('返修入库完成'); fetch()
  } catch { /* cancelled */ }
}

function handleExport() { downloadCsv('/repairs?format=csv') }

onMounted(() => fetch())
</script>
