<template>
  <el-card>
    <el-button type="primary" @click="add" style="margin-bottom:16px">新增供应商</el-button>
    <el-table :data="items" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="contact" label="联系人" width="100" />
      <el-table-column prop="phone" label="电话" width="140" />
      <el-table-column prop="address" label="地址" show-overflow-tooltip />
      <el-table-column label="操作" width="160">
        <template #default="{row}">
          <el-button link type="primary" @click="edit(row)">编辑</el-button>
          <el-popconfirm title="确认删除？" @confirm="handleDelete(row.id)"><template #reference><el-button link type="danger">删除</el-button></template></el-popconfirm>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="visible" :title="editing ? '编辑供应商' : '新增供应商'" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="联系人"><el-input v-model="form.contact" /></el-form-item>
        <el-form-item label="电话"><el-input v-model="form.phone" /></el-form-item>
        <el-form-item label="地址"><el-input v-model="form.address" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.remark" type="textarea" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="visible = false">取消</el-button><el-button type="primary" @click="submit">保存</el-button></template>
    </el-dialog>
  </el-card>
</template>

<script setup>
// 供应商管理：名称/联系人/电话/地址/备注的 CRUD
import { ref, reactive, onMounted } from 'vue'
import api from '../../api'
import { ElMessage } from 'element-plus'
const items = ref([])
const visible = ref(false)
const editing = ref(false)
const form = reactive({ name: '', contact: '', phone: '', address: '', remark: '' })

async function fetch() { const r = await api.get('/suppliers'); items.value = r.data }
function add() { editing.value = false; Object.keys(form).forEach(k => form[k] = ''); visible.value = true }
function edit(row) { editing.value = row; Object.assign(form, { name: row.name, contact: row.contact, phone: row.phone, address: row.address, remark: row.remark }); visible.value = true }
async function submit() {
  if (editing.value) { await api.put(`/suppliers/${editing.value.id}`, form) }
  else { await api.post('/suppliers', form) }
  ElMessage.success('保存成功'); visible.value = false; fetch()
}
async function handleDelete(id) { await api.delete(`/suppliers/${id}`); ElMessage.success('已删除'); fetch() }
onMounted(() => fetch())
</script>
