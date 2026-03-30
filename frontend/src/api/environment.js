import request from '@/utils/request'

export const getEnvList = (params) => {
  return request({
    url: '/environments/',
    method: 'get',
    params
  })
}

export const createEnv = (data) => {
  return request({
    url: '/environments/',
    method: 'post',
    data
  })
}

export const updateEnv = (id, data) => {
  return request({
    url: `/environments/${id}/`,
    method: 'patch',
    data
  })
}

export const deleteEnv = (id) => {
  return request({
    url: `/environments/${id}/`,
    method: 'delete'
  })
}

export const addEnvVariable = (id, data) => {
  return request({
    url: `/environments/${id}/add_variable/`,
    method: 'post',
    data
  })
}

export const deleteEnvVariable = (envId, varId) => {
  return request({
    url: `/environments/${envId}/variables/${varId}/`,
    method: 'delete'
  })
}

export const getEnvStatistics = () => {
  return request({
    url: '/environments/statistics/',
    method: 'get'
  })
}
