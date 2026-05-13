<template>
  <el-card>
    <el-button type="primary" @click="add" style="margin-bottom:16px">新增用户</el-button>
    <el-table :data="items" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="用户名" width="120" />
      <el-table-column prop="real_name" label="姓名" width="100" />
      <el-table-column prop="role" label="角色" width="80">
        <template #default="{row}"><el-tag :type="row.role==='admin'?'danger':''" size="small">{{ row.role === 'admin' ? '管理员' : '普通用户' }}</el-tag></template>
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
            <template #reference><el-button link type="danger" :disabled="row.role === 'admin'">删除</el-button></template>
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
        <el-form-item label="角色">
          <el-select v-model="form.role" style="width:100%">
            <el-option label="普通用户" value="user" />
            <el-option label="管理员" value="admin" />
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
import { ref, reactive, onMounted } from 'vue'
import api from '../../api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const saving = ref(false)
const items = ref([])
const visible = ref(false)
const editing = ref(false)
const pwdVisible = ref(false)
const pwdTarget = ref(null)
const formRef = ref(null)
const pwdFormRef = ref(null)
const form = reactive({ username: '', password: '', real_name: '', role: 'user', status: 'active' })
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

function add() {
  editing.value = false
  form.username = ''; form.password = ''; form.real_name = ''; form.role = 'user'; form.status = 'active'
  visible.value = true
}

function edit(row) {
  editing.value = row
  form.username = row.username; form.password = ''; form.real_name = row.real_name; form.role = row.role; form.status = row.status
  visible.value = true
}

function resetForm() { editing.value = false }

async function submit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (editing.value) {
      await api.put(`/users/${editing.value.id}`, { real_name: form.real_name, role: form.role, status: form.status })
    } else {
      await api.post('/users', { username: form.username, password: form.password, real_name: form.real_name, role: form.role })
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

onMounted(() => fetch())
</script>
