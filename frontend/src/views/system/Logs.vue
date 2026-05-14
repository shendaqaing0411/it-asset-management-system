<template>
  <el-card>
    <el-form :inline="true" :model="query" size="small" style="margin-bottom:16px">
      <el-form-item label="日期范围">
        <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" style="width:260px" />
      </el-form-item>
      <el-form-item label="关键字">
        <el-input v-model="query.keyword" placeholder="操作人/操作内容" clearable style="width:200px" @keyup.enter="fetch" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="fetch">查询</el-button>
        <el-button @click="reset">重置</el-button>
      </el-form-item>
    </el-form>
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
// 操作日志：日期范围 + 关键字筛选，分页展示（只读）
import { ref, reactive, onMounted } from 'vue'
import api from '../../api'

const loading = ref(false)
const items = ref([])
const total = ref(0)
const page = ref(1)
const dateRange = ref(null)
const query = reactive({ keyword: '' })

async function fetch() {
  loading.value = true
  try {
    const params = { page: page.value }
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    if (query.keyword) params.keyword = query.keyword
    const r = await api.get('/logs', { params })
    items.value = r.data.items
    total.value = r.data.total
  } finally { loading.value = false }
}

function reset() {
  dateRange.value = null
  query.keyword = ''
  page.value = 1
  fetch()
}

onMounted(() => fetch())
</script>
