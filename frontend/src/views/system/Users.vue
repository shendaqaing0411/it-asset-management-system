<template>
  <el-card>
    <el-button type="primary" @click="add" style="margin-bottom:16px">新增用户</el-button>
    <el-table :data="items" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="用户名" width="120" />
      <el-table-column prop="real_name" label="姓名" width="100" />
      <el-table-column prop="role_name" label="角色" width="110">
        <template #default="{row}">{{ row.role_name || roleLabel(row.role) }}</template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="80">
        <template #default="{row}"><el-tag :type="row.status==='active'?'success':'info'" size="small">{{ row.status === 'active' ? '启用' : '禁用' }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="create_time" label="创建时间" width="160" />
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{row}">
          <el-button link type="primary" @click="edit(row)">编辑</el-button>
          <el-button link type="warning" @click="resetPwd(row)">重置密码</el-button>
          <el-popconfirm title="确认删除？" @confirm="handleDelete(row.id)">
            <template #reference><el-button link type="danger" :disabled="row.role_name === '超级管理员' || row.role === 'super_admin'">删除</el-button></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新增/编辑 -->
    <el-dialog v-model="visible" :title="editing ? '编辑用户' : '新增用户'" width="450px" @closed="resetForm">
      <el-form :model="form" ref="formRef" :rules="rules" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="!!editing" placeholder="登录用户名" />
        </el-form-item>
        <el-form-item :label="editing ? '新密码' : '密码'" prop="password" v-if="!editing">
          <el-input v-model="form.password" type="password" show-password placeholder="至少6位" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.real_name" placeholder="显示名称" />
        </el-form-item>
        <el-form-item label="角色" prop="role_id">
          <el-select v-model="form.role_id" style="width:100%" placeholder="选择角色">
            <el-option v-for="r in roleList" :key="r.id" :label="r.name" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属部门">
          <el-select v-model="form.dept_id" style="width:100%" clearable placeholder="选择部门">
            <el-option v-for="d in depts" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" v-if="editing">
          <el-select v-model="form.status" style="width:100%">
            <el-option label="启用" value="active" />
            <el-option label="禁用" value="disabled" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" @click="submit" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码 -->
    <el-dialog v-model="pwdVisible" title="重置密码" width="400px">
      <el-form :model="pwdForm" ref="pwdFormRef" :rules="pwdRules" label-width="80px">
        <el-form-item label="用户">{{ pwdTarget?.real_name || pwdTarget?.username }}</el-form-item>
        <el-form-item label="新密码" prop="password">
          <el-input v-model="pwdForm.password" type="password" show-password placeholder="至少6位" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdVisible = false">取消</el-button>
        <el-button type="primary" @click="doResetPwd" :loading="saving">确认重置</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
// 用户管理：角色从 API 动态加载，使用 role_id 关联
import { ref, reactive, onMounted } from 'vue'
import api from '../../api'
import { ElMessage } from 'element-plus'

function roleLabel(role) {
  const map = { super_admin: '超级管理员', asset_admin: '资产管理员', dept_manager: '部门主管', user: '普通用户', auditor: '审计员' }
  return map[role] || role || ''
}

const loading = ref(false)
const saving = ref(false)
const items = ref([])
const roleList = ref([])
const visible = ref(false)
const editing = ref(false)
const pwdVisible = ref(false)
const pwdTarget = ref(null)
const formRef = ref(null)
const pwdFormRef = ref(null)
const depts = ref([])
const form = reactive({ username: '', password: '', real_name: '', role_id: null, status: 'active', dept_id: null })
const pwdForm = reactive({ password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }, { min: 6, message: '至少6位', trigger: 'blur' }]
}
const pwdRules = {
  password: [{ required: true, message: '请输入新密码', trigger: 'blur' }, { min: 6, message: '至少6位', trigger: 'blur' }]
}

async function fetch() {
  loading.value = true
  try { const r = await api.get('/users'); items.value = r.data }
  finally { loading.value = false }
}

async function fetchDepts() {
  try { const r = await api.get('/departments'); depts.value = r.data }
  catch { /* ignore */ }
}

async function fetchRoles() {
  try { const r = await api.get('/roles'); roleList.value = r.data }
  catch { /* ignore */ }
}

function add() {
  editing.value = false
  form.username = ''; form.password = ''; form.real_name = ''; form.role_id = null; form.status = 'active'; form.dept_id = null
  visible.value = true
}

function edit(row) {
  editing.value = row
  form.username = row.username; form.password = ''; form.real_name = row.real_name
  form.role_id = row.role_id || null; form.status = row.status; form.dept_id = row.dept_id || null
  visible.value = true
}

function resetForm() { editing.value = false }

async function submit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const payload = { real_name: form.real_name, role_id: form.role_id, status: form.status, dept_id: form.dept_id }
    if (editing.value) {
      await api.put(`/users/${editing.value.id}`, payload)
    } else {
      await api.post('/users', { ...payload, username: form.username, password: form.password })
    }
    ElMessage.success('保存成功'); visible.value = false; fetch()
  } finally { saving.value = false }
}

function resetPwd(row) {
  pwdTarget.value = row
  pwdForm.password = ''
  pwdVisible.value = true
}

async function doResetPwd() {
  const valid = await pwdFormRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    await api.put(`/users/${pwdTarget.value.id}/password`, { password: pwdForm.password })
    ElMessage.success('密码已重置'); pwdVisible.value = false
  } finally { saving.value = false }
}

async function handleDelete(id) {
  await api.delete(`/users/${id}`)
  ElMessage.success('已删除'); fetch()
}

onMounted(() => { fetch(); fetchDepts(); fetchRoles() })
</script>
