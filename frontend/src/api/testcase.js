import request from '@/utils/request'

export const getTestCaseList = (params) => {
  return request({
    url: '/api/testcases/',
    method: 'get',
    params
  })
}

export const createTestCase = (data) => {
  return request({
    url: '/api/testcases/',
    method: 'post',
    data
  })
}

export const updateTestCase = (id, data) => {
  return request({
    url: `/api/testcases/${id}/`,
    method: 'patch',
    data
  })
}

export const deleteTestCase = (id) => {
  return request({
    url: `/api/testcases/${id}/`,
    method: 'delete'
  })
}

export const getTestCaseDetail = (id) => {
  return request({
    url: `/api/testcases/${id}/`,
    method: 'get'
  })
}

export const importTestCases = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return request({
    url: '/api/testcases/import_excel/',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const exportTestCases = (params) => {
  return request({
    url: '/api/testcases/export_excel/',
    method: 'get',
    params,
    responseType: 'blob'
  })
}

export const getTestCaseStatistics = () => {
  return request({
    url: '/api/testcases/statistics/',
    method: 'get'
  })
}
