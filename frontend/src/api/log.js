import request from '@/utils/request'

export const getOperationLogs = (params) => {
  return request({
    url: '/logs/operations/',
    method: 'get',
    params
  })
}

export const getErrorLogs = (params) => {
  return request({
    url: '/logs/errors/',
    method: 'get',
    params
  })
}

export const getOperationStatistics = () => {
  return request({
    url: '/logs/operations/statistics/',
    method: 'get'
  })
}

export const getErrorStatistics = () => {
  return request({
    url: '/logs/errors/statistics/',
    method: 'get'
  })
}
