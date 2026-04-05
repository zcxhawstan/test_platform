<template>
  <div class="automation-tasks-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>自动化任务管理</span>
          <div class="search-box">
            <el-input v-model="searchForm.name" placeholder="请输入任务名称" style="width: 200px; margin-right: 10px" />
            <el-select v-model="searchForm.status" placeholder="选择状态" style="width: 120px; margin-right: 10px">
              <el-option label="全部" value="" />
              <el-option label="待执行" value="pending" />
              <el-option label="执行中" value="running" />
              <el-option label="执行成功" value="success" />
              <el-option label="执行失败" value="failed" />
              <el-option label="执行异常" value="error" />
            </el-select>
            <el-button type="primary" @click="loadTasks">查询</el-button>
            <el-button @click="resetSearch">重置</el-button>
          </div>
          <el-button type="primary" @click="showAddDialog">新增任务</el-button>
        </div>
      </template>
      
      <el-table :data="tasks" v-loading="loading" border>
        <el-table-column prop="id" label="任务ID" width="80" />
        <el-table-column prop="name" label="任务名称" />
        <el-table-column prop="script_source" label="脚本来源" width="120">
          <template #default="{ row }">
            <el-tag :type="getScriptSourceType(row.script_source)">{{ getScriptSourceText(row.script_source) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="environment" label="执行环境" width="150">
          <template #default="{ row }">
            <span v-if="row.environment">
              {{ row.environment.name || `环境ID: ${row.environment.id}` }}
            </span>
            <span v-else class="environment-not-set">
              未设置
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="Docker容器" width="180">
          <template #default="{ row }">
            {{ getDockerContainerName(row) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-dropdown>
              <el-button type="primary" size="small">
                操作 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="handleExecute(row)" :disabled="row.status === 'running'">
                    <el-icon><VideoPlay /></el-icon> 执行
                  </el-dropdown-item>
                  <el-dropdown-item 
                    v-if="row.status === 'running'" 
                    @click="handleStop(row)"
                    :loading="stoppingTaskId === row.id"
                  >
                    <el-icon><CircleClose /></el-icon> 停止
                  </el-dropdown-item>
                  <el-dropdown-item @click="handleEdit(row)">
                    <el-icon><Edit /></el-icon> 编辑
                  </el-dropdown-item>
                  <el-dropdown-item @click="handleDelete(row)" divided>
                    <el-icon><Delete /></el-icon> 删除
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
        @size-change="loadTasks"
        @current-change="loadTasks"
        style="margin-top: 20px; justify-content: center"
      />
    </el-card>
    
    <!-- 新增/编辑任务对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入任务名称" />
        </el-form-item>
        
        <el-form-item label="任务描述" prop="description">
          <el-input v-model="form.description" type="textarea" placeholder="请输入任务描述" />
        </el-form-item>
        
        <el-form-item label="Git仓库类型" prop="git_type">
          <el-select v-model="form.git_type" placeholder="请选择Git仓库类型">
            <el-option label="HTTPS" value="https" />
            <el-option label="SSH" value="ssh" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="Git仓库地址" prop="git_repo">
          <el-input v-model="form.git_repo" placeholder="请输入Git仓库地址" />
        </el-form-item>
        
        <el-form-item label="Git分支" prop="git_branch">
          <template #label>
            <div style="display: flex; align-items: center;">
              Git分支
              <el-tooltip
                content="代码将自动拉取到执行机的以下路径：
/opt/automation/repos/&lt;仓库名称&gt;"
                placement="top"
                :effect="'light'"
                :show-after="300"
              >
                <el-icon class="is-warning" style="margin-left: 4px; color: #E6A23C;">
                  <WarningFilled />
                </el-icon>
              </el-tooltip>
            </div>
          </template>
          <el-input v-model="form.git_branch" placeholder="请输入Git分支" />
        </el-form-item>
        
        <el-form-item label="脚本路径" prop="script_path">
          <template #label>
            <div style="display: flex; align-items: center;">
              脚本路径
              <el-tooltip
                content="相对于Git仓库根目录的脚本路径，例如：test_cases/test_api.py"
                placement="top"
                :effect="'light'"
                :show-after="300"
              >
                <el-icon class="is-warning" style="margin-left: 4px; color: #E6A23C;">
                  <WarningFilled />
                </el-icon>
              </el-tooltip>
            </div>
          </template>
          <el-input v-model="form.script_path" placeholder="请输入相对于仓库根目录的脚本路径" />
        </el-form-item>
        
        <el-form-item label="执行环境" prop="environment" required>
          <el-select v-model="form.environment" placeholder="请选择执行环境">
            <el-option v-for="env in environments" :key="env.id" :label="env.name" :value="env.id" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="执行方式" prop="execution_type">
          <el-select v-model="form.execution_type">
            <el-option label="手动执行" value="manual" />
            <el-option label="定时执行" value="scheduled" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="Cron表达式" prop="cron_expression" v-if="form.execution_type === 'scheduled'">
          <el-input v-model="form.cron_expression" placeholder="请输入Cron表达式" />
        </el-form-item>
        
        <el-form-item label="失败重跑次数" prop="retry_count">
          <el-input-number v-model="form.retry_count" :min="0" :max="10" />
        </el-form-item>
        
        <el-form-item label="超时时间(秒)" prop="timeout">
          <el-input-number v-model="form.timeout" :min="60" :max="7200" />
        </el-form-item>
        
        <el-form-item label="启用Allure报告" prop="enable_allure">
          <el-switch v-model="form.enable_allure" />
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
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox, ElTooltip, ElIcon } from 'element-plus'
import { WarningFilled, ArrowDown, VideoPlay, CircleClose, Edit, Delete } from '@element-plus/icons-vue'
import {
  getTaskList, createTask, updateTask, deleteTask, executeTask, stopTask,
  getEnvironmentList
} from '@/api/automation'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const submitLoading = ref(false)
const stoppingTaskId = ref(null)  // 正在停止的任务ID
const refreshTimer = ref(null)    // 定时刷新器
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()
const tasks = ref([])
const environments = ref([])

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const searchForm = reactive({
  name: '',
  status: ''
})

const form = reactive({
  name: '',
  description: '',
  git_type: 'https',
  git_repo: '',
  git_branch: 'main',
  script_path: '',
  environment: null,
  execution_type: 'manual',
  cron_expression: '',
  retry_count: 0,
  timeout: 3600,
  enable_allure: true
})

const rules = {
  name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  script_path: [{ required: true, message: '请输入脚本路径', trigger: 'blur' }],
  environment: [{ required: true, message: '请选择执行环境', trigger: 'change' }],
  git_type: [{ required: true, message: '请选择Git仓库类型', trigger: 'change' }],
  git_repo: [
    { required: true, message: '请输入Git仓库地址', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (!value) {
          callback(new Error('请输入Git仓库地址'))
          return
        }
        if (form.git_type === 'https') {
          // HTTPS格式校验
          const httpsRegex = /^https:\/\/[\w\-]+(\.[\w\-]+)+([\w\-\.,@?^=%&:/~\+#]*[\w\-\@?^=%&/~\+#])?$/
          if (!httpsRegex.test(value)) {
            callback(new Error('请输入有效的HTTPS格式Git仓库地址'))
            return
          }
        } else if (form.git_type === 'ssh') {
          // SSH格式校验
          const sshRegex = /^git@[\w\-]+(\.[\w\-]+)+:[\w\-\.]+\/[\w\-\.]+(\.git)?$/
          if (!sshRegex.test(value)) {
            callback(new Error('请输入有效的SSH格式Git仓库地址'))
            return
          }
        }
        callback()
      },
      trigger: 'blur'
    }
  ],
  git_branch: [{ required: true, message: '请输入Git分支', trigger: 'blur' }]
}

const dialogTitle = computed(() => isEdit.value ? '编辑任务' : '新增任务')

const loadTasks = async () => {
  loading.value = true
  try {
    const res = await getTaskList({
      page: pagination.page,
      page_size: pagination.size,
      name: searchForm.name,
      status: searchForm.status
    })
    tasks.value = res.results
    pagination.total = res.count
  } catch (error) {
    ElMessage.error('加载任务列表失败')
  } finally {
    loading.value = false
  }
}

const loadEnvironments = async () => {
  try {
    const res = await getEnvironmentList()
    environments.value = res.results
  } catch (error) {
    ElMessage.error('加载环境列表失败')
  }
}

const showAddDialog = () => {
  isEdit.value = false
  Object.assign(form, {
    id: null,
    name: '',
    description: '',
    git_type: 'https',
    git_repo: '',
    git_branch: 'main',
    script_path: '',
    environment: null,
    execution_type: 'manual',
    cron_expression: '',
    retry_count: 0,
    timeout: 1800,
    enable_allure: true
  })
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  
  // 处理git_repo字段，确保是字符串
  let gitRepo = row.git_repo || ''
  if (Array.isArray(gitRepo)) {
    console.warn('编辑时发现git_repo是数组:', gitRepo)
    gitRepo = gitRepo[0] || ''
  }
  
  // 自动检测Git仓库类型
  let gitType = 'https'
  if (gitRepo && gitRepo.startsWith('git@')) {
    gitType = 'ssh'
  }
  
  Object.assign(form, {
    id: row.id,
    name: row.name,
    description: row.description,
    git_type: gitType,
    git_repo: gitRepo,
    git_branch: row.git_branch || 'main',
    script_path: row.script_path,
    environment: row.environment ? row.environment.id : null,
    execution_type: row.execution_type,
    cron_expression: row.cron_expression || '',
    retry_count: row.retry_count,
    timeout: row.timeout,
    enable_allure: row.enable_allure
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitLoading.value = true
    
    // 数据清理：确保git_repo是字符串而不是数组
    const submitData = { ...form }
    
    // 如果git_repo是数组，取第一个元素
    if (Array.isArray(submitData.git_repo)) {
      console.warn('git_repo是数组，自动转换为字符串:', submitData.git_repo)
      submitData.git_repo = submitData.git_repo[0] || ''
    }
    
    // 确保git_repo是字符串
    if (typeof submitData.git_repo !== 'string') {
      submitData.git_repo = String(submitData.git_repo || '')
    }
    
    // 调试日志
    console.log('提交数据:', submitData)
    
    if (isEdit.value) {
      await updateTask(form.id, submitData)
      ElMessage.success('任务更新成功')
    } else {
      await createTask(submitData)
      ElMessage.success('任务创建成功')
    }
    dialogVisible.value = false
    loadTasks()
  } catch (error) {
    console.error('提交错误:', error)
    // 表单验证失败时，Element Plus会自动显示错误信息，不需要额外处理
    if (error.message !== '表单验证失败') {
      ElMessage.error('操作失败')
    }
  } finally {
    submitLoading.value = false
  }
}

const handleExecute = async (row) => {
  try {
    await executeTask(row.id)
    ElMessage.success('任务执行已启动')
    // 刷新任务列表
    loadTasks()
    // 跳转到执行历史页面
    router.push('/automation/executions')
  } catch (error) {
    console.error('执行任务失败:', error)
    ElMessage.error('启动任务失败: ' + (error.message || '未知错误'))
  }
}

const handleStop = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要停止任务 "${row.name}" 吗？`,
      '确认停止',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    stoppingTaskId.value = row.id
    const res = await stopTask(row.id)
    ElMessage.success(res.message || '停止请求已发送')
    // 刷新任务列表
    loadTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '停止任务失败')
    }
  } finally {
    stoppingTaskId.value = null
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除任务 ${row.name} 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteTask(row.id)
    ElMessage.success('任务删除成功')
    loadTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const resetSearch = () => {
  searchForm.name = ''
  searchForm.status = ''
  loadTasks()
}

const getScriptSourceType = (source) => {
  // 根据用户要求，脚本来源固定为"Git仓库"，使用warning类型
  return 'warning'
}

const getScriptSourceText = (source) => {
  // 根据用户要求，直接显示"Git仓库"
  return 'Git仓库'
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

const getDockerContainerName = (row) => {
  // 如果没有关联环境，无法生成容器名称
  if (!row.environment) {
    return '未设置环境'
  }
  
  // 根据用户要求，显示实际任务执行后的容器名称
  // 容器名称规则：automation-{environment.id}（与后端DockerService保持一致）
  const containerName = `automation-${row.environment.id}`
  
  // 根据任务状态显示不同信息
  if (row.status === 'pending') {
    return `未执行 (将使用: ${containerName})`
  } else if (row.status === 'running') {
    return `执行中 (${containerName})`
  } else if (row.status === 'success' || row.status === 'failed' || row.status === 'error' || row.status === 'stopped') {
    // 任务已执行过，显示实际容器名称
    return containerName
  }
  
  return containerName
}

onMounted(() => {
  // 初始加载任务列表
  loadTasks()
  loadEnvironments()
  
  // 启动定时刷新（30秒一次）
  refreshTimer.value = setInterval(() => {
    // 只在页面活跃时刷新
    if (document.visibilityState === 'visible') {
      loadTasks()
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

// 监听路由变化，当进入任务页面时刷新数据
watch(() => route.path, (newPath, oldPath) => {
  if (newPath.includes('/automation/tasks')) {
    console.log('路由变化到任务页面，刷新数据')
    loadTasks()
  }
}, { immediate: true })
</script>

<style scoped>
.automation-tasks-page {
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

.environment-not-set {
  color: #999;
  font-style: italic;
}
</style>
