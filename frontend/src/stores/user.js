import { defineStore } from 'pinia'
import { login as loginApi, logout as logoutApi, getProfile } from '@/api/auth'
import router from '@/router'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: JSON.parse(localStorage.getItem('user') || '{}')
  }),
  
  getters: {
    isLoggedIn: (state) => !!state.token,
    username: (state) => state.user.username || '',
    role: (state) => state.user.role || ''
  },
  
  actions: {
    async login(credentials) {
      const res = await loginApi(credentials)
      console.log('登录响应:', res)
      console.log('用户信息:', res.data.user)
      this.token = res.data.token
      this.user = res.data.user
      localStorage.setItem('token', this.token)
      localStorage.setItem('user', JSON.stringify(this.user))
      console.log('存储的用户信息:', JSON.parse(localStorage.getItem('user')))
      return res
    },
    
    async logout() {
      try {
        await logoutApi()
      } finally {
        this.token = ''
        this.user = {}
        localStorage.removeItem('token')
        localStorage.removeItem('user')
      }
    },
    
    async fetchProfile() {
      try {
        const res = await getProfile()
        this.user = res.data
        localStorage.setItem('user', JSON.stringify(this.user))
        return res
      } catch (error) {
        // 如果获取个人信息失败，说明token无效，清除登录状态
        this.logout()
        router.push('/login')
        throw error
      }
    },
    
    async validateToken() {
      if (!this.token) {
        return false
      }
      
      try {
        await this.fetchProfile()
        return true
      } catch (error) {
        return false
      }
    }
  }
})
