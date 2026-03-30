<template>
  <div class="logs-page">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="操作日志" name="operations">
        <el-card>
          <template #header>
            <span>操作日志</span>
          </template>
          
          <el-form :inline="true" :model="opFilters" class="filter-form">
            <el-form-item label="操作类型">
              <el-select v-model="opFilters.action" placeholder="请选择" clearable>
                <el-option label="创建" value="create" />
                <el-option label="更新" value="update" />
                <el-option label="删除" value="delete" />
                <el-option label="查询" value="query" />
                <el-option label="执行" value="execute" />
                <el-option label="登录" value="login" />
                <el-option label="登出" value="logout" />
              </el-select>
            </el-form-item>
            <el-form-item label="操作模块">
              <el-select v-model="opFilters.module" placeholder="请选择" clearable>
                <el-option label="用户管理" value="user" />
                <el-option label="测试用例" value="test_case" />
                <el-option label="测试计划" value="test_plan" />
                <el-option label="缺陷管理" value="defect" />
                <el-option label="接口测试" value="api_test" />
                <el-option label="环境管理" value="environment" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="loadOperationLogs">查询</el-button>
              <el-button @click="resetOpFilters">重置</el-button>
            </el-form-item>
          </el-form>
          
          <el-table :data="operationLogs" v-loading="opLoading" border>
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="username" label="操作人" width="120" />
            <el-table-column prop="action" label="操作类型" width="100">
              <template #default="{ row }">
                <el-tag>{{ getActionText(row.action) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="module" label="操作模块" width="120">
              <template #default="{ row }">
                <el-tag type="info">{{ getModuleText(row.module) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="操作描述" width="200" />
            <el-table-column prop="request_method" label="请求方法" width="80" />
            <el-table-column prop="request_url" label="请求URL" width="200" />
            <el-table-column prop="response_status" label="响应状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.response_status === 200 ? 'success' : 'danger'">{{ row.response_status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="execution_time" label="执行时间(ms)" width="120" />
            <el-table-column prop="ip_address" label="IP地址" width="130" />
            <el-table-column prop="created_at" label="创建时间" width="180" />
          </el-table>
          
          <el-pagination
            v-model:current-page="opPagination.page"
            v-model:page-size="opPagination.size"
            :total="opPagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="loadOperationLogs"
            @current-change="loadOperationLogs"
            style="margin-top: 20px; justify-content: center"
          />
        </el-card>
      </el-tab-pane>
      
      <el-tab-pane label="错误日志" name="errors">
        <el-card>
          <template #header>
            <span>错误日志</span>
          </template>
          
          <el-form :inline="true" :model="errorFilters" class="filter-form">
            <el-form-item label="日志级别">
              <el-select v-model="errorFilters.level" placeholder="请选择" clearable>
                <el-option label="DEBUG" value="debug" />
                <el-option label="INFO" value="info" />
                <el-option label="WARNING" value="warning" />
                <el-option label="ERROR" value="error" />
                <el-option label="CRITICAL" value="critical" />
              </el-select>
            </el-form-item>
            <el-form-item label="模块">
              <el-select v-model="errorFilters.module" placeholder="请选择" clearable>
                <el-option label="用户管理" value="user" />
                <el-option label="测试用例" value="test_case" />
                <el-option label="测试计划" value="test_plan" />
                <el-option label="缺陷管理" value="defect" />
                <el-option label="接口测试" value="api_test" />
                <el-option label="环境管理" value="environment" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="loadErrorLogs">查询</el-button>
              <el-button @click="resetErrorFilters">重置</el-button>
            </el-form-item>
          </el-form>
          
          <el-table :data="errorLogs" v-loading="errorLoading" border>
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="level" label="日志级别" width="100">
              <template #default="{ row }">
                <el-tag :type="getLevelType(row.level)">{{ row.level }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="module" label="模块" width="120">
              <template #default="{ row }">
                <el-tag type="info">{{ getModuleText(row.module) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="message" label="错误信息" width="300" show-overflow-tooltip />
            <el-table-column prop="username" label="用户" width="120" />
            <el-table-column prop="ip_address" label="IP地址" width="130" />
            <el-table-column prop="created_at" label="创建时间" width="180" />
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button type="primary" size="small" @click="handleViewError(row)">查看</el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <el-pagination
            v-model:current-page="errorPagination.page"
            v-model:page-size="errorPagination.size"
            :total="errorPagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="loadErrorLogs"
            @current-change="loadErrorLogs"
            style="margin-top: 20px; justify-content: center"
          />
        </el-card>
      </el-tab-pane>
    </el-tabs>
    
    <el-dialog v-model="errorDetailVisible" title="错误详情" width="800px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="日志级别">
          <el-tag :type="getLevelType(currentError.level)">{{ currentError.level }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="模块">
          <el-tag type="info">{{ getModuleText(currentError.module) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="错误信息" :span="2">{{ currentError.message }}</el-descriptions-item>
        <el-descriptions-item label="请求URL" :span="2">{{ currentError.request_url }}</el-descriptions-item>
        <el-descriptions-item label="用户">{{ currentError.username }}</el-descriptions-item>
        <el-descriptions-item label="IP地址">{{ currentError.ip_address }}</el-descriptions-item>
        <el-descriptions-item label="创建时间" :span="2">{{ currentError.created_at }}</el-descriptions-item>
        <el-descriptions-item label="堆栈信息" :span="2">
          <pre style="white-space: pre-wrap; word-wrap: break-word; max-height: 400px; overflow-y: auto">{{ currentError.traceback }}</pre>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getOperationLogs, getErrorLogs } from '@/api/log'

const activeTab = ref('operations')
const opLoading = ref(false)
const errorLoading = ref(false)
const errorDetailVisible = ref(false)
const operationLogs = ref([])
const errorLogs = ref([])
const currentError = ref({})

const opPagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const errorPagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const opFilters = reactive({
  action: '',
  module: ''
})

const errorFilters = reactive({
  level: '',
  module: ''
})

const loadOperationLogs = async () => {
  opLoading.value = true
  try {
    const res = await getOperationLogs({
      page: opPagination.page,
      page_size: opPagination.size,
      ...opFilters
    })
    operationLogs.value = res.data.results
    opPagination.total = res.data.count
  } catch (error) {
    ElMessage.error('加载操作日志失败')
  } finally {
    opLoading.value = false
  }
}

const resetOpFilters = () => {
  Object.assign(opFilters, { action: '', module: '' })
  loadOperationLogs()
}

const loadErrorLogs = async () => {
  errorLoading.value = true
  try {
    const res = await getErrorLogs({
      page: errorPagination.page,
      page_size: errorPagination.size,
      ...errorFilters
    })
    errorLogs.value = res.data.results
    errorPagination.total = res.data.count
  } catch (error) {
    ElMessage.error('加载错误日志失败')
  } finally {
    errorLoading.value = false
  }
}

const resetErrorFilters = () => {
  Object.assign(errorFilters, { level: '', module: '' })
  loadErrorLogs()
}

const handleViewError = (row) => {
  currentError.value = row
  errorDetailVisible.value = true
}

const getActionText = (action) => {
  const textMap = { create: '创建', update: '更新', delete: '删除', query: '查询', execute: '执行', login: '登录', logout: '登出' }
  return textMap[action] || action
}

const getModuleText = (module) => {
  const textMap = { user: '用户管理', test_case: '测试用例', test_plan: '测试计划', defect: '缺陷管理', api_test: '接口测试', environment: '环境管理' }
  return textMap[module] || module
}

const getLevelType = (level) => {
  const typeMap = { debug: 'info', info: 'success', warning: 'warning', error: 'danger', critical: 'danger' }
  return typeMap[level] || 'info'
}

onMounted(() => {
  loadOperationLogs()
  loadErrorLogs()
})
</script>

<style scoped>
.logs-page {
  padding: 20px;
}

.filter-form {
  margin-bottom: 20px;
}

pre {
  margin: 0;
  background-color: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
}
</style>
