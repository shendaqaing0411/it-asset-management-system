<template>
  <el-card>
    <h3 style="margin-bottom:16px">库存统计</h3>
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
          <el-table-column prop="status" label="状态" />
          <el-table-column prop="count" label="数量" />
        </el-table>
      </el-col>
    </el-row>
  </el-card>
</template>

<script setup>
// 库存统计：按分类/状态/部门三个维度展示库存分布
import { ref, onMounted } from 'vue'
import api from '../../api'
const data = ref({ by_category: [], by_status: [], by_dept: [] })
onMounted(async () => { const res = await api.get('/report/stock'); data.value = res.data })
</script>
