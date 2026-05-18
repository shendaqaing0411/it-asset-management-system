// Axios 实例：统一 baseURL、token 注入、错误处理、登录过期跳转

import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({ baseURL: '/api' })

// 请求拦截器：自动注入 JWT token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  res => {
    // 业务层错误（code !== 0）：弹窗提示并拒绝 Promise
    if (res.data.code && res.data.code !== 0) {
      ElMessage.error(res.data.message || '请求失败')
      return Promise.reject(res.data)
    }
    return res.data
  },
  err => {
    // 组件卸载时主动取消的请求，静默忽略不弹窗
    if (axios.isCancel(err)) {
      return Promise.reject(err)
    }
    // 401 未登录：清除 token 并跳转登录页
    // 注意：项目使用 Hash 模式路由，登录页路径为 /#/login
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      // 使用动态 import 避免循环依赖，通过 Vue Router 跳转而非硬刷新
      import('../router/index.js').then(({ default: router }) => {
        router.push('/login')
      }).catch(() => {
        // 兜底：router 加载失败时使用 location.href（Hash 模式正确路径）
        window.location.href = '/#/login'
      })
      return Promise.reject(err)
    }
    // 网络错误或服务器错误：仅对非 401、非取消类错误弹窗提示
    ElMessage.error(err.response?.data?.detail || err.message || '网络错误')
    return Promise.reject(err)
  }
)

export default api
