<template>
  <el-card>
    <h3 style="margin-bottom:16px">报废管理</h3>

    <!-- 报废表单 -->
    <el-form :model="form" ref="formRef" :rules="rules" label-width="120px" style="max-width:700px;margin-bottom:20px">
      <el-form-item label="资产" prop="asset_id">
        <el-select v-model="form.asset_id" filterable remote :remote-method="searchAssets" :loading="searching" placeholder="搜索资产" style="width:100%" @change="onAssetChange">
          <el-option v-for="a in assetOptions" :key="a.id" :label="`${a.asset_no} - ${a.name}`" :value="a.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="报废原因" prop="scrap_reason">
        <el-radio-group v-model="form.scrap_reason">
          <el-radio value="自然老化">自然老化</el-radio>
          <el-radio value="人为损坏">人为损坏</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item v-if="form.scrap_reason === '自然老化' && selectedAsset.purchase_lifespan_years" label="匹配使用年限">
        <el-switch v-model="form.aging_match" active-text="是" inactive-text="否" :active-value="1" :inactive-value="0" />
        <span style="margin-left:8px;color:#999;font-size:12px">使用年限：{{ selectedAsset.purchase_lifespan_years }} 年</span>
      </el-form-item>
      <el-form-item v-if="form.scrap_reason === '人为损坏'" label="损坏责任人" prop="damage_responsible">
        <el-input v-model="form.damage_responsible" placeholder="请输入损坏责任人" />
      </el-form-item>
      <el-form-item label="报废日期" prop="scrap_date">
        <el-date-picker v-model="form.scrap_date" type="date" style="width:100%" value-format="YYYY-MM-DD" />
      </el-form-item>
      <el-form-item label="备注"><el-input v-model="form.remark" type="textarea" /></el-form-item>
      <el-form-item><el-button type="danger" @click="handleScrap" :loading="saving">确认报废</el-button></el-form-item>
    </el-form>

    <el-divider />
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
      <h4>报废记录</h4>
      <el-button size="small" @click="handleExport"><el-icon style="margin-right:4px"><Download /></el-icon>导出</el-button>
    </div>
    <el-table :data="items" stripe v-loading="loading">
      <el-table-column prop="asset_no" label="资产编号" width="140" />
      <el-table-column prop="asset_name" label="资产名称" />
      <el-table-column prop="scrap_reason" label="报废原因" width="100" />
      <el-table-column label="责任人" width="100">
        <template #default="{row}">{{ row.damage_responsible || '—' }}</template>
      </el-table-column>
      <el-table-column prop="scrap_date" label="报废日期" width="120" />
      <el-table-column prop="remark" label="备注" show-overflow-tooltip />
      <el-table-column prop="create_time" label="操作时间" width="160" />
    </el-table>
    <el-pagination v-model:current-page="page" :total="total" :page-size="20" layout="total, prev, pager, next" @current-change="fetch" style="margin-top:16px" />
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api, { downloadCsv } from '../../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const saving = ref(false)
const searching = ref(false)
const items = ref([])
const total = ref(0)
const page = ref(1)
const assetOptions = ref([])
const selectedAsset = reactive({})
const formRef = ref(null)

const form = reactive({
  asset_id: null,
  scrap_reason: '自然老化',
  aging_match: 0,
  damage_responsible: '',
  scrap_date: null,
  remark: ''
})

const rules = {
  asset_id: [{ required: true, message: '请选择资产', trigger: 'change' }],
  scrap_reason: [{ required: true, message: '请选择报废原因', trigger: 'change' }],
  scrap_date: [{ required: true, message: '请选择报废日期', trigger: 'change' }],
  damage_responsible: [{ required: true, message: '请输入责任人', trigger: 'blur' }]
}

async function fetch() {
  loading.value = true
  try { const res = await api.get('/scraps', { params: { page: page.value } }); items.value = res.data.items; total.value = res.data.total }
  finally { loading.value = false }
}

async function searchAssets(q) {
  if (!q) return
  searching.value = true
  try { const res = await api.get('/assets', { params: { keyword: q, page_size: 20 } }); assetOptions.value = res.data.items }
  finally { searching.value = false }
}

function onAssetChange(val) {
  if (val) {
    const found = assetOptions.value.find(a => a.id === val)
    if (found) Object.assign(selectedAsset, found)
  }
}

async function handleScrap() {
  if (!form.asset_id) { ElMessage.warning('请选择资产'); return }
  await ElMessageBox.confirm('确认报废该资产？此操作不可撤销。', '报废确认', { type: 'warning' })

  const validateRules = { ...rules }
  if (form.scrap_reason === '自然老化') delete validateRules.damage_responsible

  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    const payload = { ...form }
    if (form.scrap_reason === '自然老化') payload.damage_responsible = null
    else payload.aging_match = 0
    await api.post('/scraps', payload)
    ElMessage.success('报废完成')
    Object.assign(form, { asset_id: null, scrap_reason: '自然老化', aging_match: 0, damage_responsible: '', scrap_date: null, remark: '' })
    Object.keys(selectedAsset).forEach(k => delete selectedAsset[k])
    fetch()
  } finally { saving.value = false }
}

function handleExport() { downloadCsv('/scraps?format=csv') }

onMounted(() => fetch())
</script>
