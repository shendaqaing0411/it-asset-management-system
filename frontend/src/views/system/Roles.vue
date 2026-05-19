<template>
  <div class="roles-page">
    <div class="roles-left">
      <el-card>
        <template #header><span>角色列表</span></template>
        <el-button type="primary" @click="add" style="margin-bottom:12px">新增角色</el-button>
        <el-table :data="roles" stripe highlight-current-row @row-click="selectRole" :row-class-name="rowClass">
          <el-table-column prop="name" label="角色名称" width="120" />
          <el-table-column prop="user_count" label="用户数" width="70" align="center" />
          <el-table-column prop="scope" label="范围" width="70" align="center">
            <template #default="{row}">
              <el-tag size="small" :type="scopeTag(row.scope)">{{ scopeLabel(row.scope) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="{row}">
              <el-popconfirm title="确认删除？" @confirm="handleDelete(row.id)">
                <template #reference>
                  <el-button link type="danger" size="small" :disabled="row.is_system === 1">删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <div class="roles-right" v-if="selected">
      <el-card>
        <template #header>
          <span>{{ editing ? '编辑角色' : '角色权限配置' }} — {{ form.name }}</span>
          <el-tag v-if="selected.is_system === 1" type="warning" size="small" style="margin-left:8px">内置</el-tag>
        </template>
        <el-form :model="form" label-width="80px" style="margin-bottom:16px">
          <el-form-item label="角色名称">
            <el-input v-model="form.name" placeholder="角色名称" :disabled="selected.is_system === 1" />
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="form.description" placeholder="角色描述" />
          </el-form-item>
          <el-form-item label="数据范围">
            <el-select v-model="form.scope" style="width:200px">
              <el-option label="全部数据" value="all" />
              <el-option label="本部门" value="dept" />
              <el-option label="仅本人" value="self" />
            </el-select>
          </el-form-item>
        </el-form>

        <div class="perm-header">
          <span class="perm-title">权限配置</span>
          <el-button link type="primary" @click="toggleAll">{{ allChecked ? '全部取消' : '全部勾选' }}</el-button>
        </div>

        <div v-for="group in permGroups" :key="group.module" class="perm-group">
          <div class="perm-group-header">
            <el-checkbox v-model="group._checked" :indeterminate="group._indeterminate" @change="(v) => toggleGroup(group, v)">
              <strong>{{ group.module }}</strong>
            </el-checkbox>
          </div>
          <div class="perm-items">
            <el-checkbox v-for="item in group.items" :key="item.code" v-model="item._checked" @change="onPermChange" style="margin-right:8px;width:160px">
              {{ item.label }}
            </el-checkbox>
          </div>
        </div>

        <div style="margin-top:16px">
          <el-button type="primary" @click="submit" :loading="saving">保存</el-button>
          <el-button @click="selected = null">取消</el-button>
        </div>
      </el-card>
    </div>

    <div class="roles-right" v-else>
      <el-empty description="选择左侧角色以编辑权限" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import api from '../../api'
import { ElMessage } from 'element-plus'

const roles = ref([])
const selected = ref(null)
const editing = ref(false)
const saving = ref(false)
const permGroups = ref([])

const form = reactive({ name: '', description: '', scope: 'all' })

const allChecked = computed(() => {
  if (!permGroups.value.length) return false
  return permGroups.value.every(g => g.items.every(i => i._checked))
})

function scopeLabel(s) { return { all: '全部', dept: '部门', self: '本人' }[s] || s }
function scopeTag(s) { return { all: '', dept: 'warning', self: 'info' }[s] || '' }

function rowClass({ row }) {
  if (selected.value && row.id === selected.value.id) return 'current-row'
  return ''
}

async function fetchRoles() {
  const r = await api.get('/roles')
  roles.value = r.data
}

async function fetchPerms() {
  const r = await api.get('/permissions')
  permGroups.value = (r.data || []).map(g => ({
    module: g.module,
    items: (g.items || []).map(i => ({ ...i, _checked: false }))
  }))
}

function applyPerms(codes) {
  for (const g of permGroups.value) {
    for (const item of g.items) {
      item._checked = codes.includes(item.code)
    }
    updateGroupState(g)
  }
}

function getPermCodes() {
  const codes = []
  for (const g of permGroups.value) {
    for (const item of g.items) {
      if (item._checked) codes.push(item.code)
    }
  }
  return codes
}

function updateGroupState(group) {
  const total = group.items.length
  const checked = group.items.filter(i => i._checked).length
  group._checked = checked === total
  group._indeterminate = checked > 0 && checked < total
}

function onPermChange() {
  for (const g of permGroups.value) updateGroupState(g)
}

function toggleGroup(group, val) {
  for (const item of group.items) item._checked = val
  group._checked = val
  group._indeterminate = false
}

function toggleAll() {
  const newVal = !allChecked.value
  for (const g of permGroups.value) {
    for (const item of g.items) item._checked = newVal
    g._checked = newVal
    g._indeterminate = false
  }
}

async function selectRole(row) {
  if (selected.value && selected.value.id === row.id) return
  selected.value = row
  editing.value = true
  await fetchPerms()
  const r = await api.get(`/roles/${row.id}`)
  const role = r.data
  form.name = role.name
  form.description = role.description || ''
  form.scope = role.scope || 'all'
  applyPerms(role.permissions || [])
}

function add() {
  selected.value = { id: null, is_system: 0 }
  editing.value = false
  form.name = ''
  form.description = ''
  form.scope = 'all'
  fetchPerms().then(() => applyPerms([]))
}

async function submit() {
  if (!form.name.trim()) { ElMessage.warning('请输入角色名称'); return }
  saving.value = true
  try {
    const payload = {
      name: form.name,
      description: form.description,
      scope: form.scope,
      permissions: getPermCodes()
    }
    if (editing.value) {
      await api.put(`/roles/${selected.value.id}`, payload)
      ElMessage.success('角色已更新')
    } else {
      await api.post('/roles', payload)
      ElMessage.success('角色创建成功')
    }
    selected.value = null
    fetchRoles()
  } finally { saving.value = false }
}

async function handleDelete(id) {
  await api.delete(`/roles/${id}`)
  ElMessage.success('已删除')
  if (selected.value && selected.value.id === id) selected.value = null
  fetchRoles()
}

onMounted(() => { fetchRoles() })
</script>

<style scoped>
.roles-page { display: flex; gap: 16px; height: calc(100vh - 140px); }
.roles-left { width: 400px; flex-shrink: 0; }
.roles-left .el-card { height: 100%; display: flex; flex-direction: column; }
.roles-left :deep(.el-card__body) { flex: 1; overflow: auto; }
.roles-right { flex: 1; overflow-y: auto; }
.roles-right .el-card { min-height: 100%; }
.perm-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.perm-title { font-size: 14px; font-weight: 600; }
.perm-group { margin-bottom: 12px; padding: 10px; background: #fafafa; border-radius: 6px; }
.perm-group-header { margin-bottom: 6px; }
.perm-items { display: flex; flex-wrap: wrap; gap: 4px 0; padding-left: 22px; }
</style>
