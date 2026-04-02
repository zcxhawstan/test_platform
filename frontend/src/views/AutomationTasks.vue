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
            {{ row.environment ? row.environment.name : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleExecute(row)">执行</el-button>
            <el-button type="warning" size="small" @click="handleEdit(row)">编辑</el-button>
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
        
        <el-form-item label="脚本来源" prop="script_source">
          <el-select v-model="form.script_source">
            <el-option label="平台内置脚本" value="builtin" />
            <el-option label="上传脚本" value="upload" />
            <el-option label="Git仓库" value="git" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="脚本路径" prop="script_path">
          <el-input v-model="form.script_path" placeholder="请输入脚本路径" />
        </el-form-item>
        
        <el-form-item label="Git仓库地址" prop="git_repo" v-if="form.script_source === 'git'">
          <el-input v-model="form.git_repo" placeholder="请输入Git仓库地址" />
        </el-form-item>
        
        <el-form-item label="Git分支" prop="git_branch" v-if="form.script_source === 'git'">
          <el-input v-model="form.git_branch" placeholder="请输入Git分支" />
        </el-form-item>
        
        <el-form-item label="执行命令" prop="execution_command">
          <el-input v-model="form.execution_command" placeholder="请输入执行命令" />
        </el-form-item>
        
        <el-form-item label="执行环境" prop="environment">
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
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getTaskList, createTask, updateTask, deleteTask, executeTask,
  getEnvironmentList
} from '@/api/automation'

const loading = ref(false)
const submitLoading = ref(false)
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
  id: null,
  name: '',
  description: '',
  script_source: 'builtin',
  script_path: '',
  git_repo: '',
  git_branch: 'main',
  execution_command: 'pytest {script} --alluredir=./result',
  environment: null,
  execution_type: 'manual',
  cron_expression: '',
  retry_count: 0,
  timeout: 1800,
  enable_allure: true
})

const rules = {
  name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  script_path: [{ required: true, message: '请输入脚本路径', trigger: 'blur' }],
  execution_command: [{ required: true, message: '请输入执行命令', trigger: 'blur' }]
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
    script_source: 'builtin',
    script_path: '',
    git_repo: '',
    git_branch: 'main',
    execution_command: 'pytest {script} --alluredir=./result',
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
  Object.assign(form, {
    id: row.id,
    name: row.name,
    description: row.description,
    script_source: row.script_source,
    script_path: row.script_path,
    git_repo: row.git_repo || '',
    git_branch: row.git_branch || 'main',
    execution_command: row.execution_command,
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
  await formRef.value.validate()
  submitLoading.value = true
  try {
    if (isEdit.value) {
      await updateTask(form.id, form)
      ElMessage.success('任务更新成功')
    } else {
      await createTask(form)
      ElMessage.success('任务创建成功')
    }
    dialogVisible.value = false
    loadTasks()
  } catch (error) {
    ElMessage.error('操作失败')
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
  } catch (error) {
    ElMessage.error('启动任务失败')
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
  const typeMap = {
    builtin: 'info',
    upload: 'primary',
    git: 'warning'
  }
  return typeMap[source] || 'info'
}

const getScriptSourceText = (source) => {
  const textMap = {
    builtin: '平台内置',
    upload: '上传',
    git: 'Git仓库'
  }
  return textMap[source] || source
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

onMounted(() => {
  loadTasks()
  loadEnvironments()
})
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
</style>
