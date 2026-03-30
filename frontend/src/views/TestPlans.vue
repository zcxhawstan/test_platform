<template>
  <div class="testplans-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>测试计划管理</span>
          <el-button type="primary" @click="showAddDialog">新增计划</el-button>
        </div>
      </template>
      
      <el-table :data="testPlans" v-loading="loading" border>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="计划名称" width="200" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="start_date" label="开始日期" width="120" />
        <el-table-column prop="end_date" label="结束日期" width="120" />
        <el-table-column prop="cases_count" label="用例数" width="80" />
        <el-table-column prop="passed_count" label="通过" width="80">
          <template #default="{ row }">
            <span style="color: #67C23A">{{ row.passed_count }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="failed_count" label="失败" width="80">
          <template #default="{ row }">
            <span style="color: #F56C6C">{{ row.failed_count }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_by_name" label="创建人" width="120" />
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
        @size-change="loadTestPlans"
        @current-change="loadTestPlans"
        style="margin-top: 20px; justify-content: center"
      />
    </el-card>
    
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="计划名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        
        <el-form-item label="计划描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="状态" prop="status">
              <el-select v-model="form.status">
                <el-option label="草稿" value="draft" />
                <el-option label="进行中" value="active" />
                <el-option label="已完成" value="completed" />
                <el-option label="已取消" value="cancelled" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="创建人">
              <el-input v-model="form.created_by_name" disabled />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始日期" prop="start_date">
              <el-date-picker v-model="form.start_date" type="date" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束日期" prop="end_date">
              <el-date-picker v-model="form.end_date" type="date" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="detailVisible" title="计划详情" width="1000px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="计划名称">{{ currentPlan.name }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentPlan.status)">{{ getStatusText(currentPlan.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="开始日期">{{ currentPlan.start_date }}</el-descriptions-item>
        <el-descriptions-item label="结束日期">{{ currentPlan.end_date }}</el-descriptions-item>
        <el-descriptions-item label="创建人">{{ currentPlan.created_by_name }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ currentPlan.created_at }}</el-descriptions-item>
        <el-descriptions-item label="计划描述" :span="2">{{ currentPlan.description }}</el-descriptions-item>
      </el-descriptions>
      
      <div style="margin-top: 20px">
        <el-button type="primary" @click="showAddCaseDialog">添加用例</el-button>
      </div>
      
      <el-table :data="currentPlan.plan_cases" border style="margin-top: 10px">
        <el-table-column prop="test_case_title" label="用例标题" width="200" />
        <el-table-column prop="test_case_module" label="模块" width="120" />
        <el-table-column prop="test_case_priority" label="优先级" width="100">
          <template #default="{ row }">
            <el-tag :type="getPriorityType(row.test_case_priority)">{{ getPriorityText(row.test_case_priority) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="execution_status" label="执行状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getExecutionStatusType(row.execution_status)">{{ getExecutionStatusText(row.execution_status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="actual_result" label="实际结果" />
        <el-table-column prop="executed_by_name" label="执行人" width="100" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleExecute(row)">执行</el-button>
            <el-button type="danger" size="small" @click="handleRemoveCase(row)">移除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
    
    <el-dialog v-model="addCaseVisible" title="添加用例" width="600px">
      <el-form :inline="true">
        <el-form-item>
          <el-input v-model="caseSearch" placeholder="搜索用例" clearable @change="loadAvailableCases" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadAvailableCases">搜索</el-button>
        </el-form-item>
      </el-form>
      
      <el-table :data="availableCases" @selection-change="handleCaseSelection" border>
        <el-table-column type="selection" width="55" />
        <el-table-column prop="title" label="用例标题" />
        <el-table-column prop="module" label="模块" width="120" />
        <el-table-column prop="priority" label="优先级" width="100">
          <template #default="{ row }">
            <el-tag :type="getPriorityType(row.priority)">{{ getPriorityText(row.priority) }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
      
      <template #footer>
        <el-button @click="addCaseVisible = false">取消</el-button>
        <el-button type="primary" :loading="addCaseLoading" @click="handleAddCases">确定</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="executeVisible" title="执行用例" width="600px">
      <el-form ref="executeFormRef" :model="executeForm" :rules="executeRules" label-width="100px">
        <el-form-item label="执行状态" prop="execution_status">
          <el-select v-model="executeForm.execution_status">
            <el-option label="未执行" value="not_run" />
            <el-option label="通过" value="passed" />
            <el-option label="失败" value="failed" />
            <el-option label="阻塞" value="blocked" />
            <el-option label="跳过" value="skipped" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="实际结果">
          <el-input v-model="executeForm.actual_result" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="executeVisible = false">取消</el-button>
        <el-button type="primary" :loading="executeLoading" @click="handleExecuteSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getTestPlanList, createTestPlan, updateTestPlan, deleteTestPlan, getTestPlanDetail, addCasesToPlan, removeCaseFromPlan, executeCase } from '@/api/testplan'
import { getTestCaseList } from '@/api/testcase'

const loading = ref(false)
const submitLoading = ref(false)
const addCaseLoading = ref(false)
const executeLoading = ref(false)
const dialogVisible = ref(false)
const detailVisible = ref(false)
const addCaseVisible = ref(false)
const executeVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()
const executeFormRef = ref()
const testPlans = ref([])
const availableCases = ref([])
const selectedCases = ref([])
const currentPlan = ref({})
const currentCase = ref({})
const caseSearch = ref('')

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const form = reactive({
  id: null,
  name: '',
  description: '',
  status: 'draft',
  start_date: '',
  end_date: '',
  created_by_name: ''
})

const executeForm = reactive({
  execution_status: 'passed',
  actual_result: ''
})

const rules = {
  name: [{ required: true, message: '请输入计划名称', trigger: 'blur' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }],
  start_date: [{ required: true, message: '请选择开始日期', trigger: 'change' }],
  end_date: [{ required: true, message: '请选择结束日期', trigger: 'change' }]
}

const executeRules = {
  execution_status: [{ required: true, message: '请选择执行状态', trigger: 'change' }]
}

const dialogTitle = computed(() => isEdit.value ? '编辑计划' : '新增计划')

const loadTestPlans = async () => {
  loading.value = true
  try {
    const res = await getTestPlanList({
      page: pagination.page,
      page_size: pagination.size
    })
    testPlans.value = res.data.results
    pagination.total = res.data.count
  } catch (error) {
    ElMessage.error('加载测试计划失败')
  } finally {
    loading.value = false
  }
}

const showAddDialog = () => {
  isEdit.value = false
  Object.assign(form, {
    id: null,
    name: '',
    description: '',
    status: 'draft',
    start_date: '',
    end_date: '',
    created_by_name: ''
  })
  dialogVisible.value = true
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
      await updateTestPlan(form.id, form)
      ElMessage.success('更新成功')
    } else {
      await createTestPlan(form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadTestPlans()
  } catch (error) {
    ElMessage.error('操作失败')
  } finally {
    submitLoading.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除计划 ${row.name} 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteTestPlan(row.id)
    ElMessage.success('删除成功')
    loadTestPlans()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleView = async (row) => {
  try {
    const res = await getTestPlanDetail(row.id)
    currentPlan.value = res.data
    detailVisible.value = true
  } catch (error) {
    ElMessage.error('加载详情失败')
  }
}

const showAddCaseDialog = () => {
  caseSearch.value = ''
  loadAvailableCases()
  addCaseVisible.value = true
}

const loadAvailableCases = async () => {
  try {
    const res = await getTestCaseList({ search: caseSearch.value, page_size: 100 })
    availableCases.value = res.data.results
  } catch (error) {
    ElMessage.error('加载用例失败')
  }
}

const handleCaseSelection = (selection) => {
  selectedCases.value = selection
}

const handleAddCases = async () => {
  if (selectedCases.value.length === 0) {
    ElMessage.warning('请选择用例')
    return
  }
  
  addCaseLoading.value = true
  try {
    await addCasesToPlan(currentPlan.value.id, {
      test_case_ids: selectedCases.value.map(c => c.id)
    })
    ElMessage.success('添加成功')
    addCaseVisible.value = false
    handleView(currentPlan.value)
  } catch (error) {
    ElMessage.error('添加失败')
  } finally {
    addCaseLoading.value = false
  }
}

const handleRemoveCase = async (row) => {
  try {
    await ElMessageBox.confirm('确定要移除该用例吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await removeCaseFromPlan(currentPlan.value.id, row.test_case)
    ElMessage.success('移除成功')
    handleView(currentPlan.value)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('移除失败')
    }
  }
}

const handleExecute = (row) => {
  currentCase.value = row
  Object.assign(executeForm, {
    execution_status: row.execution_status || 'passed',
    actual_result: row.actual_result || ''
  })
  executeVisible.value = true
}

const handleExecuteSubmit = async () => {
  await executeFormRef.value.validate()
  executeLoading.value = true
  try {
    await executeCase(currentPlan.value.id, currentCase.value.test_case, executeForm)
    ElMessage.success('执行成功')
    executeVisible.value = false
    handleView(currentPlan.value)
  } catch (error) {
    ElMessage.error('执行失败')
  } finally {
    executeLoading.value = false
  }
}

const getStatusType = (status) => {
  const typeMap = { draft: 'info', active: 'warning', completed: 'success', cancelled: 'danger' }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = { draft: '草稿', active: '进行中', completed: '已完成', cancelled: '已取消' }
  return textMap[status] || status
}

const getPriorityType = (priority) => {
  const typeMap = { low: 'info', medium: 'warning', high: 'danger', critical: 'danger' }
  return typeMap[priority] || 'info'
}

const getPriorityText = (priority) => {
  const textMap = { low: '低', medium: '中', high: '高', critical: '紧急' }
  return textMap[priority] || priority
}

const getExecutionStatusType = (status) => {
  const typeMap = { not_run: 'info', passed: 'success', failed: 'danger', blocked: 'warning', skipped: 'info' }
  return typeMap[status] || 'info'
}

const getExecutionStatusText = (status) => {
  const textMap = { not_run: '未执行', passed: '通过', failed: '失败', blocked: '阻塞', skipped: '跳过' }
  return textMap[status] || status
}

onMounted(() => {
  loadTestPlans()
})
</script>

<style scoped>
.testplans-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
