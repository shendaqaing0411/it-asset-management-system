<template>
  <el-card>
    <h3 style="margin-bottom:16px">{{ isEdit ? '编辑资产' : '新增资产' }}</h3>
    <el-form :model="form" ref="formRef" :rules="rules" label-width="100px" style="max-width:700px">
      <el-row :gutter="16">
        <el-col :span="12"><el-form-item label="资产名称" prop="name"><el-input v-model="form.name" /></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="资产分类" prop="category_id"><el-select v-model="form.category_id" style="width:100%"><el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" /></el-select></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="品牌"><el-input v-model="form.brand" /></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="型号"><el-input v-model="form.model" /></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="序列号"><el-input v-model="form.serial_no" /></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="采购价格"><el-input-number v-model="form.purchase_price" :min="0" :precision="2" style="width:100%" /></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="采购日期"><el-date-picker v-model="form.purchase_date" type="date" style="width:100%" value-format="YYYY-MM-DD" /></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="保修到期"><el-date-picker v-model="form.warranty_date" type="date" style="width:100%" value-format="YYYY-MM-DD" /></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="使用部门"><el-select v-model="form.dept_id" clearable style="width:100%"><el-option v-for="d in depts" :key="d.id" :label="d.name" :value="d.id" /></el-select></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="仓库"><el-select v-model="form.warehouse_id" clearable style="width:100%"><el-option v-for="w in warehouses" :key="w.id" :label="w.name" :value="w.id" /></el-select></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="供应商"><el-select v-model="form.supplier_id" clearable style="width:100%"><el-option v-for="s in suppliers" :key="s.id" :label="s.name" :value="s.id" /></el-select></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="存放位置"><el-input v-model="form.location" /></el-form-item></el-col>
        <el-col :span="24"><el-form-item label="备注"><el-input v-model="form.remark" type="textarea" /></el-form-item></el-col>
      </el-row>
      <el-form-item>
        <el-button type="primary" @click="submit" :loading="saving">保存</el-button>
        <el-button @click="$router.back()">取消</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../../api'

const route = useRoute()
const router = useRouter()
const isEdit = !!route.params.id
const formRef = ref(null)
const saving = ref(false)
const form = reactive({
  name: '', category_id: null, brand: '', model: '', serial_no: '',
  purchase_price: 0, purchase_date: null, dept_id: null, warehouse_id: null,
  supplier_id: null, location: '', warranty_date: null, remark: ''
})
const rules = {
  name: [{ required: true, message: '请输入资产名称', trigger: 'blur' }],
  category_id: [{ required: true, message: '请选择分类', trigger: 'change' }]
}
const categories = ref([])
const depts = ref([])
const warehouses = ref([])
const suppliers = ref([])

onMounted(async () => {
  const [c, d, w, s] = await Promise.all([
    api.get('/categories'), api.get('/departments'), api.get('/warehouses'), api.get('/suppliers')
  ])
  categories.value = c.data; depts.value = d.data; warehouses.value = w.data; suppliers.value = s.data
  if (isEdit) {
    const res = await api.get(`/assets/${route.params.id}`)
    Object.assign(form, res.data)
  }
})

async function submit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (isEdit) {
      await api.put(`/assets/${route.params.id}`, form)
    } else {
      await api.post('/assets', form)
    }
    router.push('/assets/list')
  } finally { saving.value = false }
}
</script>
