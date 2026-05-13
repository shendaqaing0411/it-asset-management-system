<template>
  <el-card>
    <h3 style="margin-bottom:16px">资产汇总</h3>
    <el-row :gutter="16">
      <el-col :span="4" v-for="card in cards" :key="card.label">
        <div style="background:#fff;border:1px solid #e6e6e6;border-radius:8px;padding:20px;text-align:center">
          <div :style="{color:card.color,fontSize:'28px',fontWeight:'bold'}">{{ card.value }}</div>
          <div style="color:#999;fontSize:13px;marginTop:4px">{{ card.label }}</div>
        </div>
      </el-col>
    </el-row>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'
const cards = ref([
  { label: '资产总数', value: 0, color: '#409eff' },
  { label: '在库', value: 0, color: '#67c23a' },
  { label: '使用中', value: 0, color: '#e6a23c' },
  { label: '维修中', value: 0, color: '#f56c6c' },
  { label: '借出', value: 0, color: '#909399' },
  { label: '总价值', value: '¥0', color: '#722ed1' }
])
onMounted(async () => {
  const s = await api.get('/report/summary')
  cards.value[0].value = s.data.total; cards.value[1].value = s.data.in_stock
  cards.value[2].value = s.data.in_use || 0; cards.value[3].value = s.data.repairing || 0
  cards.value[4].value = s.data.borrowed || 0; cards.value[5].value = '¥' + (s.data.total_value || 0).toLocaleString()
})
</script>
