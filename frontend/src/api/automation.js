import request from '@/utils/request'

// 环境配置相关API
export const getEnvironmentList = (params) => {
  return request({
    url: '/automation/environments/',
    method: 'get',
    params
  })
}

export const createEnvironment = (data) => {
  return request({
    url: '/automation/environments/',
    method: 'post',
    data
  })
}

export const updateEnvironment = (id, data) => {
  return request({
    url: `/automation/environments/${id}/`,
    method: 'put',
    data
  })
}

export const deleteEnvironment = (id) => {
  return request({
    url: `/automation/environments/${id}/`,
    method: 'delete'
  })
}

// 自动化任务相关API
export const getTaskList = (params) => {
  return request({
    url: '/automation/tasks/',
    method: 'get',
    params
  })
}

export const createTask = (data) => {
  return request({
    url: '/automation/tasks/',
    method: 'post',
    data
  })
}

export const updateTask = (id, data) => {
  return request({
    url: `/automation/tasks/${id}/`,
    method: 'put',
    data
  })
}

export const deleteTask = (id) => {
  return request({
    url: `/automation/tasks/${id}/`,
    method: 'delete'
  })
}

export const executeTask = (id) => {
  return request({
    url: `/automation/tasks/${id}/execute/`,
    method: 'post'
  })
}

export const stopTask = (id) => {
  return request({
    url: `/automation/tasks/${id}/stop/`,
    method: 'post'
  })
}

// 执行历史相关API
export const getExecutionList = (params) => {
  return request({
    url: '/automation/executions/',
    method: 'get',
    params
  })
}

export const getExecutionLogs = (id) => {
  return request({
    url: `/automation/executions/${id}/logs/`,
    method: 'get'
  })
}

export const getExecutionReports = (id) => {
  return request({
    url: `/automation/executions/${id}/reports/`,
    method: 'get'
  })
}

// 报告相关API
export const getReportList = (params) => {
  return request({
    url: '/automation/reports/',
    method: 'get',
    params
  })
}

export const downloadReport = (id) => {
  return request({
    url: `/automation/reports/${id}/download/`,
    method: 'get'
  })
}

export const previewReport = (id) => {
  return request({
    url: `/automation/reports/${id}/preview/`,
    method: 'get'
  })
}
