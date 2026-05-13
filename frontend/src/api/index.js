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
    // 401 未登录：清除 token 并跳转登录页
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    ElMessage.error(err.response?.data?.detail || '网络错误')
    return Promise.reject(err)
  }
)

export default api
