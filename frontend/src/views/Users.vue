<template>
  <div class="users-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <div class="search-box">
            <el-input v-model="searchForm.username" placeholder="请输入用户名" style="width: 200px; margin-right: 10px" />
            <el-button type="primary" @click="loadUsers">查询</el-button>
            <el-button @click="resetSearch">重置</el-button>
          </div>
          <el-button type="primary" @click="showAddDialog">新增用户</el-button>
        </div>
      </template>
      
      <el-table :data="users" v-loading="loading" border>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="email" label="邮箱" width="200" />
        <el-table-column prop="role" label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.role)">{{ getRoleText(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="120">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_active"
              active-text="启用"
              inactive-text="禁用"
              @change="handleStatusChange(row)"
              inline-prompt
              style="--el-switch-on-color: var(--el-color-success); --el-switch-off-color: var(--el-color-danger);"
            />
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button type="warning" size="small" @click="handleResetPassword(row)">重置密码</el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadUsers"
        @current-change="loadUsers"
        style="margin-top: 20px; justify-content: center"
      />
    </el-card>
    
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="isEdit" />
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" />
        </el-form-item>
        
        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input v-model="form.password" :type="showPassword ? 'text' : 'password'">
            <template #append>
              <el-button @click="showPassword = !showPassword" type="text">
                <el-icon v-if="!showPassword"><View /></el-icon>
                <el-icon v-else><Hide /></el-icon>
              </el-button>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role">
            <el-option label="管理员" value="admin" />
            <el-option label="测试开发" value="tester_dev" />
            <el-option label="普通测试" value="tester" />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { View, Hide } from '@element-plus/icons-vue'
import { getUserList, deleteUser, createUser, updateUserStatus, resetPassword } from '@/api/auth'

const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()
const users = ref([])
const showPassword = ref(false)
const passwordVisible = ref({})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const searchForm = reactive({
  username: ''
})

const form = reactive({
  id: null,
  username: '',
  email: '',
  password: '',
  role: 'tester'
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

const dialogTitle = computed(() => isEdit.value ? '编辑用户' : '新增用户')

const loadUsers = async () => {
  loading.value = true
  try {
    const res = await getUserList({
      page: pagination.page,
      page_size: pagination.size,
      username: searchForm.username
    })
    users.value = res.data.results
    pagination.total = res.data.count
  } catch (error) {
    ElMessage.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

const showAddDialog = () => {
  isEdit.value = false
  Object.assign(form, {
    id: null,
    username: '',
    email: '',
    password: '',
    role: 'tester'
  })
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  Object.assign(form, {
    id: row.id,
    username: row.username,
    email: row.email,
    password: '',
    role: row.role
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value.validate()
  submitLoading.value = true
  try {
    if (isEdit.value) {
      ElMessage.success('更新成功')
    } else {
      const response = await createUser(form)
      if (response.code === 201) {
        ElMessage.success('创建成功')
      }
    }
    dialogVisible.value = false
    loadUsers()
  } catch (error) {
    ElMessage.error('操作失败')
  } finally {
    submitLoading.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除用户 ${row.username} 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteUser(row.id)
    ElMessage.success('删除成功')
    loadUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const resetSearch = () => {
  searchForm.username = ''
  loadUsers()
}

const getRoleType = (role) => {
  const typeMap = {
    admin: 'danger',
    tester_dev: 'warning',
    tester: 'info'
  }
  return typeMap[role] || 'info'
}

const getRoleText = (role) => {
  const textMap = {
    admin: '管理员',
    tester_dev: '测试开发',
    tester: '普通测试'
  }
  return textMap[role] || role
}

const handleResetPassword = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要将用户 ${row.username} 的密码重置为默认密码 admin123 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const response = await resetPassword(row.id, { new_password: 'admin123' })
    if (response.code === 200) {
      ElMessage.success('密码重置成功，新密码：admin123')
    } else {
      ElMessage.error('密码重置失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('网络错误，请稍后重试')
      console.error('Reset password error:', error)
    }
  }
}

const handleStatusChange = async (row) => {
  try {
    const response = await updateUserStatus(row.id, { is_active: row.is_active })
    if (response.code === 200) {
      ElMessage.success(row.is_active ? '用户已启用' : '用户已禁用')
    } else {
      // 恢复原状态
      row.is_active = !row.is_active
      ElMessage.error('状态更新失败')
    }
  } catch (error) {
    // 恢复原状态
    row.is_active = !row.is_active
    ElMessage.error('网络错误，请稍后重试')
    console.error('Status change error:', error)
  }
}

const formatDateTime = (dateString) => {
  if (!dateString) return ''
  
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return ''
  
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.users-page {
  padding: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.search-box {
  display: flex;
  align-items: center;
  margin: 0 20px;
}
</style>
