import { createRouter, createWebHashHistory } from 'vue-router'

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
      { path: 'dashboard', name: 'Dashboard', component: () => import('../views/Dashboard.vue'), meta: { title: '仪表盘' } },
      { path: 'assets/list', name: 'AssetList', component: () => import('../views/assets/AssetList.vue'), meta: { title: '资产列表' } },
      { path: 'assets/form/:id?', name: 'AssetForm', component: () => import('../views/assets/AssetForm.vue'), meta: { title: '资产登记' } },
      { path: 'assets/check', name: 'CheckPlan', component: () => import('../views/assets/CheckPlan.vue'), meta: { title: '资产盘点' } },
      { path: 'stock/query', name: 'StockQuery', component: () => import('../views/stock/StockQuery.vue'), meta: { title: '库存查询' } },
      { path: 'stock/in', name: 'StockIn', component: () => import('../views/stock/StockIn.vue'), meta: { title: '入库管理' } },
      { path: 'stock/out', name: 'StockOut', component: () => import('../views/stock/StockOut.vue'), meta: { title: '出库管理' } },
      { path: 'repairs/list', name: 'RepairList', component: () => import('../views/repairs/RepairList.vue'), meta: { title: '维修记录' } },
      { path: 'repairs/scraps', name: 'ScrapList', component: () => import('../views/repairs/ScrapList.vue'), meta: { title: '报废管理' } },
      { path: 'reports/stock', name: 'StockReport', component: () => import('../views/reports/StockReport.vue'), meta: { title: '库存统计' } },
      { path: 'reports/inout', name: 'InoutReport', component: () => import('../views/reports/InoutReport.vue'), meta: { title: '出入库报表' } },
      { path: 'reports/summary', name: 'SummaryReport', component: () => import('../views/reports/SummaryReport.vue'), meta: { title: '资产汇总' } },
      { path: 'system/departments', name: 'Departments', component: () => import('../views/system/Departments.vue'), meta: { title: '部门管理' } },
      { path: 'system/categories', name: 'Categories', component: () => import('../views/system/Categories.vue'), meta: { title: '分类管理' } },
      { path: 'system/suppliers', name: 'Suppliers', component: () => import('../views/system/Suppliers.vue'), meta: { title: '供应商管理' } },
      { path: 'system/warehouses', name: 'Warehouses', component: () => import('../views/system/Warehouses.vue'), meta: { title: '仓库管理' } },
      { path: 'system/warnings', name: 'Warnings', component: () => import('../views/system/Warnings.vue'), meta: { title: '库存预警' } },
      { path: 'system/logs', name: 'Logs', component: () => import('../views/system/Logs.vue'), meta: { title: '操作日志' } },
      { path: 'system/users', name: 'Users', component: () => import('../views/system/Users.vue'), meta: { title: '用户管理' } }
    ]
  }
]

const router = createRouter({ history: createWebHashHistory(), routes })

router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - IT资产管理系统` : 'IT资产管理系统'
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
