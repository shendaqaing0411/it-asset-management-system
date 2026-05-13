<template>
  <el-card>
    <el-button type="primary" @click="add" style="margin-bottom:16px">新增部门</el-button>
    <el-table :data="items" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="部门名称" />
      <el-table-column label="操作" width="160">
        <template #default="{row}">
          <el-button link type="primary" @click="edit(row)">编辑</el-button>
          <el-popconfirm title="确认删除？" @confirm="handleDelete(row.id)"><template #reference><el-button link type="danger">删除</el-button></template></el-popconfirm>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="visible" :title="editing ? '编辑部门' : '新增部门'" width="400px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="排序"><el-input-number v-model="form.sort_order" :min="0" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="visible = false">取消</el-button><el-button type="primary" @click="submit">保存</el-button></template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '../../api'
import { ElMessage } from 'element-plus'
const items = ref([])
const visible = ref(false)
const editing = ref(false)
const form = reactive({ name: '', parent_id: 0, sort_order: 0 })

async function fetch() { const r = await api.get('/departments'); items.value = r.data }
function add() { editing.value = false; form.name = ''; form.sort_order = 0; visible.value = true }
function edit(row) { editing.value = row; form.name = row.name; form.sort_order = row.sort_order; visible.value = true }
async function submit() {
  if (editing.value) { await api.put(`/departments/${editing.value.id}`, form) }
  else { await api.post('/departments', form) }
  ElMessage.success('保存成功'); visible.value = false; fetch()
}
async function handleDelete(id) { await api.delete(`/departments/${id}`); ElMessage.success('已删除'); fetch() }
onMounted(() => fetch())
</script>
