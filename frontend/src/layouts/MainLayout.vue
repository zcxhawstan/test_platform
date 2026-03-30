<template>
  <el-container class="main-layout">
    <el-aside width="200px">
      <div class="logo">
        <h3>测试平台</h3>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Dashboard /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        
        <el-menu-item index="/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        
        <el-menu-item index="/testcases">
          <el-icon><Document /></el-icon>
          <span>测试用例</span>
        </el-menu-item>
        
        <el-menu-item index="/testplans">
          <el-icon><Calendar /></el-icon>
          <span>测试计划</span>
        </el-menu-item>
        
        <el-menu-item index="/defects">
          <el-icon><Warning /></el-icon>
          <span>缺陷管理</span>
        </el-menu-item>
        
        <el-menu-item index="/apitest">
          <el-icon><Connection /></el-icon>
          <span>接口测试</span>
        </el-menu-item>
        
        <el-menu-item index="/environments">
          <el-icon><Setting /></el-icon>
          <span>环境管理</span>
        </el-menu-item>
        
        <el-menu-item index="/logs">
          <el-icon><DocumentCopy /></el-icon>
          <span>日志管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <el-container>
      <el-header>
        <div class="header-content">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
          
          <div class="user-info">
            <el-dropdown>
              <span class="el-dropdown-link">
                <el-icon><User /></el-icon>
                {{ userStore.username }}
                <el-icon class="el-icon--right"><arrow-down /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </el-header>
      
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)
const currentTitle = computed(() => route.meta.title || '仪表盘')

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await userStore.logout()
    ElMessage.success('退出成功')
    router.push('/login')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('退出失败')
    }
  }
}
</script>

<style scoped>
.main-layout {
  height: 100%;
}

.el-aside {
  background-color: #304156;
  overflow-x: hidden;
}

.logo {
  height: 50px;
  line-height: 50px;
  text-align: center;
  color: #fff;
  background-color: #2b3a4a;
}

.logo h3 {
  margin: 0;
  font-size: 18px;
}

.el-header {
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-info {
  cursor: pointer;
}

.el-dropdown-link {
  display: flex;
  align-items: center;
  gap: 5px;
}

.el-main {
  background-color: #f0f2f5;
  padding: 20px;
}
</style>
