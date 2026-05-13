<template>
  <el-card>
    <el-button type="primary" @click="add" style="margin-bottom:16px">新增预警规则</el-button>
    <el-table :data="items" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="warehouse_name" label="仓库" width="100" />
      <el-table-column prop="category_name" label="分类" width="100" />
      <el-table-column prop="min_stock" label="最低库存" width="100" />
      <el-table-column prop="max_stock" label="最高库存" width="100" />
      <el-table-column label="操作" width="160">
        <template #default="{row}">
          <el-button link type="primary" @click="edit(row)">编辑</el-button>
          <el-popconfirm title="确认删除？" @confirm="handleDelete(row.id)"><template #reference><el-button link type="danger">删除</el-button></template></el-popconfirm>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="visible" :title="editing ? '编辑预警' : '新增预警'" width="400px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="仓库"><el-select v-model="form.warehouse_id" style="width:100%"><el-option v-for="w in warehouses" :key="w.id" :label="w.name" :value="w.id" /></el-select></el-form-item>
        <el-form-item label="分类"><el-select v-model="form.category_id" style="width:100%"><el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" /></el-select></el-form-item>
        <el-form-item label="最低库存"><el-input-number v-model="form.min_stock" :min="0" /></el-form-item>
        <el-form-item label="最高库存"><el-input-number v-model="form.max_stock" :min="0" /></el-form-item>
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
const warehouses = ref([])
const categories = ref([])
const form = reactive({ warehouse_id: null, category_id: null, min_stock: 5, max_stock: 100 })

async function fetch() { const r = await api.get('/warnings'); items.value = r.data }
function add() { editing.value = false; form.warehouse_id = null; form.category_id = null; form.min_stock = 5; form.max_stock = 100; visible.value = true }
function edit(row) { editing.value = row; Object.assign(form, { warehouse_id: row.warehouse_id, category_id: row.category_id, min_stock: row.min_stock, max_stock: row.max_stock }); visible.value = true }
async function submit() {
  if (editing.value) { await api.put(`/warnings/${editing.value.id}`, form) }
  else { await api.post('/warnings', form) }
  ElMessage.success('保存成功'); visible.value = false; fetch()
}
async function handleDelete(id) { await api.delete(`/warnings/${id}`); ElMessage.success('已删除'); fetch() }
onMounted(async () => {
  const [w, c] = await Promise.all([api.get('/warehouses'), api.get('/categories')])
  warehouses.value = w.data; categories.value = c.data; fetch()
})
</script>
