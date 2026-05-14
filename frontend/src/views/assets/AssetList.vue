<template>
  <div>
    <el-card>
      <el-form :inline="true" :model="query" size="small">
        <el-form-item label="关键字"><el-input v-model="query.keyword" placeholder="编号/名称/序列号" clearable /></el-form-item>
        <el-form-item label="分类"><el-select v-model="query.category_id" clearable><el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" /></el-select></el-form-item>
        <el-form-item label="状态"><el-select v-model="query.status" clearable><el-option label="在库" value="in_stock" /><el-option label="使用中" value="in_use" /><el-option label="借出" value="borrowed" /><el-option label="维修中" value="repairing" /><el-option label="已报废" value="scrapped" /></el-select></el-form-item>
        <el-form-item><el-button type="primary" @click="fetch">查询</el-button><el-button @click="reset">重置</el-button><el-button type="success" @click="$router.push('/assets/form')">新增资产</el-button><el-button @click="showImport = true"><el-icon style="margin-right:4px"><Upload /></el-icon>批量导入</el-button></el-form-item>
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
    <!-- 批量导入 -->
    <el-dialog v-model="showImport" title="批量导入资产" width="550px" @closed="importResult = null">
      <el-steps :active="importStep" align-center style="margin-bottom:24px">
        <el-step title="下载模板" />
        <el-step title="上传文件" />
        <el-step title="导入完成" />
      </el-steps>
      <div v-if="importStep === 0" style="text-align:center;padding:20px 0">
        <p style="margin-bottom:16px;color:#666">请先下载标准模板，按格式填写资产信息后上传</p>
        <el-button type="primary" @click="downloadTemplate">
          <el-icon style="margin-right:4px"><Download /></el-icon>下载 Excel 模板
        </el-button>
        <div style="margin-top:24px;text-align:left;background:#f5f7fa;padding:16px;border-radius:8px;font-size:13px;color:#666;line-height:1.8">
          <p style="font-weight:600;margin-bottom:8px;color:#333">模板填写说明：</p>
          <p>• <b>资产名称</b> 和 <b>分类ID</b> 为必填项</p>
          <p>• 分类ID 见「系统管理 → 分类管理」</p>
          <p>• 仓库ID / 部门ID / 供应商ID 可选，留空则不关联</p>
          <p>• 采购日期 / 保修到期 格式为 YYYY-MM-DD</p>
          <p>• 模板第一行是示例数据，导入前请删除或覆盖</p>
        </div>
        <el-button type="primary" style="margin-top:20px" @click="importStep = 1">已下载，下一步</el-button>
      </div>
      <div v-else-if="importStep === 1" style="padding:20px 0">
        <el-upload ref="uploadRef" drag :auto-upload="false" :limit="1" accept=".xlsx,.xls" :on-change="onFileChange" :on-remove="onFileRemove">
          <el-icon :size="48" style="color:#5b7cfa"><UploadFilled /></el-icon>
          <div style="margin-top:8px">将 Excel 文件拖到此处，或点击选择</div>
          <template #tip><div style="font-size:12px;color:#999;margin-top:8px">仅支持 .xlsx / .xls 格式</div></template>
        </el-upload>
        <div style="text-align:center;margin-top:20px">
          <el-button @click="importStep = 0">上一步</el-button>
          <el-button type="primary" @click="doImport" :loading="importing" :disabled="!importFile">开始导入</el-button>
        </div>
      </div>
      <div v-else style="text-align:center;padding:20px 0">
        <el-result :icon="importErrors.length ? 'warning' : 'success'" :title="importResult?.message || '导入完成'">
          <template #sub-title>
            <p>成功导入 <b>{{ importResult?.count || 0 }}</b> 条资产</p>
            <div v-if="importErrors.length" style="text-align:left;margin-top:12px;max-height:200px;overflow-y:auto">
              <p v-for="(e, i) in importErrors" :key="i" style="font-size:12px;color:#f56c6c;line-height:1.6">{{ e }}</p>
            </div>
          </template>
        </el-result>
        <el-button type="primary" @click="showImport = false; fetch()">完成</el-button>
        <el-button @click="importStep = 0; importFile = null; importResult = null; importErrors = []">继续导入</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
// 资产列表：多条件查询、分页展示、状态标签、二维码弹窗、删除确认、批量导入
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../../api'

const loading = ref(false)
const items = ref([])
const total = ref(0)
const categories = ref([])
const query = reactive({ keyword: '', category_id: null, status: '', page: 1 })
const qrVisible = ref(false)
const qrSrc = ref('')
const qrLabel = ref('')

// 批量导入
const showImport = ref(false)
const importStep = ref(0)
const importFile = ref(null)
const importing = ref(false)
const importResult = ref(null)
const importErrors = ref([])
const uploadRef = ref(null)

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

// ---- 批量导入 ----
function downloadTemplate() {
  window.open('/api/assets/import/template', '_blank')
}

function onFileChange(file) {
  importFile.value = file.raw
}

function onFileRemove() {
  importFile.value = null
}

async function doImport() {
  if (!importFile.value) return
  importing.value = true
  try {
    const fd = new FormData()
    fd.append('file', importFile.value)
    const res = await api.post('/assets/import', fd)  // axios 自动设置 Content-Type 与 boundary
    importResult.value = res.data
    importErrors.value = res.data.errors || []
    importStep.value = 2
  } catch {
    ElMessage.error('导入失败，请检查文件格式')
  } finally { importing.value = false }
}

onMounted(async () => {
  const res = await api.get('/categories')
  categories.value = res.data
  fetch()
})
</script>
