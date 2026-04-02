<template>
  <div class="automation-environments-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>环境配置管理</span>
          <div class="search-box">
            <el-input v-model="searchForm.name" placeholder="请输入环境名称" style="width: 200px; margin-right: 10px" />
            <el-button type="primary" @click="loadEnvironments">查询</el-button>
            <el-button @click="resetSearch">重置</el-button>
          </div>
          <el-button type="primary" @click="showAddDialog">新增环境</el-button>
        </div>
      </template>
      
      <el-table :data="environments" v-loading="loading" border>
        <el-table-column prop="id" label="环境ID" width="80" />
        <el-table-column prop="name" label="环境名称" />
        <el-table-column prop="environment_type" label="环境类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getEnvironmentType(row.environment_type)">{{ getEnvironmentText(row.environment_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="base_url" label="基础URL" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
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
    
    <!-- 新增/编辑环境对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="环境名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入环境名称" />
        </el-form-item>
        
        <el-form-item label="环境类型" prop="environment_type">
          <el-select v-model="form.environment_type">
            <el-option label="测试环境" value="test" />
            <el-option label="预发环境" value="staging" />
            <el-option label="生产环境" value="production" />
            <el-option label="自定义环境" value="custom" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="基础URL" prop="base_url">
          <el-input v-model="form.base_url" placeholder="请输入基础URL" />
        </el-form-item>
        
        <el-form-item label="环境变量" prop="variables">
          <el-input v-model="variablesText" type="textarea" placeholder="请输入环境变量，格式：key1=value1\nkey2=value2" />
        </el-form-item>
        
        <el-form-item label="环境描述" prop="description">
          <el-input v-model="form.description" type="textarea" placeholder="请输入环境描述" />
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
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getEnvironmentList, createEnvironment, updateEnvironment, deleteEnvironment
} from '@/api/automation'

const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()
const environments = ref([])

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const searchForm = reactive({
  name: ''
})

const form = reactive({
  id: null,
  name: '',
  environment_type: 'test',
  base_url: '',
  variables: {},
  description: ''
})

const variablesText = ref('')

const rules = {
  name: [{ required: true, message: '请输入环境名称', trigger: 'blur' }],
  base_url: [{ required: true, message: '请输入基础URL', trigger: 'blur' }]
}

const dialogTitle = computed(() => isEdit.value ? '编辑环境' : '新增环境')

const loadEnvironments = async () => {
  loading.value = true
  try {
    const res = await getEnvironmentList({
      page: pagination.page,
      page_size: pagination.size,
      name: searchForm.name
    })
    environments.value = res.results
    pagination.total = res.count
  } catch (error) {
    ElMessage.error('加载环境列表失败')
  } finally {
    loading.value = false
  }
}

const showAddDialog = () => {
  isEdit.value = false
  Object.assign(form, {
    id: null,
    name: '',
    environment_type: 'test',
    base_url: '',
    variables: {},
    description: ''
  })
  variablesText.value = ''
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  Object.assign(form, {
    id: row.id,
    name: row.name,
    environment_type: row.environment_type,
    base_url: row.base_url,
    variables: row.variables || {},
    description: row.description
  })
  // 将variables对象转换为文本格式
  variablesText.value = Object.entries(row.variables || {}).map(([key, value]) => `${key}=${value}`).join('\n')
  dialogVisible.value = true
}

const handleSubmit = async () => {
  // 将文本格式的环境变量转换为对象
  try {
    form.variables = variablesText.value.split('\n')
      .filter(line => line.trim())
      .reduce((acc, line) => {
        const [key, ...valueParts] = line.split('=')
        acc[key.trim()] = valueParts.join('=').trim()
        return acc
      }, {})
  } catch (error) {
    ElMessage.error('环境变量格式错误')
    return
  }
  
  await formRef.value.validate()
  submitLoading.value = true
  try {
    if (isEdit.value) {
      await updateEnvironment(form.id, form)
      ElMessage.success('环境更新成功')
    } else {
      await createEnvironment(form)
      ElMessage.success('环境创建成功')
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
    await deleteEnvironment(row.id)
    ElMessage.success('环境删除成功')
    loadEnvironments()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const resetSearch = () => {
  searchForm.name = ''
  loadEnvironments()
}

const getEnvironmentType = (type) => {
  const typeMap = {
    test: 'info',
    staging: 'warning',
    production: 'danger',
    custom: 'primary'
  }
  return typeMap[type] || 'info'
}

const getEnvironmentText = (type) => {
  const textMap = {
    test: '测试环境',
    staging: '预发环境',
    production: '生产环境',
    custom: '自定义环境'
  }
  return textMap[type] || type
}

onMounted(() => {
  loadEnvironments()
})
</script>

<style scoped>
.automation-environments-page {
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
