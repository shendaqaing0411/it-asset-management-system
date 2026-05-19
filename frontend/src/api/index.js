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
    // 403 权限不足：明确提示
    if (err.response?.status === 403) {
      ElMessage.error('权限不足，无法执行该操作')
      return Promise.reject(err)
    }
    // 网络错误或服务器错误：弹窗提示
    ElMessage.error(err.response?.data?.detail || err.message || '网络错误')
    return Promise.reject(err)
  }
)

// 认证 CSV 下载：用 axios 发起请求（自动携带 token），触发浏览器下载
export function downloadCsv(url, filename) {
  api.get(url, { responseType: 'blob' }).then(res => {
    const blob = res instanceof Blob ? res : new Blob([res], { type: 'text/csv;charset=utf-8' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    // 从 Content-Disposition 头提取文件名，或使用传入的 filename
    const disposition = res.headers?.['content-disposition'] || (res.headers?.get?.('content-disposition') || '')
    const match = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
    link.download = match ? match[1].replace(/['"]/g, '') : (filename || 'export.csv')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(link.href)
  }).catch(() => {
    // 错误由拦截器统一处理
  })
}

export default api
