<template>
  <div class="login-page">
    <div class="login-bg-shapes">
      <div class="shape shape-1"></div>
      <div class="shape shape-2"></div>
      <div class="shape shape-3"></div>
    </div>
    <div class="login-container">
      <div class="login-left">
        <div class="welcome-text">
          <div class="welcome-badge">◆ IT ASSET MANAGEMENT</div>
          <h1>IT 资产<br/>管理系统</h1>
          <p>轻量化、安全可控的本地资产解决方案<br/>资产管理 · 库存追踪 · 维修记录 · 数据报表</p>
        </div>
        <div class="feature-list">
          <div class="feature-item"><span class="dot"></span> 单文件数据库，即装即用</div>
          <div class="feature-item"><span class="dot"></span> 本地运行，数据安全可控</div>
          <div class="feature-item"><span class="dot"></span> 二维码标签，扫码即查</div>
        </div>
      </div>
      <div class="login-right">
        <div class="login-card">
          <h3>欢迎登录</h3>
          <p class="subtitle">请输入您的账号信息</p>
          <el-form :model="form" :rules="rules" ref="formRef" size="large" @submit.prevent="handleLogin">
            <el-form-item prop="username">
              <el-input v-model="form.username" placeholder="用户名" :prefix-icon="User" />
            </el-form-item>
            <el-form-item prop="password">
              <el-input v-model="form.password" type="password" placeholder="密码" :prefix-icon="Lock" show-password @keyup.enter="handleLogin" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" native-type="submit" :loading="loading" style="width:100%;height:44px;font-size:15px;border-radius:8px;">登 录</el-button>
            </el-form-item>
          </el-form>
          <p class="hint">默认账号 admin / admin123</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock } from '@element-plus/icons-vue'
import api from '../api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    const res = await api.post('/auth/login', form)
    localStorage.setItem('token', res.data.token)
    localStorage.setItem('user', JSON.stringify(res.data.user))
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } finally { loading.value = false }
}
</script>

<style scoped>
.login-page { display: flex; align-items: center; justify-content: center; height: 100vh; background: linear-gradient(135deg, #f0f2fe 0%, #e8ecff 40%, #f5f0ff 100%); position: relative; overflow: hidden; }
.login-bg-shapes { position: absolute; inset: 0; pointer-events: none; }
.shape { position: absolute; border-radius: 50%; opacity: .06; }
.shape-1 { width: 600px; height: 600px; background: var(--primary); top: -200px; right: -100px; }
.shape-2 { width: 400px; height: 400px; background: #7c5cfc; bottom: -150px; left: -80px; }
.shape-3 { width: 250px; height: 250px; background: var(--primary); top: 50%; left: 40%; }
.login-container { display: flex; max-width: 960px; width: 100%; background: #fff; border-radius: 16px; box-shadow: 0 20px 60px rgba(0,0,0,.08), 0 0 1px rgba(0,0,0,.04); overflow: hidden; z-index: 1; margin: 20px; }
.login-left { flex: 1; background: linear-gradient(135deg, #1d1e2c 0%, #2a2d45 100%); padding: 60px 48px; display: flex; flex-direction: column; justify-content: space-between; }
.welcome-badge { display: inline-block; padding: 4px 12px; border-radius: 4px; background: rgba(91,124,250,.15); color: var(--primary); font-size: 11px; letter-spacing: 1px; font-weight: 600; margin-bottom: 24px; }
.welcome-text h1 { color: #fff; font-size: 34px; font-weight: 700; line-height: 1.2; margin-bottom: 16px; }
.welcome-text p { color: rgba(255,255,255,.55); font-size: 14px; line-height: 1.8; }
.feature-list { display: flex; flex-direction: column; gap: 12px; }
.feature-item { color: rgba(255,255,255,.45); font-size: 13px; display: flex; align-items: center; gap: 10px; }
.feature-item .dot { width: 6px; height: 6px; border-radius: 50%; background: var(--primary); flex-shrink: 0; }
.login-right { width: 420px; padding: 60px 48px; display: flex; align-items: center; }
.login-card { width: 100%; }
.login-card h3 { font-size: 22px; font-weight: 600; margin-bottom: 6px; color: #1a1a2e; }
.login-card .subtitle { color: #999; font-size: 13px; margin-bottom: 32px; }
.hint { text-align: center; color: #bbb; font-size: 12px; margin-top: 24px; }

@media (max-width: 768px) { .login-left { display: none; } .login-right { width: 100%; padding: 40px 24px; } }
</style>
