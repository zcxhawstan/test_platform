<template>
  <div class="login-container">
    <div class="left-background">
      <img 
        src="https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=modern%203D%20test%20platform%20interface%20with%20blue%20theme%2C%20clean%20design%2C%20technology%20concept&image_size=landscape_16_9" 
        alt="测试平台" 
        class="background-image"
      />
    </div>
    
    <div class="right-form">
      <div class="login-card">
        <div class="card-header">
          <h2>测试平台</h2>
        </div>
        
        <div class="form-item">
          <input 
            type="text" 
            placeholder="请输入账号" 
            class="form-input"
            v-model="form.username"
            @keyup="handleKeyUp"
          />
        </div>
        
        <div class="form-item">
          <input 
            type="password" 
            placeholder="请输入密码" 
            class="form-input"
            v-model="form.password"
            @keyup="handleKeyUp"
          />
        </div>
        
        <div class="form-item">
          <button 
            class="login-button"
            @click="handleLogin"
            :disabled="loading"
          >
            {{ loading ? '登录中...' : '登录' }}
          </button>
        </div>
        
        <div class="form-item">
          <button class="register-link">没有账号？注册</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

const form = ref({
  username: '',
  password: ''
})

const loading = ref(false)

const handleLogin = async () => {
  if (!form.value.username.trim() || !form.value.password.trim()) {
    ElMessage.error('请输入账号和密码')
    return
  }

  try {
    loading.value = true
    const response = await userStore.login(form.value)
    
    if (response.code === 200) {
      ElMessage.success('登录成功')
      router.push('/')
    } else {
      ElMessage.error(response.message || '登录失败')
    }
  } catch (error) {
    ElMessage.error('网络错误，请检查服务器连接')
    console.error('Login error:', error)
  } finally {
    loading.value = false
  }
}

const handleKeyUp = (event) => {
  if (event.key === 'Enter') {
    handleLogin()
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.left-background {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.background-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.left-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  z-index: 1;
}

.left-text h1 {
  font-size: 3rem;
  font-weight: 700;
  color: white;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  margin: 0;
}

.right-form {
  width: 400px;
  background: white;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px;
}

.login-card {
  width: 100%;
}

.card-header {
  text-align: center;
  margin-bottom: 30px;
}

.card-header h2 {
  margin: 0;
  font-size: 1.8rem;
  font-weight: 600;
  color: #333;
}

.login-subtitle {
  margin: 5px 0 0 0;
  font-size: 1rem;
  color: #666;
  font-weight: 400;
}

.form-item {
  margin-bottom: 15px;
}

.form-input {
  width: 100%;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
  padding: 12px 15px;
  font-size: 14px;
}

.form-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
  outline: none;
}

.login-button {
  width: 100%;
  border-radius: 8px;
  padding: 12px;
  font-size: 1rem;
  font-weight: 600;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  border: none;
  color: white;
  cursor: pointer;
  margin-top: 10px;
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.register-link {
  background: none;
  border: none;
  color: #3b82f6;
  font-weight: 500;
  cursor: pointer;
  padding: 0;
  font-size: 14px;
  margin-top: 10px;
}

.register-link:hover {
  color: #1d4ed8;
  text-decoration: underline;
}

@media (max-width: 768px) {
  .login-container {
    flex-direction: column;
  }
  
  .left-background {
    height: 40%;
  }
  
  .right-form {
    width: 100%;
    height: 60%;
  }
  
  .left-text h1 {
    font-size: 2.5rem;
  }
  
  .card-header h2 {
    font-size: 1.5rem;
  }
}
</style>