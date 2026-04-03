import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

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
        path: 'logs',
        name: 'Logs',
        component: () => import('@/views/Logs.vue'),
        meta: { title: '日志管理' }
      },
      {
        path: 'automation/tasks',
        name: 'AutomationTasks',
        component: () => import('@/views/AutomationTasks.vue'),
        meta: { title: '自动化任务' }
      },
      {
        path: 'automation/environments',
        name: 'AutomationEnvironments',
        component: () => import('@/views/AutomationEnvironments.vue'),
        meta: { title: '环境配置' }
      },
      {
        path: 'automation/executions',
        name: 'AutomationExecutions',
        component: () => import('@/views/AutomationExecutions.vue'),
        meta: { title: '执行历史' }
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
  
  console.log('路由守卫检查:', {
    to: to.path,
    token: userStore.token,
    user: userStore.user,
    role: userStore.role
  })
  
  if (to.meta.requiresAuth && !userStore.token) {
    console.log('未登录，跳转到登录页')
    next('/login')
  } else if (to.path === '/login' && userStore.token) {
    console.log('已登录，跳转到首页')
    next('/')
  } else if (to.path === '/users') {
    // 检查用户是否为管理员
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    console.log('检查用户角色:', user.role)
    if (user.role !== 'admin') {
      console.log('非管理员，跳转到首页')
      ElMessage.error('您没有访问该页面的权限')
      next('/')
    } else {
      console.log('管理员，允许访问')
      next()
    }
  } else {
    console.log('允许访问')
    next()
  }
})

export default router
