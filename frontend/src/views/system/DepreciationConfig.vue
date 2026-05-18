<template>
  <el-card>
    <div style="margin-bottom:16px">
      <el-button type="primary" @click="add">新增配置</el-button>
      <span style="margin-left:12px;color:#909399;font-size:13px">按资产分类自定义折旧方法和使用年限，未配置的分类将使用资产自身字段</span>
    </div>
    <el-table :data="items" stripe v-loading="loading">
      <el-table-column prop="category_name" label="资产分类" width="160" />
      <el-table-column prop="parent_name" label="上级分类" width="120">
        <template #default="{row}"><span v-if="row.parent_name">{{ row.parent_name }}</span><span v-else style="color:#c0c4cc">-</span></template>
      </el-table-column>
      <el-table-column prop="method" label="折旧方法" width="120">
        <template #default="{row}">
          <el-tag :type="row.method === 'once' ? 'warning' : 'primary'" size="small">{{ row.method === 'once' ? '一次性' : '直线法' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="useful_life_years" label="使用年限(年)" width="120" />
      <el-table-column prop="salvage_rate" label="残值率" width="100">
        <template #default="{row}">{{ (row.salvage_rate * 100).toFixed(0) }}%</template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{row}">
          <el-button link type="primary" @click="edit(row)">编辑</el-button>
          <el-popconfirm title="确认删除？" @confirm="handleDelete(row.id)"><template #reference><el-button link type="danger">删除</el-button></template></el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="visible" :title="editingId ? '编辑折旧配置' : '新增折旧配置'" width="480px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="资产分类">
          <el-select v-model="form.category_id" placeholder="选择分类" style="width:100%" :disabled="!!editingId">
            <el-option v-for="c in flatCategories" :key="c.id" :label="c.label" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="折旧方法">
          <el-radio-group v-model="form.method">
            <el-radio value="straight">直线法</el-radio>
            <el-radio value="once">一次性</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="使用年限">
          <el-input-number v-model="form.useful_life_years" :min="1" :max="50" />
          <span style="margin-left:8px;color:#909399">年</span>
        </el-form-item>
        <el-form-item label="残值率">
          <el-input-number v-model="form.salvage_rate" :min="0" :max="1" :step="0.05" :precision="2" />
          <span style="margin-left:8px;color:#909399">0~1（如 0.05 表示 5%）</span>
        </el-form-item>
      </el-form>
      <template #footer><el-button @click="visible = false">取消</el-button><el-button type="primary" @click="submit">保存</el-button></template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '../../api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const items = ref([])
const visible = ref(false)
const editingId = ref(null)
const flatCategories = ref([])
const form = reactive({ category_id: null, method: 'straight', useful_life_years: 5, salvage_rate: 0 })

async function loadCategories() {
  const res = await api.get('/categories')
  const result = []
  for (const p of res.data) {
    result.push({ id: p.id, label: p.name })
    if (p.children) {
      for (const c of p.children) {
        result.push({ id: c.id, label: `  └ ${c.name}` })
      }
    }
  }
  flatCategories.value = result
}

async function fetch() {
  loading.value = true
  try {
    const res = await api.get('/depreciation-configs')
    items.value = res.data
  } finally { loading.value = false }
}

function add() {
  editingId.value = null
  form.category_id = null
  form.method = 'straight'
  form.useful_life_years = 5
  form.salvage_rate = 0
  visible.value = true
}

function edit(row) {
  editingId.value = row.id
  form.category_id = row.category_id
  form.method = row.method
  form.useful_life_years = row.useful_life_years
  form.salvage_rate = row.salvage_rate
  visible.value = true
}

async function submit() {
  if (!form.category_id) { ElMessage.warning('请选择分类'); return }
  await api.post('/depreciation-configs', { ...form })
  ElMessage.success('保存成功')
  visible.value = false
  fetch()
}

async function handleDelete(id) {
  await api.delete(`/depreciation-configs/${id}`)
  ElMessage.success('已删除')
  fetch()
}

onMounted(async () => {
  await loadCategories()
  fetch()
})
</script>
