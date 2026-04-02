import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000
})

request.interceptors.request.use(
  config => {
    // 从localStorage直接获取token，避免pinia上下文问题
    const token = localStorage.getItem('token')
    // 只有当token存在且不为空时，才添加Authorization头
    if (token && token.trim()) {
      config.headers.Authorization = `Token ${token}`
    } else {
      // 如果token不存在，删除Authorization头
      delete config.headers.Authorization
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

request.interceptors.response.use(
  response => {
    const res = response.data
    if (res.code !== 200 && res.code !== 201) {
      console.error('API响应错误:', res)
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res
  },
  error => {
    console.error('请求错误:', error)
    if (error.response) {
      const { status, data } = error.response
      console.error('响应状态码:', status)
      console.error('响应数据:', data)
      if (status === 401) {
        // 直接清除本地存储，避免循环调用logout接口
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        // 重置用户状态
        const userStore = useUserStore()
        userStore.token = ''
        userStore.user = {}
        window.location.href = '/login'
      } else {
        ElMessage.error(data.message || '请求失败')
      }
    } else if (error.request) {
      console.error('请求已发送但无响应:', error.request)
      ElMessage.error('请求超时或网络错误')
    } else {
      console.error('请求配置错误:', error.message)
      ElMessage.error('网络错误')
    }
    return Promise.reject(error)
  }
)

export default request
