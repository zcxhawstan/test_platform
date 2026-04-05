import request from '@/utils/request'

export const getOperationLogs = (params) => {
  return request({
    url: '/api/logs/operations/',
    method: 'get',
    params
  })
}

export const getErrorLogs = (params) => {
  return request({
    url: '/api/logs/errors/',
    method: 'get',
    params
  })
}

export const getOperationStatistics = () => {
  return request({
    url: '/api/logs/operations/statistics/',
    method: 'get'
  })
}

export const getErrorStatistics = () => {
  return request({
    url: '/api/logs/errors/statistics/',
    method: 'get'
  })
}
