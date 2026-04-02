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
          </div>
        </div>
      </template>
      
      <el-table :data="executions" v-loading="loading" border>
        <el-table-column prop="id" label="执行ID" width="80" />
        <el-table-column prop="task" label="任务名称">
          <template #default="{ row }">
            {{ row.task ? row.task.name : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="environment" label="执行环境" width="150">
          <template #default="{ row }">
            {{ row.environment ? row.environment.name : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="executor" label="执行人" width="120">
          <template #default="{ row }">
            {{ row.executor ? row.executor.username : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间" width="180" />
        <el-table-column prop="duration" label="执行时长(秒)" width="120" />
        <el-table-column label="操作" width="250">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleViewLogs(row)">查看日志</el-button>
            <el-button type="warning" size="small" @click="handleViewReports(row)">查看报告</el-button>
            <el-button size="small" @click="handlePreviewReport(row)">预览报告</el-button>
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
    <el-dialog v-model="logsDialogVisible" title="执行日志" width="800px" height="600px">
      <div class="logs-container" v-loading="logsLoading">
        <div v-if="logs.length === 0" class="empty-logs">暂无日志</div>
        <div v-else class="logs-content">
          <div v-for="log in logs" :key="log.id" :class="['log-item', `log-${log.level.toLowerCase()}`]">
            <span class="log-time">{{ log.timestamp }}</span>
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
    <el-dialog v-model="reportsDialogVisible" title="测试报告" width="800px">
      <div class="reports-container" v-loading="reportsLoading">
        <div v-if="reports.length === 0" class="empty-reports">暂无报告</div>
        <div v-else class="reports-content">
          <el-table :data="reports" border>
            <el-table-column prop="id" label="报告ID" width="80" />
            <el-table-column prop="report_type" label="报告类型" width="120">
              <template #default="{ row }">
                <el-tag>{{ getReportTypeText(row.report_type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="generated_at" label="生成时间" width="180" />
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button type="primary" size="small" @click="handleDownloadReport(row)">下载</el-button>
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getExecutionList, getExecutionLogs, getExecutionReports, downloadReport, previewReport
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

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const searchForm = reactive({
  task_name: '',
  status: ''
})

const loadExecutions = async () => {
  loading.value = true
  try {
    const res = await getExecutionList({
      page: pagination.page,
      page_size: pagination.size,
      task_name: searchForm.task_name,
      status: searchForm.status
    })
    executions.value = res.results
    pagination.total = res.count
  } catch (error) {
    ElMessage.error('加载执行历史失败')
  } finally {
    loading.value = false
  }
}

const handleViewLogs = async (row) => {
  currentExecution.value = row
  logsDialogVisible.value = true
  logsLoading.value = true
  try {
    const res = await getExecutionLogs(row.id)
    logs.value = res
  } catch (error) {
    ElMessage.error('加载日志失败')
  } finally {
    logsLoading.value = false
  }
}

const handleViewReports = async (row) => {
  currentExecution.value = row
  reportsDialogVisible.value = true
  reportsLoading.value = true
  try {
    const res = await getExecutionReports(row.id)
    reports.value = res
  } catch (error) {
    ElMessage.error('加载报告失败')
  } finally {
    reportsLoading.value = false
  }
}

const handleDownloadReport = async (row) => {
  try {
    await downloadReport(row.id)
    ElMessage.success('报告下载已开始')
  } catch (error) {
    ElMessage.error('下载报告失败')
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

onMounted(() => {
  loadExecutions()
})
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
</style>
