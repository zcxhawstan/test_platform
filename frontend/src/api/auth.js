import request from '@/utils/request'

export const login = (data) => {
  return request({
    url: '/auth/login/',
    method: 'post',
    data
  })
}

export const register = (data) => {
  return request({
    url: '/auth/register/',
    method: 'post',
    data
  })
}

export const logout = () => {
  return request({
    url: '/auth/logout/',
    method: 'post'
  })
}

export const getProfile = () => {
  return request({
    url: '/auth/profile/',
    method: 'get'
  })
}

export const updateProfile = (data) => {
  return request({
    url: '/auth/profile/',
    method: 'put',
    data
  })
}

export const changePassword = (data) => {
  return request({
    url: '/auth/change-password/',
    method: 'post',
    data
  })
}

export const getUserList = (params) => {
  return request({
    url: '/auth/users/',
    method: 'get',
    params
  })
}

export const deleteUser = (id) => {
  return request({
    url: `/auth/users/${id}/`,
    method: 'delete'
  })
}
