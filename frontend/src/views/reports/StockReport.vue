<template>
  <el-card>
    <h3 style="margin-bottom:16px">库存统计</h3>
    <!-- 二级类目统计 -->
    <h4 style="margin-bottom:12px">按二级类目统计</h4>
    <div v-for="parent in data.by_sub_category" :key="parent.id" style="margin-bottom:16px">
      <el-tag type="primary" size="small" style="margin-bottom:8px">{{ parent.name }}（{{ parent.count }} 件 / ¥{{ (parent.value || 0).toLocaleString() }}）</el-tag>
      <el-table :data="parent.children" size="small" border>
        <el-table-column prop="name" label="二级类目" />
        <el-table-column prop="count" label="数量" width="100" />
        <el-table-column prop="value" label="总价值" width="150">
          <template #default="{row}">¥{{ (row.value || 0).toLocaleString() }}</template>
        </el-table-column>
      </el-table>
    </div>
    <el-empty v-if="!data.by_sub_category?.length" description="暂无二级类目数据" :image-size="60" />
    <el-divider />
    <el-row :gutter="16">
      <el-col :span="12">
        <h4>按分类统计</h4>
        <el-table :data="data.by_category" size="small">
          <el-table-column prop="name" label="分类" />
          <el-table-column prop="count" label="数量" />
          <el-table-column prop="value" label="总价值"><template #default="{row}">¥{{ (row.value || 0).toLocaleString() }}</template></el-table-column>
        </el-table>
      </el-col>
      <el-col :span="12">
        <h4>按状态统计</h4>
        <el-table :data="data.by_status" size="small">
          <el-table-column prop="status" label="状态"><template #default="{row}">{{ statusMap[row.status] || row.status }}</template></el-table-column>
          <el-table-column prop="count" label="数量" />
        </el-table>
      </el-col>
    </el-row>
  </el-card>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import api from '../../api'
const data = ref({ by_category: [], by_status: [], by_dept: [], by_sub_category: [] })
const statusMap = {
  in_stock: '在库',
  in_use: '使用中',
  borrowed: '借出',
  repairing: '维修中',
  scrapped: '已报废'
}
let abortController = null
onMounted(async () => {
  try {
    abortController = new AbortController()
    const res = await api.get('/report/stock', { signal: abortController.signal })
    data.value = res.data
  } catch (err) {
    if (err?.name === 'CanceledError' || err?.code === 'ERR_CANCELED') return
  }
})
onBeforeUnmount(() => {
  if (abortController) abortController.abort()
})
</script>
