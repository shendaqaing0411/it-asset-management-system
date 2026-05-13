<template>
  <!-- 根组件：提供 CSS 变量、全局样式、路由过渡动画 -->
  <router-view v-slot="{ Component, route }">
    <transition name="fade" mode="out-in">
      <component :is="Component" :key="route.path" />
    </transition>
  </router-view>
</template>

<style>
:root {
  --sidebar-bg: #1d1e2c;
  --sidebar-hover: #262738;
  --sidebar-active: #2d2e3f;
  --sidebar-text: #a6a7b7;
  --sidebar-active-text: #fff;
  --header-bg: #fff;
  --main-bg: #f5f6f8;
  --card-shadow: 0 1px 3px rgba(0,0,0,.06);
  --card-radius: 8px;
  --primary: #5b7cfa;
  --primary-light: #eef1fe;
  --success: #34c88d;
  --warning: #f5a623;
  --danger: #f55858;
}

* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif; font-size: 14px; color: #333; background: var(--main-bg); }

.fade-enter-active, .fade-leave-active { transition: opacity .2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* override element-plus */
.el-card { border-radius: var(--card-radius) !important; box-shadow: var(--card-shadow) !important; border: none !important; }
.el-button--primary { background-color: var(--primary) !important; border-color: var(--primary) !important; }
.el-menu { border-right: none !important; }
.el-pagination { justify-content: center; }
</style>
