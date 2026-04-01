import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000
})

request.interceptors.request.use(
  config => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Token ${userStore.token}`
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
    if (res.code !== 200) {
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
        const userStore = useUserStore()
        userStore.logout()
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
