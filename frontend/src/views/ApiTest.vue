<template>
  <div class="apitest-page">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="API环境" name="environments">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>API环境管理</span>
              <el-button type="primary" @click="showAddEnvDialog">新增环境</el-button>
            </div>
          </template>
          
          <el-table :data="environments" v-loading="envLoading" border>
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="name" label="环境名称" width="150" />
            <el-table-column prop="base_url" label="基础URL" width="300" />
            <el-table-column prop="description" label="描述" />
            <el-table-column prop="created_by_name" label="创建人" width="120" />
            <el-table-column prop="created_at" label="创建时间" width="180" />
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button type="primary" size="small" @click="handleEditEnv(row)">编辑</el-button>
                <el-button type="danger" size="small" @click="handleDeleteEnv(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
      
      <el-tab-pane label="API用例" name="cases">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>API测试用例</span>
              <el-button type="primary" @click="showAddCaseDialog">新增用例</el-button>
            </div>
          </template>
          
          <el-form :inline="true" :model="caseFilters" class="filter-form">
            <el-form-item label="请求方法">
              <el-select v-model="caseFilters.method" placeholder="请选择" clearable>
                <el-option label="GET" value="GET" />
                <el-option label="POST" value="POST" />
                <el-option label="PUT" value="PUT" />
                <el-option label="DELETE" value="DELETE" />
                <el-option label="PATCH" value="PATCH" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="loadApiTestCases">查询</el-button>
              <el-button @click="resetCaseFilters">重置</el-button>
            </el-form-item>
          </el-form>
          
          <el-table :data="apiTestCases" v-loading="caseLoading" border>
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="name" label="用例名称" width="200" />
            <el-table-column prop="method" label="方法" width="80">
              <template #default="{ row }">
                <el-tag :type="getMethodType(row.method)">{{ row.method }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="path" label="路径" width="200" />
            <el-table-column prop="environment_name" label="环境" width="120" />
            <el-table-column prop="created_by_name" label="创建人" width="120" />
            <el-table-column prop="created_at" label="创建时间" width="180" />
            <el-table-column label="操作" width="250">
              <template #default="{ row }">
                <el-button type="success" size="small" @click="handleExecuteCase(row)">执行</el-button>
                <el-button type="warning" size="small" @click="handleEditCase(row)">编辑</el-button>
                <el-button type="danger" size="small" @click="handleDeleteCase(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <el-pagination
            v-model:current-page="casePagination.page"
            v-model:page-size="casePagination.size"
            :total="casePagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="loadApiTestCases"
            @current-change="loadApiTestCases"
            style="margin-top: 20px; justify-content: center"
          />
        </el-card>
      </el-tab-pane>
      
      <el-tab-pane label="执行记录" name="executions">
        <el-card>
          <template #header>
            <span>执行记录</span>
          </template>
          
          <el-table :data="executions" v-loading="executionLoading" border>
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="test_case_name" label="用例名称" width="200" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getExecutionStatusType(row.status)">{{ getExecutionStatusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="response_status_code" label="响应码" width="100" />
            <el-table-column prop="response_time" label="响应时间(ms)" width="120" />
            <el-table-column prop="executed_by_name" label="执行人" width="120" />
            <el-table-column prop="executed_at" label="执行时间" width="180" />
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button type="primary" size="small" @click="handleViewExecution(row)">查看</el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <el-pagination
            v-model:current-page="executionPagination.page"
            v-model:page-size="executionPagination.size"
            :total="executionPagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="loadExecutions"
            @current-change="loadExecutions"
            style="margin-top: 20px; justify-content: center"
          />
        </el-card>
      </el-tab-pane>
    </el-tabs>
    
    <el-dialog v-model="envDialogVisible" :title="envDialogTitle" width="600px">
      <el-form ref="envFormRef" :model="envForm" :rules="envRules" label-width="100px">
        <el-form-item label="环境名称" prop="name">
          <el-input v-model="envForm.name" />
        </el-form-item>
        
        <el-form-item label="基础URL" prop="base_url">
          <el-input v-model="envForm.base_url" />
        </el-form-item>
        
        <el-form-item label="环境描述">
          <el-input v-model="envForm.description" type="textarea" :rows="3" />
        </el-form-item>
        
        <el-form-item label="公共请求头">
          <el-input v-model="envForm.headers" type="textarea" :rows="2" placeholder='{"Content-Type": "application/json"}' />
        </el-form-item>
        
        <el-form-item label="环境变量">
          <el-input v-model="envForm.variables" type="textarea" :rows="2" placeholder='{"env": "test"}' />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="envDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="envSubmitLoading" @click="handleEnvSubmit">确定</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="caseDialogVisible" :title="caseDialogTitle" width="800px">
      <el-form ref="caseFormRef" :model="caseForm" :rules="caseRules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="用例名称" prop="name">
              <el-input v-model="caseForm.name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="请求方法" prop="method">
              <el-select v-model="caseForm.method">
                <el-option label="GET" value="GET" />
                <el-option label="POST" value="POST" />
                <el-option label="PUT" value="PUT" />
                <el-option label="DELETE" value="DELETE" />
                <el-option label="PATCH" value="PATCH" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="所属环境" prop="environment">
              <el-select v-model="caseForm.environment">
                <el-option v-for="env in environments" :key="env.id" :label="env.name" :value="env.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="预期状态码" prop="expected_status_code">
              <el-input-number v-model="caseForm.expected_status_code" :min="100" :max="599" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="请求路径" prop="path">
          <el-input v-model="caseForm.path" placeholder="/api/users" />
        </el-form-item>
        
        <el-form-item label="用例描述">
          <el-input v-model="caseForm.description" type="textarea" :rows="2" />
        </el-form-item>
        
        <el-form-item label="请求头">
          <el-input v-model="caseForm.headers" type="textarea" :rows="2" placeholder='{"Authorization": "Bearer token"}' />
        </el-form-item>
        
        <el-form-item label="请求参数">
          <el-input v-model="caseForm.params" type="textarea" :rows="2" placeholder='{"page": 1}' />
        </el-form-item>
        
        <el-form-item label="请求体">
          <el-input v-model="caseForm.body" type="textarea" :rows="3" placeholder='{"username": "test"}' />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="caseDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="caseSubmitLoading" @click="handleCaseSubmit">确定</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="executionVisible" title="执行详情" width="800px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="用例名称">{{ currentExecution.test_case_name }}</el-descriptions-item>
        <el-descriptions-item label="执行状态">
          <el-tag :type="getExecutionStatusType(currentExecution.status)">{{ getExecutionStatusText(currentExecution.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="请求URL" :span="2">{{ currentExecution.request_url }}</el-descriptions-item>
        <el-descriptions-item label="响应状态码">{{ currentExecution.response_status_code }}</el-descriptions-item>
        <el-descriptions-item label="响应时间">{{ currentExecution.response_time }}ms</el-descriptions-item>
        <el-descriptions-item label="请求头" :span="2">
          <pre>{{ JSON.stringify(currentExecution.request_headers, null, 2) }}</pre>
        </el-descriptions-item>
        <el-descriptions-item label="请求体" :span="2">
          <pre>{{ JSON.stringify(currentExecution.request_body, null, 2) }}</pre>
        </el-descriptions-item>
        <el-descriptions-item label="响应头" :span="2">
          <pre>{{ JSON.stringify(currentExecution.response_headers, null, 2) }}</pre>
        </el-descriptions-item>
        <el-descriptions-item label="响应体" :span="2">
          <pre>{{ JSON.stringify(currentExecution.response_body, null, 2) }}</pre>
        </el-descriptions-item>
        <el-descriptions-item v-if="currentExecution.error_message" label="错误信息" :span="2" style="color: red">
          {{ currentExecution.error_message }}
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getEnvironmentList, createEnvironment, updateEnvironment, deleteEnvironment } from '@/api/apitest'
import { getApiTestCaseList, createApiTestCase, updateApiTestCase, deleteApiTestCase, executeApiTest, getExecutionList } from '@/api/apitest'

const activeTab = ref('environments')
const envLoading = ref(false)
const caseLoading = ref(false)
const executionLoading = ref(false)
const envSubmitLoading = ref(false)
const caseSubmitLoading = ref(false)
const envDialogVisible = ref(false)
const caseDialogVisible = ref(false)
const executionVisible = ref(false)
const isEnvEdit = ref(false)
const isCaseEdit = ref(false)
const envFormRef = ref()
const caseFormRef = ref()
const environments = ref([])
const apiTestCases = ref([])
const executions = ref([])
const currentExecution = ref({})

const casePagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const executionPagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const caseFilters = reactive({
  method: ''
})

const envForm = reactive({
  id: null,
  name: '',
  base_url: '',
  description: '',
  headers: '{}',
  variables: '{}'
})

const caseForm = reactive({
  id: null,
  name: '',
  description: '',
  method: 'GET',
  path: '',
  headers: '{}',
  params: '{}',
  body: '{}',
  expected_status_code: 200,
  expected_response: '{}',
  assertions: '[]',
  environment: null
})

const envRules = {
  name: [{ required: true, message: '请输入环境名称', trigger: 'blur' }],
  base_url: [{ required: true, message: '请输入基础URL', trigger: 'blur' }]
}

const caseRules = {
  name: [{ required: true, message: '请输入用例名称', trigger: 'blur' }],
  method: [{ required: true, message: '请选择请求方法', trigger: 'change' }],
  path: [{ required: true, message: '请输入请求路径', trigger: 'blur' }],
  environment: [{ required: true, message: '请选择所属环境', trigger: 'change' }]
}

const envDialogTitle = computed(() => isEnvEdit.value ? '编辑环境' : '新增环境')
const caseDialogTitle = computed(() => isCaseEdit.value ? '编辑用例' : '新增用例')

const loadEnvironments = async () => {
  envLoading.value = true
  try {
    const res = await getEnvironmentList({ page_size: 100 })
    environments.value = res.data.results
  } catch (error) {
    console.error('加载环境列表失败:', error)
    ElMessage.error('加载环境列表失败')
  } finally {
    envLoading.value = false
  }
}

const loadApiTestCases = async () => {
  caseLoading.value = true
  try {
    const res = await getApiTestCaseList({
      page: casePagination.page,
      page_size: casePagination.size,
      ...caseFilters
    })
    apiTestCases.value = res.data.results
    casePagination.total = res.data.count
  } catch (error) {
    console.error('加载用例列表失败:', error)
    ElMessage.error('加载用例列表失败')
  } finally {
    caseLoading.value = false
  }
}

const loadExecutions = async () => {
  executionLoading.value = true
  try {
    const res = await getExecutionList({
      page: executionPagination.page,
      page_size: executionPagination.size
    })
    executions.value = res.data.results
    executionPagination.total = res.data.count
  } catch (error) {
    console.error('加载执行记录失败:', error)
    ElMessage.error('加载执行记录失败')
  } finally {
    executionLoading.value = false
  }
}

const resetCaseFilters = () => {
  Object.assign(caseFilters, { method: '' })
  loadApiTestCases()
}

const showAddEnvDialog = () => {
  isEnvEdit.value = false
  Object.assign(envForm, {
    id: null,
    name: '',
    base_url: '',
    description: '',
    headers: '{}',
    variables: '{}'
  })
  envDialogVisible.value = true
}

const handleEditEnv = (row) => {
  isEnvEdit.value = true
  Object.assign(envForm, {
    id: row.id,
    name: row.name,
    base_url: row.base_url,
    description: row.description,
    headers: JSON.stringify(row.headers),
    variables: JSON.stringify(row.variables)
  })
  envDialogVisible.value = true
}

const handleEnvSubmit = async () => {
  await envFormRef.value.validate()
  envSubmitLoading.value = true
  try {
    const data = {
      ...envForm,
      headers: JSON.parse(envForm.headers),
      variables: JSON.parse(envForm.variables)
    }
    if (isEnvEdit.value) {
      await updateEnvironment(envForm.id, data)
      ElMessage.success('更新成功')
    } else {
      await createEnvironment(data)
      ElMessage.success('创建成功')
    }
    envDialogVisible.value = false
    loadEnvironments()
  } catch (error) {
    ElMessage.error('操作失败')
  } finally {
    envSubmitLoading.value = false
  }
}

const handleDeleteEnv = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除环境 ${row.name} 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteEnvironment(row.id)
    ElMessage.success('删除成功')
    loadEnvironments()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const showAddCaseDialog = () => {
  isCaseEdit.value = false
  Object.assign(caseForm, {
    id: null,
    name: '',
    description: '',
    method: 'GET',
    path: '',
    headers: '{}',
    params: '{}',
    body: '{}',
    expected_status_code: 200,
    expected_response: '{}',
    assertions: '[]',
    environment: environments.value[0]?.id || null
  })
  caseDialogVisible.value = true
}

const handleEditCase = (row) => {
  isCaseEdit.value = true
  Object.assign(caseForm, {
    id: row.id,
    name: row.name,
    description: row.description,
    method: row.method,
    path: row.path,
    headers: JSON.stringify(row.headers),
    params: JSON.stringify(row.params),
    body: JSON.stringify(row.body),
    expected_status_code: row.expected_status_code,
    expected_response: JSON.stringify(row.expected_response),
    assertions: JSON.stringify(row.assertions),
    environment: row.environment
  })
  caseDialogVisible.value = true
}

const handleCaseSubmit = async () => {
  await caseFormRef.value.validate()
  caseSubmitLoading.value = true
  try {
    const data = {
      ...caseForm,
      headers: JSON.parse(caseForm.headers),
      params: JSON.parse(caseForm.params),
      body: JSON.parse(caseForm.body),
      expected_response: JSON.parse(caseForm.expected_response),
      assertions: JSON.parse(caseForm.assertions)
    }
    if (isCaseEdit.value) {
      await updateApiTestCase(caseForm.id, data)
      ElMessage.success('更新成功')
    } else {
      await createApiTestCase(data)
      ElMessage.success('创建成功')
    }
    caseDialogVisible.value = false
    loadApiTestCases()
  } catch (error) {
    ElMessage.error('操作失败')
  } finally {
    caseSubmitLoading.value = false
  }
}

const handleExecuteCase = async (row) => {
  console.log('开始执行用例:', row)
  console.log('用例ID:', row.id)
  try {
    console.log('准备发送执行请求...')
    const result = await executeApiTest({ test_case_id: row.id })
    console.log('执行结果:', result)
    ElMessage.success('执行成功')
    activeTab.value = 'executions'
    loadExecutions()
  } catch (error) {
    console.error('执行失败，详细错误:', error)
    if (error.response) {
      console.error('响应状态:', error.response.status)
      console.error('响应数据:', error.response.data)
      ElMessage.error(`执行失败: ${error.response.data?.message || error.message}`)
    } else if (error.request) {
      console.error('请求已发送但无响应:', error.request)
      ElMessage.error('请求超时或网络错误')
    } else {
      console.error('请求配置错误:', error.message)
      ElMessage.error(`执行失败: ${error.message}`)
    }
  }
}

const handleDeleteCase = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除用例 ${row.name} 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteApiTestCase(row.id)
    ElMessage.success('删除成功')
    loadApiTestCases()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleViewExecution = (row) => {
  currentExecution.value = row
  executionVisible.value = true
}

const getMethodType = (method) => {
  const typeMap = { GET: 'success', POST: 'primary', PUT: 'warning', DELETE: 'danger', PATCH: 'info' }
  return typeMap[method] || 'info'
}

const getExecutionStatusType = (status) => {
  const typeMap = { pending: 'info', running: 'warning', passed: 'success', failed: 'danger', error: 'danger' }
  return typeMap[status] || 'info'
}

const getExecutionStatusText = (status) => {
  const textMap = { pending: '待执行', running: '执行中', passed: '通过', failed: '失败', error: '错误' }
  return textMap[status] || status
}

onMounted(() => {
  loadEnvironments()
  loadApiTestCases()
  loadExecutions()
})
</script>

<style scoped>
.apitest-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-form {
  margin-bottom: 20px;
}

pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
