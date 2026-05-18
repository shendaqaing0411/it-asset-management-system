<template>
  <el-card v-loading="loading">
    <el-tabs v-model="activeTab" @tab-change="fetch">
      <el-tab-pane label="我的申请" name="my" />
      <el-tab-pane v-if="isApprover" label="待审批" name="pending" />
      <el-tab-pane v-if="isAdmin" label="待出库" name="approved" />
    </el-tabs>

    <!-- 我的申请：新增按钮 -->
    <div v-if="activeTab === 'my'" style="margin-bottom:16px;display:flex;justify-content:space-between">
      <el-button type="primary" @click="showApplyDialog = true">新增申请</el-button>
      <el-button @click="handleExport"><el-icon style="margin-right:4px"><Download /></el-icon>导出</el-button>
    </div>

    <el-table :data="items" stripe>
      <el-table-column prop="asset_no" label="资产编号" width="140" />
      <el-table-column prop="asset_name" label="资产名称" show-overflow-tooltip />
      <el-table-column prop="apply_reason" label="申请原因" show-overflow-tooltip />
      <el-table-column prop="apply_date" label="申请日期" width="120" />
      <el-table-column prop="applicant_name" v-if="activeTab !== 'my'" label="申请人" width="100" />
      <el-table-column label="状态" width="100">
        <template #default="{row}">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column v-if="activeTab === 'pending'" label="操作" width="180">
        <template #default="{row}">
          <el-button link type="success" @click="handleApprove(row, true)">通过</el-button>
          <el-button link type="danger" @click="handleReject(row)">拒绝</el-button>
        </template>
      </el-table-column>
      <el-table-column v-if="activeTab === 'approved'" label="操作" width="120">
        <template #default="{row}">
          <el-button link type="primary" @click="handleDeliver(row)">确认出库</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination v-model:current-page="page" :total="total" :page-size="20" layout="total, prev, pager, next" @current-change="fetch" style="margin-top:16px" />

    <!-- 新增申请 -->
    <el-dialog v-model="showApplyDialog" title="新增领用申请" width="450px">
      <el-form :model="applyForm" label-width="80px">
        <el-form-item label="资产">
          <el-select v-model="applyForm.asset_id" filterable remote :remote-method="searchAssets" placeholder="搜索资产" style="width:100%">
            <el-option v-for="a in assetOptions" :key="a.id" :label="`${a.asset_no} - ${a.name}`" :value="a.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="申请原因"><el-input v-model="applyForm.apply_reason" type="textarea" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showApplyDialog = false">取消</el-button><el-button type="primary" @click="submitApply" :loading="saving">提交</el-button></template>
    </el-dialog>

    <!-- 拒绝原因 -->
    <el-dialog v-model="showRejectDialog" title="拒绝原因" width="400px">
      <el-input v-model="rejectReason" type="textarea" placeholder="请填写拒绝原因" />
      <template #footer><el-button @click="showRejectDialog = false">取消</el-button><el-button type="danger" @click="confirmReject" :loading="saving">确认拒绝</el-button></template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import api, { downloadCsv } from '../../api'
import { ElMessage } from 'element-plus'

const user = JSON.parse(localStorage.getItem('user') || '{}')
const isApprover = computed(() => ['super_admin', 'asset_admin', 'dept_manager'].includes(user.role))
const isAdmin = computed(() => ['super_admin', 'asset_admin'].includes(user.role))

const loading = ref(false)
const saving = ref(false)
const items = ref([])
const total = ref(0)
const page = ref(1)
const activeTab = ref('my')

const showApplyDialog = ref(false)
const assetOptions = ref([])
const applyForm = reactive({ asset_id: null, apply_reason: '' })

const showRejectDialog = ref(false)
const rejectReason = ref('')
const rejectTarget = ref(null)

const statusMap = { pending: '待审批', approved: '已通过', rejected: '已拒绝', delivered: '已出库' }
const statusTypeMap = { pending: 'warning', approved: 'success', rejected: 'danger', delivered: '' }
function statusLabel(s) { return statusMap[s] || s }
function statusType(s) { return statusTypeMap[s] || 'info' }

async function fetch() {
  loading.value = true
  try {
    const params = { page: page.value }
    if (activeTab.value === 'pending') params.status = 'pending'
    else if (activeTab.value === 'approved') params.status = 'approved'
    const res = await api.get('/approvals', { params })
    items.value = res.data.items || []
    total.value = res.data.total || 0
  } finally { loading.value = false }
}

async function searchAssets(q) {
  if (!q) return
  const res = await api.get('/assets', { params: { keyword: q, page_size: 20 } })
  assetOptions.value = res.data.items
}

async function submitApply() {
  if (!applyForm.asset_id) { ElMessage.warning('请选择资产'); return }
  saving.value = true
  try {
    await api.post('/approvals', { asset_id: applyForm.asset_id, apply_reason: applyForm.apply_reason, dept_id: user.dept_id })
    ElMessage.success('申请已提交')
    showApplyDialog.value = false
    applyForm.asset_id = null; applyForm.apply_reason = ''
    fetch()
  } catch { /* handled by interceptor */ }
  finally { saving.value = false }
}

async function handleApprove(row, approved) {
  saving.value = true
  try {
    await api.put(`/approvals/${row.id}/approve`, { approved })
    ElMessage.success('审批完成')
    fetch()
  } finally { saving.value = false }
}

function handleReject(row) {
  rejectTarget.value = row
  rejectReason.value = ''
  showRejectDialog.value = true
}

async function confirmReject() {
  saving.value = true
  try {
    await api.put(`/approvals/${rejectTarget.value.id}/approve`, { approved: false, reject_reason: rejectReason.value })
    ElMessage.success('已拒绝')
    showRejectDialog.value = false
    fetch()
  } finally { saving.value = false }
}

async function handleDeliver(row) {
  saving.value = true
  try {
    await api.put(`/approvals/${row.id}/deliver`)
    ElMessage.success('出库完成')
    fetch()
  } finally { saving.value = false }
}

function handleExport() { downloadCsv('/approvals?format=csv') }

onMounted(() => fetch())
</script>
