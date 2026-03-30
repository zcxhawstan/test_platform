import request from '@/utils/request'

export const getTestPlanList = (params) => {
  return request({
    url: '/testplans/',
    method: 'get',
    params
  })
}

export const createTestPlan = (data) => {
  return request({
    url: '/testplans/',
    method: 'post',
    data
  })
}

export const updateTestPlan = (id, data) => {
  return request({
    url: `/testplans/${id}/`,
    method: 'patch',
    data
  })
}

export const deleteTestPlan = (id) => {
  return request({
    url: `/testplans/${id}/`,
    method: 'delete'
  })
}

export const getTestPlanDetail = (id) => {
  return request({
    url: `/testplans/${id}/`,
    method: 'get'
  })
}

export const addCasesToPlan = (id, data) => {
  return request({
    url: `/testplans/${id}/add_cases/`,
    method: 'post',
    data
  })
}

export const removeCaseFromPlan = (planId, caseId) => {
  return request({
    url: `/testplans/${planId}/remove_case/${caseId}/`,
    method: 'delete'
  })
}

export const executeCase = (planId, caseId, data) => {
  return request({
    url: `/testplans/${planId}/cases/${caseId}/execute/`,
    method: 'post',
    data
  })
}

export const getTestPlanStatistics = () => {
  return request({
    url: '/testplans/statistics/',
    method: 'get'
  })
}
