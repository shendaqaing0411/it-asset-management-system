<template>
  <el-card>
    <div style="margin-bottom:16px;display:flex;gap:12px;align-items:center">
      <el-select v-model="filterModule" placeholder="全部模块" clearable style="width:140px" @change="fetch">
        <el-option label="资产管理" value="assets" />
        <el-option label="库存管理" value="stock" />
        <el-option label="维保管理" value="repairs" />
        <el-option label="系统管理" value="system" />
      </el-select>
      <el-button type="primary" @click="add">新增字段</el-button>
    </div>
    <el-table :data="items" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="module" label="模块" width="100">
        <template #default="{row}">{{ moduleLabel(row.module) }}</template>
      </el-table-column>
      <el-table-column prop="field_key" label="字段标识" width="140" />
      <el-table-column prop="field_name" label="字段名称" width="140" />
      <el-table-column prop="field_type" label="字段类型" width="100">
        <template #default="{row}">{{ typeLabel(row.field_type) }}</template>
      </el-table-column>
      <el-table-column prop="is_required" label="是否必填" width="80">
        <template #default="{row}">{{ row.is_required ? '是' : '否' }}</template>
      </el-table-column>
      <el-table-column prop="sort_order" label="排序" width="70" />
      <el-table-column prop="options" label="选项" min-width="150">
        <template #default="{row}">{{ row.options || '-' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{row}">
          <el-button link type="primary" @click="edit(row)">编辑</el-button>
          <el-popconfirm title="确认删除？" @confirm="handleDelete(row.id)">
            <template #reference><el-button link type="danger">删除</el-button></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="visible" :title="editing ? '编辑字段' : '新增字段'" width="520px" @closed="resetForm">
      <el-form :model="form" label-width="90px">
        <el-form-item label="所属模块">
          <el-select v-model="form.module" style="width:100%">
            <el-option label="资产管理" value="assets" />
            <el-option label="库存管理" value="stock" />
            <el-option label="维保管理" value="repairs" />
            <el-option label="系统管理" value="system" />
          </el-select>
        </el-form-item>
        <el-form-item label="字段标识">
          <el-input v-model="form.field_key" placeholder="英文字段标识，如 custom_field_1" />
        </el-form-item>
        <el-form-item label="字段名称">
          <el-input v-model="form.field_name" placeholder="显示名称，如 采购批次" />
        </el-form-item>
        <el-form-item label="字段类型">
          <el-select v-model="form.field_type" style="width:100%">
            <el-option label="文本" value="text" />
            <el-option label="数字" value="number" />
            <el-option label="下拉选择" value="select" />
            <el-option label="日期" value="date" />
          </el-select>
        </el-form-item>
        <el-form-item label="是否必填">
          <el-switch v-model="form.is_required" :active-value="1" :inactive-value="0" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="选项" v-if="form.field_type === 'select'">
          <el-input v-model="form.options" placeholder='JSON格式，如 ["选项A","选项B"]' />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
// 数据字典：管理各模块的自定义字段，支持 text/number/select/date 四种类型
import { ref, reactive, onMounted } from 'vue'
import api from '../../api'
import { ElMessage } from 'element-plus'

const items = ref([])
const visible = ref(false)
const editing = ref(null)
const filterModule = ref('')
const form = reactive({
  module: 'assets',
  field_key: '',
  field_name: '',
  field_type: 'text',
  sort_order: 0,
  is_required: 0,
  options: ''
})

const moduleLabels = { assets: '资产管理', stock: '库存管理', repairs: '维保管理', system: '系统管理' }
const typeLabels = { text: '文本', number: '数字', select: '下拉选择', date: '日期' }
function moduleLabel(m) { return moduleLabels[m] || m }
function typeLabel(t) { return typeLabels[t] || t }

async function fetch() {
  const params = filterModule.value ? { module: filterModule.value } : {}
  const r = await api.get('/dict/fields', { params })
  items.value = r.data
}

function add() {
  editing.value = null
  resetForm()
  visible.value = true
}

function edit(row) {
  editing.value = row
  form.module = row.module
  form.field_key = row.field_key
  form.field_name = row.field_name
  form.field_type = row.field_type
  form.sort_order = row.sort_order
  form.is_required = row.is_required
  form.options = row.options || ''
  visible.value = true
}

function resetForm() {
  form.module = 'assets'
  form.field_key = ''
  form.field_name = ''
  form.field_type = 'text'
  form.sort_order = 0
  form.is_required = 0
  form.options = ''
}

async function submit() {
  if (!form.field_key || !form.field_name) {
    ElMessage.warning('请填写字段标识和字段名称')
    return
  }
  const payload = { ...form }
  // 非 select 类型清空 options
  if (payload.field_type !== 'select') payload.options = null
  if (editing.value) {
    // 更新时 module 和 field_key 不可修改
    const { module, field_key, ...updateData } = payload
    await api.put(`/dict/fields/${editing.value.id}`, updateData)
  } else {
    await api.post('/dict/fields', payload)
  }
  ElMessage.success('保存成功')
  visible.value = false
  fetch()
}

async function handleDelete(id) {
  await api.delete(`/dict/fields/${id}`)
  ElMessage.success('已删除')
  fetch()
}

onMounted(() => fetch())
</script>
