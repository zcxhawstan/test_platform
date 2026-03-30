<template>
  <div class="testcases-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>测试用例管理</span>
          <div>
            <el-button @click="handleImport">导入</el-button>
            <el-button @click="handleExport">导出</el-button>
            <el-button type="primary" @click="showAddDialog">新增用例</el-button>
          </div>
        </div>
      </template>
      
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="模块">
          <el-input v-model="filters.module" placeholder="请输入模块" clearable />
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="filters.priority" placeholder="请选择" clearable>
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
            <el-option label="紧急" value="critical" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="请选择" clearable>
            <el-option label="草稿" value="draft" />
            <el-option label="激活" value="active" />
            <el-option label="归档" value="archived" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadTestCases">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
      
      <el-table :data="testCases" v-loading="loading" border>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="用例标题" width="200" />
        <el-table-column prop="module" label="模块" width="120" />
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
        <el-table-column prop="created_by_name" label="创建人" width="120" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleView(row)">查看</el-button>
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
        @size-change="loadTestCases"
        @current-change="loadTestCases"
        style="margin-top: 20px; justify-content: center"
      />
    </el-card>
    
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="800px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="用例标题" prop="title">
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
          <el-col :span="12">
            <el-form-item label="优先级" prop="priority">
              <el-select v-model="form.priority">
                <el-option label="低" value="low" />
                <el-option label="中" value="medium" />
                <el-option label="高" value="high" />
                <el-option label="紧急" value="critical" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态" prop="status">
              <el-select v-model="form.status">
                <el-option label="草稿" value="draft" />
                <el-option label="激活" value="active" />
                <el-option label="归档" value="archived" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="用例描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        
        <el-form-item label="前置条件">
          <el-input v-model="form.preconditions" type="textarea" :rows="2" />
        </el-form-item>
        
        <el-form-item label="预期结果" prop="expected_result">
          <el-input v-model="form.expected_result" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
    
    <input ref="fileInput" type="file" accept=".xlsx,.xls" style="display: none" @change="handleFileChange" />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getTestCaseList, createTestCase, updateTestCase, deleteTestCase, importTestCases, exportTestCases } from '@/api/testcase'

const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const isView = ref(false)
const formRef = ref()
const fileInput = ref()
const testCases = ref([])

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const filters = reactive({
  module: '',
  priority: '',
  status: ''
})

const form = reactive({
  id: null,
  title: '',
  description: '',
  module: '',
  priority: 'medium',
  status: 'draft',
  preconditions: '',
  expected_result: ''
})

const rules = {
  title: [{ required: true, message: '请输入用例标题', trigger: 'blur' }],
  module: [{ required: true, message: '请输入所属模块', trigger: 'blur' }],
  expected_result: [{ required: true, message: '请输入预期结果', trigger: 'blur' }]
}

const dialogTitle = computed(() => {
  if (isView.value) return '查看用例'
  return isEdit.value ? '编辑用例' : '新增用例'
})

const loadTestCases = async () => {
  loading.value = true
  try {
    const res = await getTestCaseList({
      page: pagination.page,
      page_size: pagination.size,
      ...filters
    })
    testCases.value = res.data.results
    pagination.total = res.data.count
  } catch (error) {
    ElMessage.error('加载测试用例失败')
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  Object.assign(filters, {
    module: '',
    priority: '',
    status: ''
  })
  loadTestCases()
}

const showAddDialog = () => {
  isEdit.value = false
  isView.value = false
  Object.assign(form, {
    id: null,
    title: '',
    description: '',
    module: '',
    priority: 'medium',
    status: 'draft',
    preconditions: '',
    expected_result: ''
  })
  dialogVisible.value = true
}

const handleView = (row) => {
  isEdit.value = true
  isView.value = true
  Object.assign(form, row)
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  isView.value = false
  Object.assign(form, row)
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (isView.value) {
    dialogVisible.value = false
    return
  }
  await formRef.value.validate()
  submitLoading.value = true
  try {
    if (isEdit.value) {
      await updateTestCase(form.id, form)
      ElMessage.success('更新成功')
    } else {
      await createTestCase(form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadTestCases()
  } catch (error) {
    ElMessage.error('操作失败')
  } finally {
    submitLoading.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除用例 ${row.title} 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteTestCase(row.id)
    ElMessage.success('删除成功')
    loadTestCases()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleImport = () => {
  fileInput.value.click()
}

const handleFileChange = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  try {
    await importTestCases(file)
    ElMessage.success('导入成功')
    loadTestCases()
  } catch (error) {
    ElMessage.error('导入失败')
  }
  event.target.value = ''
}

const handleExport = async () => {
  try {
    const res = await exportTestCases(filters)
    const blob = new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'test_cases.xlsx'
    a.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

const getPriorityType = (priority) => {
  const typeMap = { low: 'info', medium: 'warning', high: 'danger', critical: 'danger' }
  return typeMap[priority] || 'info'
}

const getPriorityText = (priority) => {
  const textMap = { low: '低', medium: '中', high: '高', critical: '紧急' }
  return textMap[priority] || priority
}

const getStatusType = (status) => {
  const typeMap = { draft: 'info', active: 'success', archived: 'warning' }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = { draft: '草稿', active: '激活', archived: '归档' }
  return textMap[status] || status
}

onMounted(() => {
  loadTestCases()
})
</script>

<style scoped>
.testcases-page {
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
</style>
