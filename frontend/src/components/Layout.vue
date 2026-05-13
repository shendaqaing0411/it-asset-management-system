<template>
  <div class="app-layout">
    <aside :class="['sidebar', { collapsed }]">
      <div class="sidebar-logo" @click="$router.push('/dashboard')">
        <span class="logo-icon">◆</span>
        <transition name="fade"><span v-show="!collapsed" class="logo-text">IT资产管理系统</span></transition>
      </div>
      <el-menu :default-active="activeMenu" router :collapse="collapsed" :default-openeds="openeds" background-color="transparent" text-color="var(--sidebar-text)" active-text-color="var(--sidebar-active-text)" class="sidebar-menu">
        <el-menu-item index="/dashboard"><el-icon><DataBoard /></el-icon><template #title>仪表盘</template></el-menu-item>
        <el-sub-menu index="assets">
          <template #title><el-icon><Monitor /></el-icon><span>资产管理</span></template>
          <el-menu-item index="/assets/list">资产列表</el-menu-item>
          <el-menu-item index="/assets/form">资产登记</el-menu-item>
          <el-menu-item index="/assets/check">资产盘点</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="stock">
          <template #title><el-icon><Box /></el-icon><span>库存管理</span></template>
          <el-menu-item index="/stock/query">库存查询</el-menu-item>
          <el-menu-item index="/stock/in">入库管理</el-menu-item>
          <el-menu-item index="/stock/out">出库管理</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="repairs">
          <template #title><el-icon><Tools /></el-icon><span>维保管理</span></template>
          <el-menu-item index="/repairs/list">维修记录</el-menu-item>
          <el-menu-item index="/repairs/scraps">报废管理</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="reports">
          <template #title><el-icon><PieChart /></el-icon><span>报表统计</span></template>
          <el-menu-item index="/reports/stock">库存统计</el-menu-item>
          <el-menu-item index="/reports/inout">出入库报表</el-menu-item>
          <el-menu-item index="/reports/summary">资产汇总</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="system">
          <template #title><el-icon><Setting /></el-icon><span>系统管理</span></template>
          <el-menu-item index="/system/departments">部门管理</el-menu-item>
          <el-menu-item index="/system/categories">分类管理</el-menu-item>
          <el-menu-item index="/system/suppliers">供应商管理</el-menu-item>
          <el-menu-item index="/system/warehouses">仓库管理</el-menu-item>
          <el-menu-item index="/system/warnings">库存预警</el-menu-item>
          <el-menu-item index="/system/logs">操作日志</el-menu-item>
          <el-menu-item index="/system/users">用户管理</el-menu-item>
        </el-sub-menu>
      </el-menu>
      <div class="sidebar-collapse" @click="collapsed = !collapsed">
        <el-icon :size="18"><Fold v-if="!collapsed" /><Expand v-else /></el-icon>
      </div>
    </aside>
    <div class="main-area">
      <header class="topbar">
        <div class="topbar-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="parentTitle">{{ parentTitle }}</el-breadcrumb-item>
            <el-breadcrumb-item>{{ pageTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="topbar-right">
          <el-tooltip content="全屏" placement="bottom"><el-icon class="topbar-icon" @click="toggleFullscreen"><FullScreen /></el-icon></el-tooltip>
          <el-dropdown trigger="click">
            <span class="user-badge">
              <el-avatar :size="32" icon="UserFilled" />
              <span class="user-name">{{ user?.real_name || '管理员' }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled><el-icon><User /></el-icon> {{ user?.username }} ({{ user?.role === 'admin' ? '管理员' : '普通用户' }})</el-dropdown-item>
                <el-dropdown-item divided @click="logout"><el-icon><SwitchButton /></el-icon> 退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>
      <main class="content"><router-view /></main>
    </div>
  </div>
</template>

<script setup>
// 主布局：可折叠侧边栏 + 面包屑导航 + 用户下拉菜单 + 全屏切换
// 根据路由 name 自动推断面包屑父子标题
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
const route = useRoute()
const router = useRouter()
const user = JSON.parse(localStorage.getItem('user') || 'null')
const collapsed = ref(false)
const activeMenu = computed(() => route.path)
const openeds = ['assets', 'stock', 'repairs', 'reports', 'system']
const pageTitle = computed(() => route.meta.title || '')
const parentMap = { AssetList: '资产管理', AssetForm: '资产管理', CheckPlan: '资产管理', StockQuery: '库存管理', StockIn: '库存管理', StockOut: '库存管理', RepairList: '维保管理', ScrapList: '维保管理', StockReport: '报表统计', InoutReport: '报表统计', SummaryReport: '报表统计', Departments: '系统管理', Categories: '系统管理', Suppliers: '系统管理', Warehouses: '系统管理', Warnings: '系统管理', Logs: '系统管理', Users: '系统管理' }
const parentTitle = computed(() => parentMap[route.name] || '')

function toggleFullscreen() { if (!document.fullscreenElement) document.documentElement.requestFullscreen(); else document.exitFullscreen() }

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  router.push('/login')
}
</script>

<style scoped>
.app-layout { display: flex; height: 100vh; overflow: hidden; }

/* sidebar */
.sidebar { width: 220px; min-width: 220px; background: var(--sidebar-bg); display: flex; flex-direction: column; transition: all .25s; position: relative; z-index: 10; }
.sidebar.collapsed { width: 64px; min-width: 64px; }
.sidebar-logo { height: 56px; display: flex; align-items: center; justify-content: center; gap: 8px; cursor: pointer; border-bottom: 1px solid rgba(255,255,255,.06); flex-shrink: 0; }
.logo-icon { color: var(--primary); font-size: 22px; }
.logo-text { color: #fff; font-size: 15px; font-weight: 600; white-space: nowrap; }
.sidebar-menu { flex: 1; overflow-y: auto; overflow-x: hidden; }
.sidebar-menu .el-sub-menu .el-sub-menu__title { padding-left: 20px !important; }
.sidebar-menu .el-menu-item { padding-left: 20px !important; min-width: 0; }
.sidebar-menu .el-menu-item:hover, .sidebar-menu .el-sub-menu__title:hover { background: var(--sidebar-hover) !important; }
.sidebar-menu .el-menu-item.is-active { background: var(--primary) !important; color: #fff !important; border-radius: 4px; margin: 0 8px; width: calc(100% - 16px); }
.sidebar.collapsed .sidebar-menu .el-menu-item.is-active { border-radius: 0; margin: 0; width: 100%; }
.sidebar-collapse { height: 40px; display: flex; align-items: center; justify-content: center; cursor: pointer; color: var(--sidebar-text); border-top: 1px solid rgba(255,255,255,.06); flex-shrink: 0; transition: color .2s; }
.sidebar-collapse:hover { color: #fff; }

/* main */
.main-area { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.topbar { height: 56px; background: var(--header-bg); display: flex; align-items: center; justify-content: space-between; padding: 0 24px; box-shadow: 0 1px 4px rgba(0,0,0,.04); flex-shrink: 0; z-index: 9; }
.topbar-left { display: flex; align-items: center; }
.topbar-right { display: flex; align-items: center; gap: 16px; }
.topbar-icon { font-size: 18px; cursor: pointer; color: #666; padding: 6px; border-radius: 6px; transition: all .2s; }
.topbar-icon:hover { background: #f0f0f0; color: #333; }
.user-badge { display: flex; align-items: center; gap: 8px; cursor: pointer; padding: 4px 12px 4px 4px; border-radius: 20px; transition: all .2s; }
.user-badge:hover { background: #f5f5f5; }
.user-name { font-size: 13px; color: #333; }
.content { flex: 1; padding: 20px 24px; overflow-y: auto; }
</style>
