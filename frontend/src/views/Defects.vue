<template>
  <div class="defects-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>缺陷管理</span>
          <el-button type="primary" @click="showAddDialog">新增缺陷</el-button>
        </div>
      </template>
      
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="请选择" clearable style="width: 120px;">
            <el-option label="新建" value="new" />
            <el-option label="已分配" value="assigned" />
            <el-option label="处理中" value="in_progress" />
            <el-option label="已解决" value="resolved" />
            <el-option label="已验证" value="verified" />
            <el-option label="已关闭" value="closed" />
            <el-option label="重新打开" value="reopened" />
          </el-select>
        </el-form-item>
        <el-form-item label="严重程度">
          <el-select v-model="filters.severity" placeholder="请选择" clearable style="width: 120px;">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
            <el-option label="紧急" value="critical" />
          </el-select>
        </el-form-item>
        <el-form-item label="模块">
          <el-input v-model="filters.module" placeholder="请输入模块" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadDefects">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
      
      <el-table :data="defects" v-loading="loading" border>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="缺陷标题" width="200" />
        <el-table-column prop="severity" label="严重程度" width="100">
          <template #default="{ row }">
            <el-tag :type="getSeverityType(row.severity)">{{ getSeverityText(row.severity) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="100">
          <template #default="{ row }">
            <el-tag :type="getPriorityType(row.priority)">{{ getPriorityText(row.priority) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="module" label="模块" width="120" />
        <el-table-column prop="assigned_to_name" label="分配给" width="120" />
        <el-table-column prop="reported_by_name" label="报告人" width="120" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="250">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleView(row)">详情</el-button>
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
        @size-change="loadDefects"
        @current-change="loadDefects"
        style="margin-top: 20px; justify-content: center"
      />
    </el-card>
    
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="800px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="缺陷标题" prop="title">
              <el-input v-model="form.title" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="所属模块" prop="module">
              <el-input v-model="form.module" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="严重程度" prop="severity">
              <el-select v-model="form.severity">
                <el-option label="低" value="low" />
                <el-option label="中" value="medium" />
                <el-option label="高" value="high" />
                <el-option label="紧急" value="critical" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="优先级" prop="priority">
              <el-select v-model="form.priority">
                <el-option label="低" value="low" />
                <el-option label="中" value="medium" />
                <el-option label="高" value="high" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="状态" prop="status">
              <el-select v-model="form.status">
                <el-option label="新建" value="new" />
                <el-option label="已分配" value="assigned" />
                <el-option label="处理中" value="in_progress" />
                <el-option label="已解决" value="resolved" />
                <el-option label="已验证" value="verified" />
                <el-option label="已关闭" value="closed" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="缺陷描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        
        <el-form-item label="复现步骤" prop="steps_to_reproduce">
          <el-input v-model="form.steps_to_reproduce" type="textarea" :rows="4" />
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="预期结果" prop="expected_result">
              <el-input v-model="form.expected_result" type="textarea" :rows="2" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="实际结果" prop="actual_result">
              <el-input v-model="form.actual_result" type="textarea" :rows="2" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="detailVisible" title="缺陷详情" width="1000px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="缺陷标题">{{ currentDefect.title }}</el-descriptions-item>
        <el-descriptions-item label="所属模块">{{ currentDefect.module }}</el-descriptions-item>
        <el-descriptions-item label="严重程度">
          <el-tag :type="getSeverityType(currentDefect.severity)">{{ getSeverityText(currentDefect.severity) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="优先级">
          <el-tag :type="getPriorityType(currentDefect.priority)">{{ getPriorityText(currentDefect.priority) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentDefect.status)">{{ getStatusText(currentDefect.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="分配给">{{ currentDefect.assigned_to_name || '未分配' }}</el-descriptions-item>
        <el-descriptions-item label="报告人">{{ currentDefect.reported_by_name }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ currentDefect.created_at }}</el-descriptions-item>
        <el-descriptions-item label="缺陷描述" :span="2">{{ currentDefect.description }}</el-descriptions-item>
        <el-descriptions-item label="复现步骤" :span="2" style="white-space: pre-wrap">{{ currentDefect.steps_to_reproduce }}</el-descriptions-item>
        <el-descriptions-item label="预期结果" :span="2">{{ currentDefect.expected_result }}</el-descriptions-item>
        <el-descriptions-item label="实际结果" :span="2">{{ currentDefect.actual_result }}</el-descriptions-item>
      </el-descriptions>
      
      <div style="margin-top: 20px">
        <el-button type="primary" @click="showUpdateStatusDialog">更新状态</el-button>
        <el-button @click="showAddCommentDialog">添加评论</el-button>
      </div>
      
      <el-divider>评论列表</el-divider>
      
      <div v-if="currentDefect.comments && currentDefect.comments.length > 0">
        <div v-for="comment in currentDefect.comments" :key="comment.id" class="comment-item">
          <div class="comment-header">
            <span class="comment-user">{{ comment.created_by_name }}</span>
            <span class="comment-time">{{ comment.created_at }}</span>
          </div>
          <div class="comment-content">{{ comment.content }}</div>
        </div>
      </div>
      <div v-else class="no-comments">暂无评论</div>
    </el-dialog>
    
    <el-dialog v-model="statusVisible" title="更新状态" width="500px">
      <el-form ref="statusFormRef" :model="statusForm" :rules="statusRules" label-width="100px">
        <el-form-item label="状态" prop="status">
          <el-select v-model="statusForm.status">
            <el-option label="新建" value="new" />
            <el-option label="已分配" value="assigned" />
            <el-option label="处理中" value="in_progress" />
            <el-option label="已解决" value="resolved" />
            <el-option label="已验证" value="verified" />
            <el-option label="已关闭" value="closed" />
            <el-option label="重新打开" value="reopened" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="评论">
          <el-input v-model="statusForm.comment" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="statusVisible = false">取消</el-button>
        <el-button type="primary" :loading="statusLoading" @click="handleUpdateStatus">确定</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="commentVisible" title="添加评论" width="500px">
      <el-form ref="commentFormRef" :model="commentForm" :rules="commentRules" label-width="100px">
        <el-form-item label="评论内容" prop="content">
          <el-input v-model="commentForm.content" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="commentVisible = false">取消</el-button>
        <el-button type="primary" :loading="commentLoading" @click="handleAddComment">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getDefectList, createDefect, updateDefect, deleteDefect, getDefectDetail, updateDefectStatus, addComment } from '@/api/defect'

const loading = ref(false)
const submitLoading = ref(false)
const statusLoading = ref(false)
const commentLoading = ref(false)
const dialogVisible = ref(false)
const detailVisible = ref(false)
const statusVisible = ref(false)
const commentVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()
const statusFormRef = ref()
const commentFormRef = ref()
const defects = ref([])
const currentDefect = ref({})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const filters = reactive({
  status: '',
  severity: '',
  module: ''
})

const form = reactive({
  id: null,
  title: '',
  description: '',
  severity: 'medium',
  priority: 'medium',
  status: 'new',
  module: '',
  steps_to_reproduce: '',
  expected_result: '',
  actual_result: ''
})

const statusForm = reactive({
  status: '',
  comment: ''
})

const commentForm = reactive({
  content: ''
})

const rules = {
  title: [{ required: true, message: '请输入缺陷标题', trigger: 'blur' }],
  module: [{ required: true, message: '请输入所属模块', trigger: 'blur' }],
  description: [{ required: true, message: '请输入缺陷描述', trigger: 'blur' }],
  steps_to_reproduce: [{ required: true, message: '请输入复现步骤', trigger: 'blur' }],
  expected_result: [{ required: true, message: '请输入预期结果', trigger: 'blur' }],
  actual_result: [{ required: true, message: '请输入实际结果', trigger: 'blur' }]
}

const statusRules = {
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
}

const commentRules = {
  content: [{ required: true, message: '请输入评论内容', trigger: 'blur' }]
}

const dialogTitle = computed(() => isEdit.value ? '编辑缺陷' : '新增缺陷')

const loadDefects = async () => {
  loading.value = true
  try {
    const res = await getDefectList({
      page: pagination.page,
      page_size: pagination.size,
      ...filters
    })
    defects.value = res.data.results
    pagination.total = res.data.count
  } catch (error) {
    ElMessage.error('加载缺陷列表失败')
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  Object.assign(filters, {
    status: '',
    severity: '',
    module: ''
  })
  loadDefects()
}

const showAddDialog = () => {
  isEdit.value = false
  Object.assign(form, {
    id: null,
    title: '',
    description: '',
    severity: 'medium',
    priority: 'medium',
    status: 'new',
    module: '',
    steps_to_reproduce: '',
    expected_result: '',
    actual_result: ''
  })
  dialogVisible.value = true
}

const handleView = async (row) => {
  try {
    const res = await getDefectDetail(row.id)
    currentDefect.value = res.data
    detailVisible.value = true
  } catch (error) {
    ElMessage.error('加载详情失败')
  }
}

const handleEdit = (row) => {
  isEdit.value = true
  Object.assign(form, row)
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value.validate()
  submitLoading.value = true
  try {
    if (isEdit.value) {
      await updateDefect(form.id, form)
      ElMessage.success('更新成功')
    } else {
      await createDefect(form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadDefects()
  } catch (error) {
    ElMessage.error('操作失败')
  } finally {
    submitLoading.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除缺陷 ${row.title} 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteDefect(row.id)
    ElMessage.success('删除成功')
    loadDefects()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const showUpdateStatusDialog = () => {
  Object.assign(statusForm, {
    status: currentDefect.value.status,
    comment: ''
  })
  statusVisible.value = true
}

const handleUpdateStatus = async () => {
  await statusFormRef.value.validate()
  statusLoading.value = true
  try {
    await updateDefectStatus(currentDefect.value.id, statusForm)
    ElMessage.success('状态更新成功')
    statusVisible.value = false
    handleView(currentDefect.value)
    loadDefects()
  } catch (error) {
    ElMessage.error('状态更新失败')
  } finally {
    statusLoading.value = false
  }
}

const showAddCommentDialog = () => {
  Object.assign(commentForm, {
    content: ''
  })
  commentVisible.value = true
}

const handleAddComment = async () => {
  await commentFormRef.value.validate()
  commentLoading.value = true
  try {
    await addComment(currentDefect.value.id, commentForm)
    ElMessage.success('评论添加成功')
    commentVisible.value = false
    handleView(currentDefect.value)
  } catch (error) {
    ElMessage.error('评论添加失败')
  } finally {
    commentLoading.value = false
  }
}

const getSeverityType = (severity) => {
  const typeMap = { low: 'info', medium: 'warning', high: 'danger', critical: 'danger' }
  return typeMap[severity] || 'info'
}

const getSeverityText = (severity) => {
  const textMap = { low: '低', medium: '中', high: '高', critical: '紧急' }
  return textMap[severity] || severity
}

const getPriorityType = (priority) => {
  const typeMap = { low: 'info', medium: 'warning', high: 'danger' }
  return typeMap[priority] || 'info'
}

const getPriorityText = (priority) => {
  const textMap = { low: '低', medium: '中', high: '高' }
  return textMap[priority] || priority
}

const getStatusType = (status) => {
  const typeMap = { new: 'info', assigned: 'warning', in_progress: 'warning', resolved: 'success', verified: 'success', closed: 'info', reopened: 'danger' }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = { new: '新建', assigned: '已分配', in_progress: '处理中', resolved: '已解决', verified: '已验证', closed: '已关闭', reopened: '重新打开' }
  return textMap[status] || status
}

onMounted(() => {
  loadDefects()
})
</script>

<style scoped>
.defects-page {
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

.comment-item {
  padding: 10px;
  border-bottom: 1px solid #eee;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
}

.comment-user {
  font-weight: bold;
}

.comment-time {
  color: #999;
  font-size: 12px;
}

.comment-content {
  color: #333;
}

.no-comments {
  text-align: center;
  color: #999;
  padding: 20px;
}
</style>
