// 路由配置：Hash 模式、嵌套路由、登录鉴权守卫、权限码检查

import { createRouter, createWebHashHistory } from 'vue-router'
import { ElMessage } from 'element-plus'

// 所有非登录页面均通过 Layout 组件渲染，作为其子路由
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/',
    component: () => import('../components/Layout.vue'),
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('../views/Dashboard.vue'), meta: { title: '仪表盘', permission: 'dashboard:view' } },
      { path: 'assets/list', name: 'AssetList', component: () => import('../views/assets/AssetList.vue'), meta: { title: '资产列表', permission: 'asset:read' } },
      { path: 'assets/form/:id?', name: 'AssetForm', component: () => import('../views/assets/AssetForm.vue'), meta: { title: '资产登记', permission: 'asset:create' } },
      { path: 'assets/check', name: 'CheckPlan', component: () => import('../views/assets/CheckPlan.vue'), meta: { title: '资产盘点', permission: 'stock:check' } },
      { path: 'assets/:id/timeline', name: 'AssetTimeline', component: () => import('../views/assets/AssetTimeline.vue'), meta: { title: '资产时间线', permission: 'asset:read' } },
      { path: 'stock/query', name: 'StockQuery', component: () => import('../views/stock/StockQuery.vue'), meta: { title: '库存查询', permission: 'stock:query' } },
      { path: 'stock/in', name: 'StockIn', component: () => import('../views/stock/StockIn.vue'), meta: { title: '入库管理', permission: 'stock:in' } },
      { path: 'stock/out', name: 'StockOut', component: () => import('../views/stock/StockOut.vue'), meta: { title: '出库管理', permission: 'stock:out' } },
      { path: 'stock/approvals', name: 'ApprovalList', component: () => import('../views/stock/ApprovalList.vue'), meta: { title: '领用审批', permission: 'approval:submit' } },
      { path: 'repairs/list', name: 'RepairList', component: () => import('../views/repairs/RepairList.vue'), meta: { title: '维修记录', permission: 'repair:read' } },
      { path: 'repairs/scraps', name: 'ScrapList', component: () => import('../views/repairs/ScrapList.vue'), meta: { title: '报废管理', permission: 'scrap:read' } },
      { path: 'reports/stock', name: 'StockReport', component: () => import('../views/reports/StockReport.vue'), meta: { title: '库存统计', permission: 'report:stock' } },
      { path: 'reports/inout', name: 'InoutReport', component: () => import('../views/reports/InoutReport.vue'), meta: { title: '出入库报表', permission: 'report:inout' } },
      { path: 'reports/summary', name: 'SummaryReport', component: () => import('../views/reports/SummaryReport.vue'), meta: { title: '资产汇总', permission: 'report:summary' } },
      { path: 'reports/depreciation', name: 'Depreciation', component: () => import('../views/reports/Depreciation.vue'), meta: { title: '折旧报表', permission: 'report:depreciation' } },
      { path: 'system/departments', name: 'Departments', component: () => import('../views/system/Departments.vue'), meta: { title: '部门管理', permission: 'system:dept' } },
      { path: 'system/categories', name: 'Categories', component: () => import('../views/system/Categories.vue'), meta: { title: '分类管理', permission: 'system:category' } },
      { path: 'system/suppliers', name: 'Suppliers', component: () => import('../views/system/Suppliers.vue'), meta: { title: '供应商管理', permission: 'system:supplier' } },
      { path: 'system/warehouses', name: 'Warehouses', component: () => import('../views/system/Warehouses.vue'), meta: { title: '仓库管理', permission: 'system:warehouse' } },
      { path: 'system/warnings', name: 'Warnings', component: () => import('../views/system/Warnings.vue'), meta: { title: '库存预警', permission: 'system:warehouse' } },
      { path: 'system/logs', name: 'Logs', component: () => import('../views/system/Logs.vue'), meta: { title: '操作日志', permission: 'system:log' } },
      { path: 'system/users', name: 'Users', component: () => import('../views/system/Users.vue'), meta: { title: '用户管理', permission: 'system:user' } },
      { path: 'system/roles', name: 'Roles', component: () => import('../views/system/Roles.vue'), meta: { title: '角色管理', permission: 'system:role' } },
      { path: 'system/dict', name: 'Dict', component: () => import('../views/system/Dict.vue'), meta: { title: '数据字典', permission: 'system:dict' } },
      { path: 'system/depreciation-config', name: 'DepreciationConfig', component: () => import('../views/system/DepreciationConfig.vue'), meta: { title: '折旧配置', permission: 'depreciation:config' } }
    ]
  }
]

const router = createRouter({ history: createWebHashHistory(), routes })

function getUserPermissions() {
  try {
    const user = JSON.parse(localStorage.getItem('user') || 'null')
    return user?.permissions || []
  } catch { return [] }
}

// 路由守卫：页面标题、登录校验、权限码检查
router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - IT资产管理系统` : 'IT资产管理系统'
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) {
    next('/login')
    return
  }
  const perm = to.meta.permission
  if (perm) {
    const perms = getUserPermissions()
    if (!perms.includes(perm)) {
      ElMessage.error('权限不足，无法访问该页面')
      next(from.path || '/dashboard')
      return
    }
  }
  next()
})

export default router
