<template>
  <el-card>
    <h3 style="margin-bottom:16px">出入库报表</h3>
    <el-form :inline="true" :model="query" size="small">
      <el-form-item label="开始日期"><el-date-picker v-model="query.start_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
      <el-form-item label="结束日期"><el-date-picker v-model="query.end_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
      <el-form-item label="类型"><el-select v-model="query.type" clearable><el-option label="采购入库" value="采购入库" /><el-option label="领用出库" value="领用出库" /><el-option label="借用出库" value="借用出库" /><el-option label="归还" value="归还" /><el-option label="报废" value="报废" /></el-select></el-form-item>
      <el-form-item><el-button type="primary" @click="fetch">查询</el-button></el-form-item>
    </el-form>
    <el-row :gutter="16" style="margin-bottom:16px">
      <el-col :span="4" v-for="s in summary" :key="s.type"><el-tag>{{ s.type }}: {{ s.count }}</el-tag></el-col>
    </el-row>
    <el-table :data="records" stripe size="small">
      <el-table-column prop="asset_no" label="资产编号" width="140" />
      <el-table-column prop="asset_name" label="资产名称" />
      <el-table-column prop="type" label="类型" width="100" />
      <el-table-column prop="operate_date" label="日期" width="120" />
      <el-table-column prop="remark" label="备注" show-overflow-tooltip />
    </el-table>
  </el-card>
</template>

<script setup>
// 出入库报表：按日期范围和类型筛选，展示明细记录与汇总统计
import { ref, reactive, onMounted } from 'vue'
import api from '../../api'
const records = ref([])
const summary = ref([])
const query = reactive({ start_date: '', end_date: '', type: '' })

async function fetch() {
  const res = await api.get('/report/inout', { params: { ...query, type: query.type || undefined } })
  records.value = res.data.records
  summary.value = res.data.summary
}
onMounted(() => fetch())
</script>
