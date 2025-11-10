import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import PositionSelector from '../components/PositionSelector'
import axios from 'axios'
import './Login.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

function Login() {
  const [isLogin, setIsLogin] = useState(true)
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [targetPositions, setTargetPositions] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [testingConnection, setTestingConnection] = useState(false)

  const { login, register } = useAuth()
  const navigate = useNavigate()

  // 测试后端连接
  const testConnection = async () => {
    setTestingConnection(true)
    setError('')
    try {
      const response = await axios.get(`${API_BASE_URL}/health`, {
        timeout: 5000
      })
      if (response.data.status === 'healthy') {
        setError('')
        alert('✅ 后端服务连接正常！')
      }
    } catch (error) {
      console.error('连接测试失败:', error)
      let errorMsg = '无法连接到后端服务'
      if (error.code === 'ECONNABORTED') {
        errorMsg = '连接超时，请检查后端服务是否运行'
      } else if (error.code === 'ERR_NETWORK') {
        errorMsg = '网络错误，请确保后端服务在 http://localhost:8000 运行'
      }
      setError(errorMsg)
      alert(`❌ ${errorMsg}\n\n请确保：\n1. 后端服务已启动\n2. 运行在 http://localhost:8000\n3. 网络连接正常`)
    } finally {
      setTestingConnection(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      let result
      if (isLogin) {
        // 登录验证
        if (!email || !password) {
          setError('请填写邮箱和密码')
          setLoading(false)
          return
        }
        result = await login(email, password)
      } else {
        // 注册验证
        if (!username || !email || !password) {
          setError('请填写所有必填项')
          setLoading(false)
          return
        }

        if (password.length < 6) {
          setError('密码长度至少为6位')
          setLoading(false)
          return
        }

        if (targetPositions.length === 0) {
          setError('请至少选择一个目标岗位')
          setLoading(false)
          return
        }

        if (targetPositions.length > 10) {
          setError('最多只能选择10个岗位')
          setLoading(false)
          return
        }

        result = await register(username, email, password, targetPositions)
      }

      if (result.success) {
        navigate('/')
      } else {
        setError(result.error || '操作失败，请重试')
      }
    } catch (err) {
      console.error('操作失败:', err)
      setError('操作失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  // 切换登录/注册时清空表单和错误
  const handleTabSwitch = (isLoginTab) => {
    setIsLogin(isLoginTab)
    setError('')
    setUsername('')
    setEmail('')
    setPassword('')
    setTargetPositions([])
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <h1 className="login-title">智能面试学习平台</h1>
        <p className="login-subtitle">让每一次学习都能用在面试里</p>

        {/* 项目介绍 */}
        <div className="project-intro">
          <div className="intro-section">
            <div className="intro-icon">🎯</div>
            <div className="intro-content">
              <h3>个性化面试训练</h3>
              <p>基于你的简历和目标岗位，提供定制化的面试问题和训练方案</p>
            </div>
          </div>
          <div className="intro-section">
            <div className="intro-icon">🤖</div>
            <div className="intro-content">
              <h3>AI智能评估</h3>
              <p>AI面试官实时评估你的表现，提供专业反馈和改进建议</p>
            </div>
          </div>
          <div className="intro-section">
            <div className="intro-icon">📚</div>
            <div className="intro-content">
              <h3>系统化学习</h3>
              <p>从基础能力到工程实践，全面提升面试技能和专业知识</p>
            </div>
          </div>
          <div className="intro-section">
            <div className="intro-icon">📊</div>
            <div className="intro-content">
              <h3>数据驱动成长</h3>
              <p>追踪学习进度，分析薄弱环节，生成针对性补学任务</p>
            </div>
          </div>
        </div>

        <div className="login-tabs">
          <button
            className={isLogin ? 'tab active' : 'tab'}
            onClick={() => handleTabSwitch(true)}
          >
            登录
          </button>
          <button
            className={!isLogin ? 'tab active' : 'tab'}
            onClick={() => handleTabSwitch(false)}
          >
            注册
          </button>
        </div>

        {/* 连接测试按钮 */}
        {!isLogin && (
          <div style={{ marginBottom: '16px', textAlign: 'center' }}>
            <button
              type="button"
              onClick={testConnection}
              disabled={testingConnection}
              style={{
                padding: '8px 16px',
                background: '#f5f5f7',
                border: '1px solid #d2d2d7',
                borderRadius: '8px',
                cursor: testingConnection ? 'not-allowed' : 'pointer',
                fontSize: '14px',
                color: '#1d1d1f'
              }}
            >
              {testingConnection ? '测试中...' : '🔗 测试后端连接'}
            </button>
          </div>
        )}

        <form onSubmit={handleSubmit} className="login-form">
          {!isLogin && (
            <div className="form-group">
              <label>用户名</label>
              <input
                type="text"
                className="apple-input"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                minLength={2}
                maxLength={50}
                placeholder="请输入用户名"
              />
            </div>
          )}

          <div className="form-group">
            <label>邮箱</label>
            <input
              type="email"
              className="apple-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="请输入邮箱地址"
            />
          </div>

          <div className="form-group">
            <label>密码</label>
            <input
              type="password"
              className="apple-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              placeholder="请输入密码（至少6位）"
            />
          </div>

          {!isLogin && (
            <div className="form-group">
              <label>目标岗位（至少选择一个，最多10个）</label>
              <PositionSelector
                selectedPositions={targetPositions}
                onChange={setTargetPositions}
                maxSelections={10}
                singleSelect={false}
              />
            </div>
          )}

          {error && <div className="error-message">{error}</div>}

          <button
            type="submit"
            className="apple-button"
            disabled={loading}
            style={{ width: '100%', marginTop: '20px' }}
          >
            {loading ? '处理中...' : isLogin ? '登录' : '注册'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default Login