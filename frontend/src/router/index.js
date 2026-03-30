import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/dashboard'
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '仪表盘' }
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/Users.vue'),
        meta: { title: '用户管理' }
      },
      {
        path: 'testcases',
        name: 'TestCases',
        component: () => import('@/views/TestCases.vue'),
        meta: { title: '测试用例' }
      },
      {
        path: 'testplans',
        name: 'TestPlans',
        component: () => import('@/views/TestPlans.vue'),
        meta: { title: '测试计划' }
      },
      {
        path: 'defects',
        name: 'Defects',
        component: () => import('@/views/Defects.vue'),
        meta: { title: '缺陷管理' }
      },
      {
        path: 'apitest',
        name: 'ApiTest',
        component: () => import('@/views/ApiTest.vue'),
        meta: { title: '接口测试' }
      },
      {
        path: 'environments',
        name: 'Environments',
        component: () => import('@/views/Environments.vue'),
        meta: { title: '环境管理' }
      },
      {
        path: 'logs',
        name: 'Logs',
        component: () => import('@/views/Logs.vue'),
        meta: { title: '日志管理' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  if (to.meta.requiresAuth && !userStore.token) {
    next('/login')
  } else if (to.path === '/login' && userStore.token) {
    next('/')
  } else {
    next()
  }
})

export default router
