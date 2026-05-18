<template>
  <el-card>
    <h3 style="margin-bottom:16px">{{ isEdit ? '编辑资产' : '新增资产' }}</h3>
    <el-form :model="form" ref="formRef" :rules="rules" label-width="100px" style="max-width:700px">
      <el-row :gutter="16">
        <el-col :span="12"><el-form-item label="资产名称" prop="name"><el-autocomplete v-model="form.name" :fetch-suggestions="querySearch" placeholder="请输入资产名称" style="width:100%" clearable /></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="资产分类" prop="category_id"><el-select v-model="form.category_id" style="width:100%" placeholder="请选择二级类目"><el-option-group v-for="parent in categoryTree" :key="parent.id" :label="'▎' + parent.name"><el-option v-for="child in parent.children" :key="child.id" :label="child.name" :value="child.id" /></el-option-group></el-select></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="品牌"><el-input v-model="form.brand" /></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="型号"><el-input v-model="form.model" /></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="序列号"><el-input v-model="form.serial_no" /></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="采购价格"><el-input-number v-model="form.purchase_price" :min="0" :precision="2" style="width:100%" /></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="采购日期"><el-date-picker v-model="form.purchase_date" type="date" style="width:100%" value-format="YYYY-MM-DD" /></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="使用年限(年)"><el-input-number v-model="form.purchase_lifespan_years" :min="0" :step="1" style="width:100%" /></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="保修到期"><el-date-picker v-model="form.warranty_date" type="date" style="width:100%" value-format="YYYY-MM-DD" /></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="使用部门"><el-select v-model="form.dept_id" clearable style="width:100%"><el-option v-for="d in depts" :key="d.id" :label="d.name" :value="d.id" /></el-select></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="仓库"><el-select v-model="form.warehouse_id" clearable style="width:100%"><el-option v-for="w in warehouses" :key="w.id" :label="w.name" :value="w.id" /></el-select></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="供应商"><el-select v-model="form.supplier_id" clearable style="width:100%"><el-option v-for="s in suppliers" :key="s.id" :label="s.name" :value="s.id" /></el-select></el-form-item></el-col>
        <el-col :span="12"><el-form-item label="存放位置"><el-input v-model="form.location" /></el-form-item></el-col>
        <el-col :span="24"><el-form-item label="备注"><el-input v-model="form.remark" type="textarea" /></el-form-item></el-col>
        <!-- 数据字典动态字段 -->
        <template v-for="field in dictFields" :key="field.id">
          <el-col :span="12">
            <el-form-item :label="field.field_name" :required="field.is_required === 1">
              <el-input v-if="field.field_type === 'text'" v-model="dictValues[field.field_key]" />
              <el-input-number v-else-if="field.field_type === 'number'" v-model="dictValues[field.field_key]" :precision="2" style="width:100%" />
              <el-select v-else-if="field.field_type === 'select'" v-model="dictValues[field.field_key]" style="width:100%" clearable>
                <el-option v-for="opt in parseOptions(field.options)" :key="opt" :label="opt" :value="opt" />
              </el-select>
              <el-date-picker v-else-if="field.field_type === 'date'" v-model="dictValues[field.field_key]" type="date" style="width:100%" value-format="YYYY-MM-DD" />
              <el-input v-else v-model="dictValues[field.field_key]" />
            </el-form-item>
          </el-col>
        </template>
      </el-row>
      <el-form-item>
        <el-button type="primary" @click="submit" :loading="saving">保存</el-button>
        <el-button @click="$router.back()">取消</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
// 资产登记/编辑表单：根据路由参数区分新增和编辑模式，动态加载分类/部门/仓库/供应商选项
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
  purchase_price: 0, purchase_date: null, purchase_lifespan_years: 0, dept_id: null, warehouse_id: null,
  supplier_id: null, location: '', warranty_date: null, remark: ''
})
const rules = {
  name: [{ required: true, message: '请输入资产名称', trigger: 'blur' }],
  category_id: [{ required: true, message: '请选择分类', trigger: 'change' }]
}
const categories = ref([])
const categoryTree = ref([])
const depts = ref([])
const warehouses = ref([])
const suppliers = ref([])
const assetNames = ref([])
const dictFields = ref([])
const dictValues = reactive({})

async function loadAssetNames() {
  try {
    const res = await api.get('/assets/names')
    assetNames.value = res.data || []
  } catch(e) { /* ignore */ }
}

function querySearch(queryString, cb) {
  const results = queryString
    ? assetNames.value.filter(name => name.toLowerCase().includes(queryString.toLowerCase()))
    : assetNames.value
  cb(results.map(name => ({ value: name })))
}

function parseOptions(opts) {
  if (!opts) return []
  try { return JSON.parse(opts) } catch { return [] }
}

onMounted(async () => {
  const [c, d, w, s] = await Promise.all([
    api.get('/categories', { params: { tree: true } }),
    api.get('/departments'), api.get('/warehouses'), api.get('/suppliers')
  ])
  categoryTree.value = c.data; depts.value = d.data; warehouses.value = w.data; suppliers.value = s.data
  loadAssetNames()
  // 加载资产模块的数据字典字段
  try {
    const df = await api.get('/dict/fields', { params: { module: 'assets' } })
    dictFields.value = df.data || []
    // 初始化 dictValues
    dictFields.value.forEach(f => { if (!(f.field_key in dictValues)) dictValues[f.field_key] = '' })
  } catch (e) { /* ignore */ }
  if (isEdit) {
    const res = await api.get(`/assets/${route.params.id}`)
    Object.assign(form, res.data)
    // 加载已有字典值
    try {
      const dv = await api.get('/dict/values', { params: { module: 'assets', record_id: route.params.id } })
      if (dv.data) {
        Object.keys(dv.data).forEach(key => { dictValues[key] = dv.data[key].value || '' })
      }
    } catch (e) { /* ignore */ }
  }
})

async function submit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    let assetId = route.params.id ? parseInt(route.params.id) : null
    if (isEdit) {
      await api.put(`/assets/${assetId}`, form)
    } else {
      const res = await api.post('/assets', form)
      assetId = res.data?.id || res.data?.asset_no  // 新创建的资产ID
      // 如果返回的是 asset 对象但没有 id，用 asset_no 回查
      if (!assetId) {
        const list = await api.get('/assets', { params: { keyword: form.name, page_size: 1 } })
        if (list.data?.items?.length) assetId = list.data.items[0].id
      }
    }
    // 保存数据字典值
    if (assetId && dictFields.value.length > 0) {
      const values = {}
      dictFields.value.forEach(f => { if (dictValues[f.field_key] !== '' && dictValues[f.field_key] != null) values[f.field_key] = dictValues[f.field_key] })
      if (Object.keys(values).length > 0) {
        await api.post('/dict/values', { record_id: assetId, module: 'assets', values }).catch(() => {})
      }
    }
    router.push('/assets/list')
  } finally { saving.value = false }
}
</script>
