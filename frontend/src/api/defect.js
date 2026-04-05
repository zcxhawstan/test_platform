import request from '@/utils/request'

export const getDefectList = (params) => {
  return request({
    url: '/api/defects/',
    method: 'get',
    params
  })
}

export const createDefect = (data) => {
  return request({
    url: '/api/defects/',
    method: 'post',
    data
  })
}

export const updateDefect = (id, data) => {
  return request({
    url: `/api/defects/${id}/`,
    method: 'patch',
    data
  })
}

export const deleteDefect = (id) => {
  return request({
    url: `/api/defects/${id}/`,
    method: 'delete'
  })
}

export const getDefectDetail = (id) => {
  return request({
    url: `/api/defects/${id}/`,
    method: 'get'
  })
}

export const updateDefectStatus = (id, data) => {
  return request({
    url: `/api/defects/${id}/update_status/`,
    method: 'post',
    data
  })
}

export const addComment = (id, data) => {
  return request({
    url: `/api/defects/${id}/add_comment/`,
    method: 'post',
    data
  })
}

export const getDefectStatistics = () => {
  return request({
    url: '/api/defects/statistics/',
    method: 'get'
  })
}
