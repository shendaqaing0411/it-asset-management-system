<template>
  <el-card>
    <el-table :data="items" stripe v-loading="loading" size="small">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="操作人" width="100" />
      <el-table-column prop="description" label="操作内容" show-overflow-tooltip />
      <el-table-column prop="create_time" label="时间" width="180" />
    </el-table>
    <el-pagination v-model:current-page="page" :total="total" :page-size="50" layout="total, prev, pager, next" @current-change="fetch" style="margin-top:16px" />
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'
const loading = ref(false)
const items = ref([])
const total = ref(0)
const page = ref(1)

async function fetch() {
  loading.value = true
  try { const r = await api.get('/logs', { params: { page: page.value } }); items.value = r.data.items; total.value = r.data.total }
  finally { loading.value = false }
}
onMounted(() => fetch())
</script>
