<template>
  <el-card>
    <el-button type="primary" @click="add" style="margin-bottom:16px">新增仓库</el-button>
    <el-table :data="items" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="仓库名称" />
      <el-table-column prop="location" label="位置" />
      <el-table-column label="操作" width="160">
        <template #default="{row}">
          <el-button link type="primary" @click="edit(row)">编辑</el-button>
          <el-popconfirm title="确认删除？" @confirm="handleDelete(row.id)"><template #reference><el-button link type="danger">删除</el-button></template></el-popconfirm>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="visible" :title="editing ? '编辑仓库' : '新增仓库'" width="400px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="位置"><el-input v-model="form.location" /></el-form-item>
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
const form = reactive({ name: '', location: '' })

async function fetch() { const r = await api.get('/warehouses'); items.value = r.data }
function add() { editing.value = false; form.name = ''; form.location = ''; visible.value = true }
function edit(row) { editing.value = row; form.name = row.name; form.location = row.location; visible.value = true }
async function submit() {
  if (editing.value) { await api.put(`/warehouses/${editing.value.id}`, form) }
  else { await api.post('/warehouses', form) }
  ElMessage.success('保存成功'); visible.value = false; fetch()
}
async function handleDelete(id) { await api.delete(`/warehouses/${id}`); ElMessage.success('已删除'); fetch() }
onMounted(() => fetch())
</script>
