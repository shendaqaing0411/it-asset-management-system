<template>
  <el-card>
    <el-button type="primary" @click="add" style="margin-bottom:16px">新增分类</el-button>
    <el-table :data="displayItems" stripe :row-class-name="rowClass">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="分类名称" min-width="160">
        <template #default="{row}">
          <span :style="{ paddingLeft: row.level === 1 ? '32px' : '0' }">
            <el-tag v-if="row.level === 0" type="primary" size="small" style="margin-right:6px">一级</el-tag>
            <el-tag v-else type="info" size="small" style="margin-right:6px">二级</el-tag>
            {{ row.name }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="上级分类" width="140">
        <template #default="{row}">
          <span v-if="row.parent_name" style="color:#909399">{{ row.parent_name }}</span>
          <span v-else style="color:#c0c4cc">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="sort_order" label="排序" width="60" />
      <el-table-column label="操作" width="160">
        <template #default="{row}">
          <el-button link type="primary" @click="edit(row)">编辑</el-button>
          <el-popconfirm title="确认删除？" @confirm="handleDelete(row.id)"><template #reference><el-button link type="danger">删除</el-button></template></el-popconfirm>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="visible" :title="editing ? '编辑分类' : '新增分类'" width="450px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="上级分类">
          <el-select v-model="form.parent_id" placeholder="无（作为一级类目）" clearable style="width:100%">
            <el-option v-for="p in parentOptions" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序"><el-input-number v-model="form.sort_order" :min="0" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="visible = false">取消</el-button><el-button type="primary" @click="submit">保存</el-button></template>
    </el-dialog>
  </el-card>
</template>

<script setup>
// 分类管理：支持一级/二级类目，树形展示
import { ref, reactive, computed, onMounted } from 'vue'
import api from '../../api'
import { ElMessage } from 'element-plus'

const items = ref([])      // tree data from API
const visible = ref(false)
const editing = ref(false)
const form = reactive({ name: '', parent_id: 0, sort_order: 0 })

// 将树形数据扁平化用于表格展示，一级在前、二级缩进在后
const displayItems = computed(() => {
  const result = []
  for (const parent of items.value) {
    result.push({ ...parent, level: 0, parent_name: '' })
    if (parent.children && parent.children.length) {
      for (const child of parent.children) {
        result.push({ ...child, level: 1, parent_name: parent.name })
      }
    }
  }
  return result
})

// 上级分类选项：仅一级类目，编辑时排除自身
const parentOptions = computed(() => {
  const options = []
  for (const p of items.value) {
    if (editing.value && editing.value.id === p.id) continue
    options.push({ id: p.id, name: p.name })
  }
  return options
})

function rowClass({ row }) {
  return row.level === 0 ? 'parent-row' : 'child-row'
}

async function fetch() {
  const r = await api.get('/categories', { params: { tree: true } })
  items.value = r.data
}

function add() {
  editing.value = false
  form.name = ''
  form.parent_id = 0
  form.sort_order = 0
  visible.value = true
}

function edit(row) {
  editing.value = row
  form.name = row.name
  form.parent_id = row.parent_id || 0
  form.sort_order = row.sort_order
  visible.value = true
}

async function submit() {
  const payload = { name: form.name, parent_id: form.parent_id || 0, sort_order: form.sort_order }
  if (editing.value) {
    await api.put(`/categories/${editing.value.id}`, payload)
  } else {
    await api.post('/categories', payload)
  }
  ElMessage.success('保存成功')
  visible.value = false
  fetch()
}

async function handleDelete(id) {
  await api.delete(`/categories/${id}`)
  ElMessage.success('已删除')
  fetch()
}

onMounted(() => fetch())
</script>

<style scoped>
:deep(.parent-row) {
  font-weight: 600;
  background-color: #f5f7fa;
}
:deep(.child-row) {
  color: #606266;
}
</style>
