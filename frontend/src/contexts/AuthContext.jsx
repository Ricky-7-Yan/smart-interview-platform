import React, { createContext, useContext, useState, useEffect } from 'react'
import axios from 'axios'

const AuthContext = createContext()

// API基础URL配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

// 配置axios默认值
axios.defaults.timeout = 30000 // 30秒超时
axios.defaults.headers.common['Content-Type'] = 'application/json'

export function useAuth() {
  return useContext(AuthContext)
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [token, setToken] = useState(localStorage.getItem('token'))

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      fetchUser()
    } else {
      setLoading(false)
    }
  }, [token])

  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/auth/me`)
      // 确保 target_positions 是数组
      if (response.data.target_positions && !Array.isArray(response.data.target_positions)) {
        response.data.target_positions = [response.data.target_positions]
      }
      setUser(response.data)
      setLoading(false)
    } catch (error) {
      console.error('获取用户信息失败:', error)
      localStorage.removeItem('token')
      setToken(null)
      setLoading(false)
    }
  }

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/auth/login`, {
        email,
        password
      })
      const { access_token } = response.data
      localStorage.setItem('token', access_token)
      setToken(access_token)
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      await fetchUser()
      return { success: true }
    } catch (error) {
      console.error('登录失败:', error)
      let errorMessage = '登录失败，请重试'

      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        errorMessage = '请求超时，请检查网络连接'
      } else if (error.code === 'ERR_NETWORK' || error.message.includes('Network Error')) {
        errorMessage = '网络错误，请检查后端服务是否运行'
      } else if (error.response) {
        errorMessage = error.response.data?.detail || error.response.data?.message || errorMessage
      } else if (error.request) {
        errorMessage = '无法连接到服务器，请检查后端服务是否启动'
      }

      return { success: false, error: errorMessage }
    }
  }

  const register = async (username, email, password, targetPositions) => {
    try {
      // 验证参数
      if (!username || !email || !password) {
        return { success: false, error: '请填写所有必填项' }
      }

      if (!targetPositions || !Array.isArray(targetPositions) || targetPositions.length === 0) {
        return { success: false, error: '请至少选择一个目标岗位' }
      }

      if (targetPositions.length > 10) {
        return { success: false, error: '最多只能选择10个岗位' }
      }

      const response = await axios.post(`${API_BASE_URL}/auth/register`, {
        username,
        email,
        password,
        target_positions: targetPositions
      }, {
        timeout: 30000  // 30秒超时
      })

      const { access_token } = response.data
      if (!access_token) {
        return { success: false, error: '注册成功但未获取到token，请尝试登录' }
      }

      localStorage.setItem('token', access_token)
      setToken(access_token)
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      await fetchUser()
      return { success: true }
    } catch (error) {
      console.error('注册失败:', error)

      // 处理不同类型的错误
      let errorMessage = '注册失败，请重试'

      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        errorMessage = '请求超时，请检查网络连接'
      } else if (error.code === 'ERR_NETWORK' || error.message.includes('Network Error')) {
        errorMessage = '网络错误，请检查后端服务是否运行（确保后端服务在 http://localhost:8000 运行）'
      } else if (error.response) {
        // 服务器返回了错误响应
        const status = error.response.status
        errorMessage = error.response.data?.detail || error.response.data?.message || errorMessage

        // 处理常见的HTTP错误
        if (status === 400) {
          errorMessage = error.response.data?.detail || '请求参数错误，请检查输入'
        } else if (status === 409) {
          errorMessage = '该邮箱或用户名已被注册'
        } else if (status === 500) {
          errorMessage = '服务器错误，请稍后重试'
        } else if (status === 404) {
          errorMessage = 'API接口不存在，请检查后端服务配置'
        }
      } else if (error.request) {
        // 请求已发出但没有收到响应
        errorMessage = '无法连接到服务器，请确保后端服务已启动（运行在 http://localhost:8000）'
      } else {
        // 其他错误
        errorMessage = error.message || errorMessage
      }

      return { success: false, error: errorMessage }
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
    delete axios.defaults.headers.common['Authorization']
  }

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}