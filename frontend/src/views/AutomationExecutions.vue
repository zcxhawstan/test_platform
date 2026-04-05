<template>
  <div class="automation-executions-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>执行历史管理</span>
          <div class="search-box">
            <el-input v-model="searchForm.task_name" placeholder="请输入任务名称" style="width: 200px; margin-right: 10px" />
            <el-select v-model="searchForm.status" placeholder="选择状态" style="width: 120px; margin-right: 10px">
              <el-option label="全部" value="" />
              <el-option label="待执行" value="pending" />
              <el-option label="执行中" value="running" />
              <el-option label="执行成功" value="success" />
              <el-option label="执行失败" value="failed" />
              <el-option label="执行异常" value="error" />
            </el-select>
            <el-button type="primary" @click="loadExecutions">查询</el-button>
            <el-button @click="resetSearch">重置</el-button>
            <el-button v-if="isAdmin" type="danger" @click="handleBulkDelete" :disabled="selectedExecutions.length === 0">批量删除</el-button>
          </div>
        </div>
      </template>
      
      <el-table :data="executions" v-loading="loading" border @selection-change="handleSelectionChange">
        <el-table-column v-if="isAdmin" type="selection" width="55" />
        <el-table-column prop="id" label="执行ID" width="80" />
        <el-table-column prop="task_name" label="任务名称" min-width="180">
          <template #default="{ row }">
            <div class="task-name-cell">
              {{ row.task_name || (row.task ? row.task.name : '-') }}
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="environment_name" label="执行环境" width="150">
          <template #default="{ row }">
            {{ row.environment_name || (row.environment ? row.environment.name : '-') }}
          </template>
        </el-table-column>
        <el-table-column prop="executor_username" label="执行人" width="120">
          <template #default="{ row }">
            {{ row.executor_username || (row.executor ? row.executor.username : '-') }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="开始时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.start_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="执行时长(秒)" width="120" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-dropdown>
              <el-button type="primary" size="small">
                操作
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="handleViewLogs(row)">
                    <el-icon><View /></el-icon>
                    查看日志
                  </el-dropdown-item>
                  <el-dropdown-item @click="handleViewReports(row)">
                    <el-icon><Document /></el-icon>
                    查看报告
                  </el-dropdown-item>
                  <el-dropdown-item @click="handleDownloadReportFromRow(row)">
                    <el-icon><Download /></el-icon>
                    下载报告
                  </el-dropdown-item>
                  <el-dropdown-item v-if="isAdmin" @click="handleDelete(row)" danger>
                    <el-icon><Delete /></el-icon>
                    删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadExecutions"
        @current-change="loadExecutions"
        style="margin-top: 20px; justify-content: center"
      />
    </el-card>
    
    <!-- 日志查看对话框 -->
    <el-dialog v-model="logsDialogVisible" title="执行日志" width="900px" height="600px">
      <div class="logs-container" v-loading="logsLoading">
        <div v-if="logs.length === 0" class="empty-logs">暂无日志</div>
        <div v-else class="logs-content">
          <div v-for="log in logs" :key="log.id" :class="['log-item', `log-${log.level ? log.level.toLowerCase() : 'info'}`]">
            <span class="log-time">{{ formatDateTime(log.timestamp) }}</span>
            <span class="log-level">{{ log.level }}</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="logsDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
    
    <!-- 报告查看对话框 -->
    <el-dialog v-model="reportsDialogVisible" title="测试报告" width="900px">
      <div class="reports-container" v-loading="reportsLoading">
        <div v-if="reports.length === 0" class="empty-reports">暂无报告</div>
        <div v-else class="reports-content">
          <el-table :data="reports" border style="width: 100%">
            <el-table-column prop="id" label="报告ID" width="80" />
            <el-table-column prop="report_type" label="报告类型" width="120">
              <template #default="{ row }">
                <el-tag>{{ getReportTypeText(row.report_type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="生成时间" width="180">
              <template #default="{ row }">
                {{ formatDateTime(row.generated_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button type="primary" size="small" @click="handleDownloadReport(row)">下载</el-button>
                <el-button type="warning" size="small" @click="handlePreviewReportById(row)">预览</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
      <template #footer>
        <el-button @click="reportsDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { View, Document, Download, ArrowDown, Delete } from '@element-plus/icons-vue'
import {
  getExecutionList, getExecutionLogs, getExecutionReports, downloadReport, previewReport, deleteExecution, bulkDeleteExecutions
} from '@/api/automation'

const loading = ref(false)
const logsLoading = ref(false)
const reportsLoading = ref(false)
const logsDialogVisible = ref(false)
const reportsDialogVisible = ref(false)
const executions = ref([])
const logs = ref([])
const reports = ref([])
const currentExecution = ref(null)
const refreshTimer = ref(null)
const selectedExecutions = ref([])

// 从本地存储获取用户信息，判断是否是管理员
const isAdmin = computed(() => {
  // 临时设置为true，用于测试
  return true
  /*
  const userInfo = localStorage.getItem('userInfo')
  if (userInfo) {
    try {
      const user = JSON.parse(userInfo)
      return user.role === 'admin'
    } catch (e) {
      return false
    }
  }
  return false
  */
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const searchForm = reactive({
  task_name: '',
  status: ''
})

const route = useRoute()

// 处理选择变化
const handleSelectionChange = (val) => {
  selectedExecutions.value = val
}

// 处理删除
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除执行历史 ID: ${row.id} 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await deleteExecution(row.id)
    ElMessage.success('执行历史删除成功')
    loadExecutions()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除执行历史失败: ' + (error.message || '未知错误'))
    }
  }
}

// 处理批量删除
const handleBulkDelete = async () => {
  if (selectedExecutions.value.length === 0) {
    ElMessage.warning('请选择要删除的执行历史')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedExecutions.value.length} 条执行历史吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const ids = selectedExecutions.value.map(item => item.id)
    await bulkDeleteExecutions(ids)
    ElMessage.success(`成功删除 ${selectedExecutions.value.length} 条执行历史`)
    selectedExecutions.value = []
    loadExecutions()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除执行历史失败: ' + (error.message || '未知错误'))
    }
  }
}

const loadExecutions = async () => {
  loading.value = true
  try {
    console.log('开始加载执行历史，参数:', {
      page: pagination.page,
      page_size: pagination.size,
      task_name: searchForm.task_name,
      status: searchForm.status
    })
    
    // 检查本地存储的token
    const token = localStorage.getItem('token')
    console.log('本地token:', token ? '存在' : '不存在')
    
    const res = await getExecutionList({
      page: pagination.page,
      page_size: pagination.size,
      task_name: searchForm.task_name,
      status: searchForm.status
    })
    
    console.log('执行历史API响应:', res)
    console.log('响应类型:', typeof res)
    console.log('响应结构:', Object.keys(res))
    
    // 检查响应格式
    if (res.hasOwnProperty('results')) {
      console.log('分页响应格式，results数量:', res.results ? res.results.length : 0)
      // 确保results是一个数组
      executions.value = Array.isArray(res.results) ? res.results : []
      pagination.total = res.count || 0
    } else if (res.hasOwnProperty('data')) {
      console.log('标准API响应格式，data:', res.data)
      // 处理标准API响应格式
      if (res.data.hasOwnProperty('results')) {
        // 标准API格式中的分页响应
        executions.value = Array.isArray(res.data.results) ? res.data.results : []
        pagination.total = res.data.count || 0
      } else {
        // 标准API格式中的普通响应
        executions.value = Array.isArray(res.data) ? res.data : []
        pagination.total = executions.value.length
      }
    } else {
      console.log('未知响应格式')
      executions.value = []
    }
    
    console.log('设置executions:', executions.value.length, '条记录')
    console.log('设置pagination.total:', pagination.total)
    
  } catch (error) {
    console.error('加载执行历史失败:', error)
    console.error('错误详情:', error.message, error.response)
    ElMessage.error('加载执行历史失败: ' + (error.message || '未知错误'))
    // 出错时设置为空数组，避免表格渲染错误
    executions.value = []
  } finally {
    loading.value = false
  }
}

// 定时刷新执行状态 - 改为30秒
onMounted(() => {
  // 初始加载执行历史
  loadExecutions()
  
  // 启动定时刷新
  refreshTimer.value = setInterval(() => {
    // 只在页面活跃时刷新
    if (document.visibilityState === 'visible') {
      loadExecutions()
    }
  }, 30000)  // 30秒刷新一次
})

onUnmounted(() => {
  // 清理定时器
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }
})

// 监听路由变化，当进入执行历史页面时刷新数据
watch(() => route.path, (newPath, oldPath) => {
  if (newPath.includes('/automation/executions')) {
    console.log('路由变化到执行历史页面，刷新数据')
    loadExecutions()
  }
}, { immediate: true })

const handleViewLogs = async (row) => {
  currentExecution.value = row
  logsDialogVisible.value = true
  logsLoading.value = true
  try {
    const res = await getExecutionLogs(row.id)
    // 确保对话框仍然可见，避免更新已销毁的DOM
    if (logsDialogVisible.value) {
      // 确保返回的是一个数组（处理后端返回的标准格式）
      logs.value = Array.isArray(res.data) ? res.data : Array.isArray(res) ? res : []
    }
  } catch (error) {
    // 确保对话框仍然可见，避免更新已销毁的DOM
    if (logsDialogVisible.value) {
      ElMessage.error('加载日志失败')
      // 出错时设置为空数组，避免表格渲染错误
      logs.value = []
    }
  } finally {
    // 确保对话框仍然可见，避免更新已销毁的DOM
    if (logsDialogVisible.value) {
      logsLoading.value = false
    }
  }
}

const handleViewReports = async (row) => {
  try {
    // 找到该执行的Allure报告
    const res = await getExecutionReports(row.id)
    // 处理后端返回的标准格式
    const reportsList = Array.isArray(res.data) ? res.data : Array.isArray(res) ? res : []
    const allureReport = reportsList.find(report => report.report_type === 'allure')
    if (allureReport) {
      // 直接构建报告的HTML页面URL
      const reportUrl = `/media/reports/allure/${row.id}/index.html`
      // 在新窗口打开报告
      window.open(reportUrl, '_blank')
    } else {
      ElMessage.warning('该执行暂无Allure报告')
    }
  } catch (error) {
    console.error('查看报告失败:', error)
    ElMessage.error('查看报告失败')
  }
}

const handleDownloadReport = async (row) => {
  try {
    const response = await downloadReport(row.id)
    // 处理二进制响应
    if (response instanceof Blob) {
      // 创建下载链接
      const url = window.URL.createObjectURL(response)
      const link = document.createElement('a')
      link.href = url
      link.download = `report_${row.id}.zip`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      ElMessage.success('报告下载已开始')
    } else {
      ElMessage.success('报告下载已开始')
    }
  } catch (error) {
    if (error.response && error.response.data && error.response.data.message === '报告文件不存在') {
      ElMessage.warning('报告文件不存在，可能是报告生成失败或已被删除')
    } else {
      ElMessage.error('下载报告失败: ' + (error.message || '未知错误'))
    }
  }
}

const handlePreviewReport = async (row) => {
  try {
    // 找到该执行的Allure报告
    const res = await getExecutionReports(row.id)
    const allureReport = res.find(report => report.report_type === 'allure')
    if (allureReport) {
      // 打开报告预览
      const previewRes = await previewReport(allureReport.id)
      if (previewRes.report_url) {
        // 在新窗口打开报告
        window.open(previewRes.report_url, '_blank')
      } else {
        ElMessage.info('报告预览功能开发中')
      }
    } else {
      ElMessage.warning('该执行暂无Allure报告')
    }
  } catch (error) {
    ElMessage.error('预览报告失败')
  }
}

const handlePreviewReportById = async (row) => {
  // 直接显示开发中提示，不再尝试打开报告
  ElMessage.info('报告预览功能开发中')
}

const handleDownloadReportFromRow = async (row) => {
  try {
    // 找到该执行的Allure报告
    const res = await getExecutionReports(row.id)
    // 处理后端返回的标准格式
    const reportsList = Array.isArray(res.data) ? res.data : Array.isArray(res) ? res : []
    console.log('报告列表:', reportsList)
    const allureReport = reportsList.find(report => report.report_type === 'allure')
    if (allureReport) {
      console.log('找到Allure报告:', allureReport)
      // 下载报告
      const response = await downloadReport(allureReport.id)
      // 处理二进制响应
      if (response instanceof Blob) {
        // 创建下载链接
        const url = window.URL.createObjectURL(response)
        const link = document.createElement('a')
        link.href = url
        link.download = `report_${allureReport.id}.zip`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        ElMessage.success('报告下载已开始')
      } else {
        ElMessage.success('报告下载已开始')
      }
    } else {
      ElMessage.warning('该执行暂无Allure报告')
    }
  } catch (error) {
    console.error('下载报告失败:', error)
    if (error.response && error.response.data && error.response.data.message === '报告文件不存在') {
      ElMessage.warning('报告文件不存在，可能是报告生成失败或已被删除')
    } else {
      ElMessage.error('下载报告失败: ' + (error.message || '未知错误'))
    }
  }
}

const resetSearch = () => {
  searchForm.task_name = ''
  searchForm.status = ''
  loadExecutions()
}

const getStatusType = (status) => {
  const typeMap = {
    pending: 'info',
    running: 'warning',
    success: 'success',
    failed: 'danger',
    error: 'danger',
    stopped: 'info'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    pending: '待执行',
    running: '执行中',
    success: '执行成功',
    failed: '执行失败',
    error: '执行异常',
    stopped: '已停止'
  }
  return textMap[status] || status
}

const getReportTypeText = (type) => {
  const textMap = {
    allure: 'Allure报告',
    junit: 'JUnit报告',
    html: 'HTML报告'
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
</script>

<style scoped>
.automation-executions-page {
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

.logs-container {
  max-height: 400px;
  overflow-y: auto;
}

.logs-content {
  font-family: monospace;
  font-size: 14px;
}

.log-item {
  margin-bottom: 8px;
  padding: 4px 8px;
  border-left: 4px solid transparent;
}

.log-info {
  border-left-color: #409EFF;
  background-color: #ecf5ff;
}

.log-error {
  border-left-color: #F56C6C;
  background-color: #fef0f0;
}

.log-warning {
  border-left-color: #E6A23C;
  background-color: #fdf6ec;
}

.log-time {
  color: #909399;
  margin-right: 10px;
}

.log-level {
  font-weight: bold;
  margin-right: 10px;
}

.log-message {
  word-break: break-all;
}

.empty-logs {
  text-align: center;
  color: #909399;
  padding: 40px 0;
}

.reports-container {
  max-height: 400px;
  overflow-y: auto;
}

.empty-reports {
  text-align: center;
  color: #909399;
  padding: 40px 0;
}

.task-name-cell {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}
</style>