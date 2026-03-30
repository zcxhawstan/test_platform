<template>
  <div class="environments-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>环境管理</span>
          <el-button type="primary" @click="showAddDialog">新增环境</el-button>
        </div>
      </template>
      
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="环境类型">
          <el-select v-model="filters.env_type" placeholder="请选择" clearable>
            <el-option label="开发环境" value="dev" />
            <el-option label="测试环境" value="test" />
            <el-option label="预发布环境" value="staging" />
            <el-option label="生产环境" value="prod" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="请选择" clearable>
            <el-option label="激活" value="active" />
            <el-option label="未激活" value="inactive" />
            <el-option label="维护中" value="maintenance" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadEnvironments">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
      
      <el-table :data="environments" v-loading="loading" border>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="环境名称" width="150" />
        <el-table-column prop="env_type" label="环境类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getEnvTypeColor(row.env_type)">{{ getEnvTypeText(row.env_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="host" label="主机地址" width="200" />
        <el-table-column prop="port" label="端口" width="80" />
        <el-table-column prop="database_name" label="数据库名" width="150" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
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
        @size-change="loadEnvironments"
        @current-change="loadEnvironments"
        style="margin-top: 20px; justify-content: center"
      />
    </el-card>
    
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="700px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="环境名称" prop="name">
              <el-input v-model="form.name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="环境类型" prop="env_type">
              <el-select v-model="form.env_type">
                <el-option label="开发环境" value="dev" />
                <el-option label="测试环境" value="test" />
                <el-option label="预发布环境" value="staging" />
                <el-option label="生产环境" value="prod" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="主机地址" prop="host">
              <el-input v-model="form.host" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="端口号" prop="port">
              <el-input-number v-model="form.port" :min="1" :max="65535" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="数据库名称" prop="database_name">
              <el-input v-model="form.database_name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态" prop="status">
              <el-select v-model="form.status">
                <el-option label="激活" value="active" />
                <el-option label="未激活" value="inactive" />
                <el-option label="维护中" value="maintenance" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="数据库用户" prop="database_user">
              <el-input v-model="form.database_user" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="数据库密码" prop="database_password">
              <el-input v-model="form.database_password" type="password" show-password />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="环境描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="detailVisible" title="环境详情" width="800px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="环境名称">{{ currentEnv.name }}</el-descriptions-item>
        <el-descriptions-item label="环境类型">
          <el-tag :type="getEnvTypeColor(currentEnv.env_type)">{{ getEnvTypeText(currentEnv.env_type) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="主机地址">{{ currentEnv.host }}</el-descriptions-item>
        <el-descriptions-item label="端口号">{{ currentEnv.port }}</el-descriptions-item>
        <el-descriptions-item label="数据库名称">{{ currentEnv.database_name }}</el-descriptions-item>
        <el-descriptions-item label="数据库用户">{{ currentEnv.database_user }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentEnv.status)">{{ getStatusText(currentEnv.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建人">{{ currentEnv.created_by_name }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ currentEnv.created_at }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ currentEnv.updated_at }}</el-descriptions-item>
        <el-descriptions-item label="环境描述" :span="2">{{ currentEnv.description }}</el-descriptions-item>
      </el-descriptions>
      
      <div style="margin-top: 20px">
        <el-button type="primary" @click="showAddVariableDialog">添加变量</el-button>
      </div>
      
      <el-divider>环境变量</el-divider>
      
      <el-table :data="currentEnv.variables" border>
        <el-table-column prop="key" label="变量名" width="200" />
        <el-table-column prop="value" label="变量值" />
        <el-table-column prop="description" label="描述" width="200" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button type="danger" size="small" @click="handleDeleteVariable(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
    
    <el-dialog v-model="variableVisible" title="添加变量" width="500px">
      <el-form ref="variableFormRef" :model="variableForm" :rules="variableRules" label-width="100px">
        <el-form-item label="变量名" prop="key">
          <el-input v-model="variableForm.key" />
        </el-form-item>
        
        <el-form-item label="变量值" prop="value">
          <el-input v-model="variableForm.value" type="textarea" :rows="3" />
        </el-form-item>
        
        <el-form-item label="变量描述">
          <el-input v-model="variableForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="variableVisible = false">取消</el-button>
        <el-button type="primary" :loading="variableLoading" @click="handleAddVariable">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getEnvList, createEnv, updateEnv, deleteEnv, addEnvVariable, deleteEnvVariable } from '@/api/environment'

const loading = ref(false)
const submitLoading = ref(false)
const variableLoading = ref(false)
const dialogVisible = ref(false)
const detailVisible = ref(false)
const variableVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()
const variableFormRef = ref()
const environments = ref([])
const currentEnv = ref({})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const filters = reactive({
  env_type: '',
  status: ''
})

const form = reactive({
  id: null,
  name: '',
  env_type: 'test',
  description: '',
  host: '',
  port: 3306,
  database_name: '',
  database_user: '',
  database_password: '',
  status: 'active'
})

const variableForm = reactive({
  key: '',
  value: '',
  description: ''
})

const rules = {
  name: [{ required: true, message: '请输入环境名称', trigger: 'blur' }],
  env_type: [{ required: true, message: '请选择环境类型', trigger: 'change' }],
  host: [{ required: true, message: '请输入主机地址', trigger: 'blur' }],
  port: [{ required: true, message: '请输入端口号', trigger: 'blur' }],
  database_name: [{ required: true, message: '请输入数据库名称', trigger: 'blur' }],
  database_user: [{ required: true, message: '请输入数据库用户', trigger: 'blur' }],
  database_password: [{ required: true, message: '请输入数据库密码', trigger: 'blur' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
}

const variableRules = {
  key: [{ required: true, message: '请输入变量名', trigger: 'blur' }],
  value: [{ required: true, message: '请输入变量值', trigger: 'blur' }]
}

const dialogTitle = computed(() => isEdit.value ? '编辑环境' : '新增环境')

const loadEnvironments = async () => {
  loading.value = true
  try {
    const res = await getEnvList({
      page: pagination.page,
      page_size: pagination.size,
      ...filters
    })
    environments.value = res.data.results
    pagination.total = res.data.count
  } catch (error) {
    ElMessage.error('加载环境列表失败')
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  Object.assign(filters, {
    env_type: '',
    status: ''
  })
  loadEnvironments()
}

const showAddDialog = () => {
  isEdit.value = false
  Object.assign(form, {
    id: null,
    name: '',
    env_type: 'test',
    description: '',
    host: '',
    port: 3306,
    database_name: '',
    database_user: '',
    database_password: '',
    status: 'active'
  })
  dialogVisible.value = true
}

const handleView = (row) => {
  currentEnv.value = row
  detailVisible.value = true
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
      await updateEnv(form.id, form)
      ElMessage.success('更新成功')
    } else {
      await createEnv(form)
      ElMessage.success('创建成功')
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
    await deleteEnv(row.id)
    ElMessage.success('删除成功')
    loadEnvironments()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const showAddVariableDialog = () => {
  Object.assign(variableForm, {
    key: '',
    value: '',
    description: ''
  })
  variableVisible.value = true
}

const handleAddVariable = async () => {
  await variableFormRef.value.validate()
  variableLoading.value = true
  try {
    await addEnvVariable(currentEnv.value.id, variableForm)
    ElMessage.success('添加成功')
    variableVisible.value = false
    handleView(currentEnv.value)
  } catch (error) {
    ElMessage.error('添加失败')
  } finally {
    variableLoading.value = false
  }
}

const handleDeleteVariable = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该变量吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteEnvVariable(currentEnv.value.id, row.id)
    ElMessage.success('删除成功')
    handleView(currentEnv.value)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const getEnvTypeColor = (type) => {
  const colorMap = { dev: 'info', test: 'warning', staging: 'primary', prod: 'danger' }
  return colorMap[type] || 'info'
}

const getEnvTypeText = (type) => {
  const textMap = { dev: '开发环境', test: '测试环境', staging: '预发布环境', prod: '生产环境' }
  return textMap[type] || type
}

const getStatusType = (status) => {
  const typeMap = { active: 'success', inactive: 'info', maintenance: 'warning' }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = { active: '激活', inactive: '未激活', maintenance: '维护中' }
  return textMap[status] || status
}

onMounted(() => {
  loadEnvironments()
})
</script>

<style scoped>
.environments-page {
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
