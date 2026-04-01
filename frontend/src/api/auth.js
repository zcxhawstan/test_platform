import request from '@/utils/request'

export const login = (data) => {
  return request({
    url: '/auth/users/login/',
    method: 'post',
    data
  })
}

export const register = (data) => {
  return request({
    url: '/auth/users/register/',
    method: 'post',
    data
  })
}

export const logout = () => {
  return request({
    url: '/auth/users/logout/',
    method: 'post'
  })
}

export const getProfile = () => {
  return request({
    url: '/auth/users/profile/',
    method: 'get'
  })
}

export const updateProfile = (data) => {
  return request({
    url: '/auth/users/profile/',
    method: 'put',
    data
  })
}

export const changePassword = (data) => {
  return request({
    url: '/auth/users/change_password/',
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
