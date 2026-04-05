import request from '@/utils/request'

export const getEnvironmentList = (params) => {
  return request({
    url: '/api/apitest/environments/',
    method: 'get',
    params
  })
}

export const createEnvironment = (data) => {
  return request({
    url: '/api/apitest/environments/',
    method: 'post',
    data
  })
}

export const updateEnvironment = (id, data) => {
  return request({
    url: `/api/apitest/environments/${id}/`,
    method: 'patch',
    data
  })
}

export const deleteEnvironment = (id) => {
  return request({
    url: `/api/apitest/environments/${id}/`,
    method: 'delete'
  })
}

export const addVariable = (id, data) => {
  return request({
    url: `/api/apitest/environments/${id}/add_variable/`,
    method: 'post',
    data
  })
}

export const deleteVariable = (envId, varId) => {
  return request({
    url: `/api/apitest/environments/${envId}/variables/${varId}/`,
    method: 'delete'
  })
}

export const getApiTestCaseList = (params) => {
  return request({
    url: '/api/apitest/cases/',
    method: 'get',
    params
  })
}

export const createApiTestCase = (data) => {
  return request({
    url: '/api/apitest/cases/',
    method: 'post',
    data
  })
}

export const updateApiTestCase = (id, data) => {
  return request({
    url: `/api/apitest/cases/${id}/`,
    method: 'patch',
    data
  })
}

export const deleteApiTestCase = (id) => {
  return request({
    url: `/api/apitest/cases/${id}/`,
    method: 'delete'
  })
}

export const executeApiTest = (data) => {
  return request({
    url: '/api/apitest/cases/execute/',
    method: 'post',
    data
  })
}

export const getExecutionList = (params) => {
  return request({
    url: '/api/apitest/executions/',
    method: 'get',
    params
  })
}

export const getApiTestStatistics = () => {
  return request({
    url: '/api/apitest/executions/statistics/',
    method: 'get'
  })
}
