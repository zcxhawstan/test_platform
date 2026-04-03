<template>
  <div class="automation-environments-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>环境配置管理</span>
          <div class="search-box">
            <el-input v-model="searchForm.name" placeholder="请输入环境名称" style="width: 200px; margin-right: 10px" />
            <el-button type="primary" @click="loadEnvironments">查询</el-button>
            <el-button @click="resetSearch">重置</el-button>
          </div>
          <el-button type="primary" @click="showAddDialog">新增环境</el-button>
        </div>
      </template>
      
      <el-table :data="environments" v-loading="loading" border>
        <el-table-column prop="id" label="环境ID" width="80" />
        <el-table-column prop="name" label="环境名称" />
        <el-table-column prop="environment_type" label="环境类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getEnvironmentType(row.environment_type)">{{ getEnvironmentText(row.environment_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            <span style="font-size: 13px; color: #606266;">{{ formatDateTime(row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="is_connected" label="连接状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_connected ? 'success' : 'danger'" size="small">
              {{ row.is_connected ? '已连接' : '未连接' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" align="center">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
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
        @size-change="loadEnvironments"
        @current-change="loadEnvironments"
        style="margin-top: 20px; justify-content: center"
      />
    </el-card>
    
    <!-- 新增/编辑环境对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="700px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="环境名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入环境名称" />
        </el-form-item>
        
        <el-form-item label="环境类型" prop="environment_type">
          <el-select v-model="form.environment_type">
            <el-option label="测试环境" value="test" />
            <el-option label="预发环境" value="staging" />
            <el-option label="生产环境" value="production" />
            <el-option label="自定义环境" value="custom" />
          </el-select>
        </el-form-item>
        

        
        <el-form-item label="环境变量" prop="variables">
          <el-input v-model="variablesText" type="textarea" placeholder="请输入环境变量，格式：key1=value1\nkey2=value2" />
        </el-form-item>
        
        <el-form-item label="环境描述" prop="description">
          <el-input v-model="form.description" type="textarea" placeholder="请输入环境描述" />
        </el-form-item>
        
        <el-divider>执行机配置</el-divider>
        
        <el-form-item label="执行机IP" prop="executor_ip">
          <el-input v-model="form.executor_ip" placeholder="请输入执行机IP地址" />
        </el-form-item>
        
        <el-form-item label="SSH端口" prop="executor_port">
          <el-input-number v-model="form.executor_port" :min="1" :max="65535" />
        </el-form-item>
        
        <el-form-item label="SSH用户名" prop="executor_username">
          <el-input v-model="form.executor_username" placeholder="请输入SSH用户名" />
        </el-form-item>
        
        <el-form-item label="SSH密码" prop="executor_password">
          <el-input v-model="form.executor_password" type="password" placeholder="请输入SSH密码" />
        </el-form-item>
        
        <el-divider>Docker配置</el-divider>
        
        <el-form-item label="Docker镜像" prop="docker_image">
          <el-input v-model="form.docker_image" placeholder="请输入Docker镜像，如 python:3.9" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="testLoading" @click="testConnectionInDialog" :disabled="!canTestConnection" plain>测试连接</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit" :disabled="!isConnectionTested">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getEnvironmentList, createEnvironment, updateEnvironment, deleteEnvironment, testEnvironmentConnection, testSSHConnection
} from '@/api/automation'

const loading = ref(false)
const submitLoading = ref(false)
const testLoading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()
const environments = ref([])
const isConnectionTested = ref(false)

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const searchForm = reactive({
  name: ''
})

const form = reactive({
  id: null,
  name: '',
  environment_type: 'test',
  variables: {},
  description: '',
  executor_ip: '',
  executor_port: 22,
  executor_username: '',
  executor_password: '',
  docker_image: 'python:3.9',
  is_connected: false
})

const variablesText = ref('')

const rules = {
  name: [{ required: true, message: '请输入环境名称', trigger: 'blur' }],
  executor_ip: [{ required: true, message: '请输入执行机IP', trigger: 'blur' }],
  executor_username: [{ required: true, message: '请输入SSH用户名', trigger: 'blur' }],
  executor_password: [{ required: true, message: '请输入SSH密码', trigger: 'blur' }],
  docker_image: [{ required: true, message: '请输入Docker镜像', trigger: 'blur' }]
}

const dialogTitle = computed(() => isEdit.value ? '编辑环境' : '新增环境')

const canTestConnection = computed(() => {
  return form.executor_ip && form.executor_username && form.executor_password
})

const loadEnvironments = async () => {
  loading.value = true
  try {
    const res = await getEnvironmentList({
      page: pagination.page,
      page_size: pagination.size,
      name: searchForm.name
    })
    environments.value = res.results
    pagination.total = res.count
  } catch (error) {
    ElMessage.error('加载环境列表失败')
  } finally {
    loading.value = false
  }
}

const showAddDialog = () => {
  isEdit.value = false
  isConnectionTested.value = false
  Object.assign(form, {
    id: null,
    name: '',
    environment_type: 'test',
    variables: {},
    description: '',
    executor_ip: '',
    executor_port: 22,
    executor_username: '',
    executor_password: '',
    docker_image: 'python:3.9',
    is_connected: false
  })
  variablesText.value = ''
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  isConnectionTested.value = row.is_connected || false
  Object.assign(form, {
    id: row.id,
    name: row.name,
    environment_type: row.environment_type,
    variables: row.variables || {},
    description: row.description,
    executor_ip: row.executor_ip || '',
    executor_port: row.executor_port || 22,
    executor_username: row.executor_username || '',
    executor_password: row.executor_password || '',
    docker_image: row.docker_image || 'python:3.9',
    is_connected: row.is_connected || false
  })
  // 将variables对象转换为文本格式
  variablesText.value = Object.entries(row.variables || {}).map(([key, value]) => `${key}=${value}`).join('\n')
  dialogVisible.value = true
}

const handleSubmit = async () => {
  // 将文本格式的环境变量转换为对象
  try {
    form.variables = variablesText.value.split('\n')
      .filter(line => line.trim())
      .reduce((acc, line) => {
        const [key, ...valueParts] = line.split('=')
        acc[key.trim()] = valueParts.join('=').trim()
        return acc
      }, {})
  } catch (error) {
    ElMessage.error('环境变量格式错误')
    return
  }
  

  
  await formRef.value.validate()
  submitLoading.value = true
  try {
    if (isEdit.value) {
      await updateEnvironment(form.id, form)
      ElMessage.success('环境更新成功')
    } else {
      await createEnvironment(form)
      ElMessage.success('环境创建成功')
    }
    dialogVisible.value = false
    loadEnvironments()
  } catch (error) {
    ElMessage.error('操作失败')
  } finally {
    submitLoading.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除环境 ${row.name} 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteEnvironment(row.id)
    ElMessage.success('环境删除成功')
    loadEnvironments()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const testConnection = async (row) => {
  try {
    const res = await testEnvironmentConnection(row.id)
    ElMessage.success(res.message)
    loadEnvironments()
  } catch (error) {
    ElMessage.error(error.message || '测试连接失败')
  }
}

const testConnectionInDialog = async () => {
  // 先验证SSH配置是否完整
  if (!form.executor_ip || !form.executor_username || !form.executor_password) {
    ElMessage.error('请先填写完整的SSH配置信息')
    return
  }
  
  testLoading.value = true
  try {
    // 创建临时环境数据进行测试
    const testData = {
      executor_ip: form.executor_ip,
      executor_port: form.executor_port || 22,
      executor_username: form.executor_username,
      executor_password: form.executor_password
    }
    
    // 调用后端API测试连接
    const res = await testSSHConnection(testData)
    
    if (res.data.is_connected) {
      ElMessage.success('SSH连接测试成功！')
      isConnectionTested.value = true
      form.is_connected = true
    } else {
      ElMessage.error('SSH连接测试失败，请检查配置信息')
      isConnectionTested.value = false
    }
  } catch (error) {
    ElMessage.error(error.message || 'SSH连接测试失败')
    isConnectionTested.value = false
  } finally {
    testLoading.value = false
  }
}

const resetSearch = () => {
  searchForm.name = ''
  loadEnvironments()
}

const getEnvironmentType = (type) => {
  const typeMap = {
    test: 'info',
    staging: 'warning',
    production: 'danger',
    custom: 'primary'
  }
  return typeMap[type] || 'info'
}

const getEnvironmentText = (type) => {
  const textMap = {
    test: '测试环境',
    staging: '预发环境',
    production: '生产环境',
    custom: '自定义环境'
  }
  return textMap[type] || type
}

const formatDateTime = (dateTimeStr) => {
  if (!dateTimeStr) return '-'
  const date = new Date(dateTimeStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

onMounted(() => {
  loadEnvironments()
})
</script>

<style scoped>
.automation-environments-page {
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
