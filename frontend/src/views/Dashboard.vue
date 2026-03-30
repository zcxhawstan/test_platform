<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="测试用例" :value="stats.testCases" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="测试计划" :value="stats.testPlans" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="缺陷数量" :value="stats.defects" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="API测试" :value="stats.apiTests" />
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>测试用例分布</span>
          </template>
          <div ref="testCaseChart" style="height: 300px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>缺陷状态分布</span>
          </template>
          <div ref="defectChart" style="height: 300px"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { getTestCaseStatistics } from '@/api/testcase'
import { getTestPlanStatistics } from '@/api/testplan'
import { getDefectStatistics } from '@/api/defect'
import { getApiTestStatistics } from '@/api/apitest'

const testCaseChart = ref()
const defectChart = ref()
const stats = ref({
  testCases: 0,
  testPlans: 0,
  defects: 0,
  apiTests: 0
})

let testCaseChartInstance = null
let defectChartInstance = null

const loadStats = async () => {
  try {
    const [testCaseRes, testPlanRes, defectRes, apiTestRes] = await Promise.all([
      getTestCaseStatistics(),
      getTestPlanStatistics(),
      getDefectStatistics(),
      getApiTestStatistics()
    ])
    
    stats.value = {
      testCases: testCaseRes.data.total,
      testPlans: testPlanRes.data.total,
      defects: defectRes.data.total,
      apiTests: apiTestRes.data.total
    }
    
    initTestCaseChart(testCaseRes.data)
    initDefectChart(defectRes.data)
  } catch (error) {
    console.error('加载统计数据失败', error)
  }
}

const initTestCaseChart = (data) => {
  if (!testCaseChart.value) return
  
  testCaseChartInstance = echarts.init(testCaseChart.value)
  testCaseChartInstance.setOption({
    tooltip: {
      trigger: 'item'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '测试用例',
        type: 'pie',
        radius: '50%',
        data: [
          { value: data.draft, name: '草稿' },
          { value: data.active, name: '激活' },
          { value: data.archived, name: '归档' }
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  })
}

const initDefectChart = (data) => {
  if (!defectChart.value) return
  
  defectChartInstance = echarts.init(defectChart.value)
  defectChartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    xAxis: {
      type: 'category',
      data: ['新建', '处理中', '已解决', '已关闭']
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '缺陷数量',
        type: 'bar',
        data: [data.new, data.in_progress, data.resolved, data.closed]
      }
    ]
  })
}

onMounted(() => {
  loadStats()
  window.addEventListener('resize', () => {
    testCaseChartInstance?.resize()
    defectChartInstance?.resize()
  })
})

onBeforeUnmount(() => {
  testCaseChartInstance?.dispose()
  defectChartInstance?.dispose()
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.stat-card {
  text-align: center;
}
</style>
