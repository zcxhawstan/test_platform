import { defineStore } from 'pinia'
import { login as loginApi, logout as logoutApi, getProfile } from '@/api/auth'

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
      this.token = res.data.token
      this.user = res.data.user
      localStorage.setItem('token', this.token)
      localStorage.setItem('user', JSON.stringify(this.user))
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
      const res = await getProfile()
      this.user = res.data
      localStorage.setItem('user', JSON.stringify(this.user))
      return res
    }
  }
})
