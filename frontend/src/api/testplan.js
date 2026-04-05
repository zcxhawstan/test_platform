import request from '@/utils/request'

export const getTestPlanList = (params) => {
  return request({
    url: '/api/testplans/',
    method: 'get',
    params
  })
}

export const createTestPlan = (data) => {
  return request({
    url: '/api/testplans/',
    method: 'post',
    data
  })
}

export const updateTestPlan = (id, data) => {
  return request({
    url: `/api/testplans/${id}/`,
    method: 'patch',
    data
  })
}

export const deleteTestPlan = (id) => {
  return request({
    url: `/api/testplans/${id}/`,
    method: 'delete'
  })
}

export const getTestPlanDetail = (id) => {
  return request({
    url: `/api/testplans/${id}/`,
    method: 'get'
  })
}

export const removeCaseFromPlan = (planId, caseId) => {
  return request({
    url: `/api/testplans/${planId}/remove_case/${caseId}/`,
    method: 'delete'
  })
}

export const executeCase = (planId, caseId, data) => {
  return request({
    url: `/api/testplans/${planId}/cases/${caseId}/execute/`,
    method: 'post',
    data
  })
}

export const getTestPlanStatistics = () => {
  return request({
    url: '/api/testplans/statistics/',
    method: 'get'
  })
}

export const addCasesToPlan = (planId, data) => {
  return request({
    url: `/api/testplans/${planId}/add_cases/`,
    method: 'post',
    data
  })
}
