import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import { useAuth } from '../contexts/AuthContext'
import axios from 'axios'
import './Tasks.css'

// API基础URL配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

function Tasks() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(null)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')
  const [completingTaskId, setCompletingTaskId] = useState(null)

  useEffect(() => {
    fetchTasks()
  }, [filter])

  const fetchTasks = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      const params = filter !== 'all' ? { status: filter } : {}
      const response = await axios.get(`${API_BASE_URL}/tasks/`, {
        params,
        headers: { Authorization: `Bearer ${token}` },
        timeout: 10000
      })
      setTasks(response.data)
      setError('')
    } catch (error) {
      console.error('获取任务失败:', error)
      let errorMessage = '获取任务失败，请重试'

      if (error.code === 'ERR_NETWORK' || error.message.includes('Network Error')) {
        errorMessage = '网络错误，请检查后端服务是否运行'
      } else if (error.response) {
        errorMessage = error.response.data?.detail || errorMessage
      }

      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const generateTasks = async () => {
    // 检查用户是否设置了目标岗位
    if (!user || !user.target_positions || user.target_positions.length === 0) {
      alert('请先在个人中心设置目标岗位')
      navigate('/profile')
      return
    }

    setGenerating(true)
    setError('')

    try {
      const token = localStorage.getItem('token')
      const response = await axios.post(
        `${API_BASE_URL}/tasks/generate-position-tasks`,
        { count: 4 },
        {
          headers: { Authorization: `Bearer ${token}` },
          timeout: 60000 // 60秒超时，因为生成任务可能需要调用LLM
        }
      )

      if (response.data.tasks && response.data.tasks.length > 0) {
        alert(`任务生成成功！已生成 ${response.data.tasks.length} 个任务`)
        await fetchTasks()
      } else {
        alert('任务生成成功，但未返回任务列表')
        await fetchTasks()
      }
    } catch (error) {
      console.error('生成任务失败:', error)
      let errorMessage = '生成任务失败，请重试'

      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        errorMessage = '生成任务超时，请稍后重试'
      } else if (error.code === 'ERR_NETWORK' || error.message.includes('Network Error')) {
        errorMessage = '网络错误，请检查后端服务是否运行'
      } else if (error.response) {
        const status = error.response.status
        if (status === 400) {
          errorMessage = error.response.data?.detail || '请求参数错误'
          // 如果是目标岗位未设置，提示用户
          if (errorMessage.includes('目标岗位')) {
            alert(errorMessage + '\n\n将跳转到个人中心设置目标岗位')
            navigate('/profile')
          }
        } else if (status === 500) {
          errorMessage = '服务器错误，请稍后重试'
        } else {
          errorMessage = error.response.data?.detail || errorMessage
        }
      } else if (error.request) {
        errorMessage = '无法连接到服务器，请检查后端服务是否启动'
      }

      setError(errorMessage)
      alert(`生成任务失败：${errorMessage}`)
    } finally {
      setGenerating(false)
    }
  }

  const completeTask = async (taskId, e) => {
    e.stopPropagation()
    setCompletingTaskId(taskId)

    try {
      const token = localStorage.getItem('token')
      const response = await axios.post(
        `${API_BASE_URL}/tasks/${taskId}/complete`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` },
          timeout: 60000 // 60秒超时，因为生成面试可能需要调用LLM
        }
      )

      // 检查是否成功生成了面试
      if (response.data.interview_id) {
        alert(`${response.data.message}\n\n将跳转到面试页面`)
        await fetchTasks() // 刷新任务列表
        navigate(`/interviews/${response.data.interview_id}`)
      } else if (response.data.error) {
        // 任务完成但面试生成失败
        alert(`${response.data.message}\n\n${response.data.error}`)
        await fetchTasks()
      } else {
        // 任务完成但没有面试（非岗位任务）
        alert(response.data.message)
        await fetchTasks()
      }
    } catch (error) {
      console.error('完成任务失败:', error)
      let errorMessage = '完成任务失败，请重试'

      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        errorMessage = '操作超时，请稍后重试'
      } else if (error.code === 'ERR_NETWORK' || error.message.includes('Network Error')) {
        errorMessage = '网络错误，请检查后端服务是否运行'
      } else if (error.response) {
        errorMessage = error.response.data?.detail || errorMessage
      }

      alert(`完成任务失败：${errorMessage}`)
    } finally {
      setCompletingTaskId(null)
    }
  }

  const deleteTask = async (taskId) => {
    try {
      const token = localStorage.getItem('token')
      await axios.delete(`${API_BASE_URL}/tasks/${taskId}`, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 10000
      })
      alert('任务已删除')
      await fetchTasks()
      setShowDeleteConfirm(null)
    } catch (error) {
      console.error('删除任务失败:', error)
      let errorMessage = '删除失败，请重试'

      if (error.response) {
        errorMessage = error.response.data?.detail || errorMessage
      }

      alert(`删除失败：${errorMessage}`)
    }
  }

  if (loading) {
    return (
      <div className="tasks-page">
        <Navbar />
        <div className="container">
          <div style={{ textAlign: 'center', padding: '40px' }}>加载中...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="tasks-page">
      <Navbar />
      <div className="container">
        <div className="page-header">
          <h1 className="page-title">我的任务</h1>
          <button
            className="apple-button"
            onClick={generateTasks}
            disabled={generating}
          >
            {generating ? '生成中...' : '生成新任务'}
          </button>
        </div>

        {error && (
          <div style={{
            margin: '16px 0',
            padding: '12px',
            background: '#ffe5e5',
            color: '#ff3b30',
            borderRadius: '8px',
            fontSize: '14px'
          }}>
            {error}
          </div>
        )}

        <div className="filter-tabs">
          <button
            className={filter === 'all' ? 'filter-tab active' : 'filter-tab'}
            onClick={() => setFilter('all')}
          >
            全部
          </button>
          <button
            className={filter === 'pending' ? 'filter-tab active' : 'filter-tab'}
            onClick={() => setFilter('pending')}
          >
            待完成
          </button>
          <button
            className={filter === 'completed' ? 'filter-tab active' : 'filter-tab'}
            onClick={() => setFilter('completed')}
          >
            已完成
          </button>
        </div>

        {tasks.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📋</div>
            <h2>暂无任务</h2>
            <p>点击"生成新任务"开始学习之旅</p>
            {!user?.target_positions || user.target_positions.length === 0 ? (
              <div style={{ marginTop: '16px', padding: '12px', background: '#fff3cd', borderRadius: '8px' }}>
                <p style={{ margin: 0, color: '#856404' }}>
                  ⚠️ 请先在个人中心设置目标岗位
                </p>
                <button
                  className="apple-button"
                  onClick={() => navigate('/profile')}
                  style={{ marginTop: '12px' }}
                >
                  前往设置
                </button>
              </div>
            ) : (
              <button className="apple-button" onClick={generateTasks} disabled={generating}>
                {generating ? '生成中...' : '生成新任务'}
              </button>
            )}
          </div>
        ) : (
          <div className="tasks-grid">
            {tasks.map(task => (
              <div
                key={task.id}
                className="task-card"
                onClick={() => navigate(`/tasks/${task.id}`)}
                style={{ cursor: 'pointer' }}
              >
                <div className="task-header">
                  <h3 className="task-title">{task.title}</h3>
                  <div className="task-header-actions">
                    <span className={`task-status ${task.status}`}>
                      {task.status === 'pending' ? '待完成' :
                       task.status === 'in_progress' ? '进行中' : '已完成'}
                    </span>
                    <button
                      className="delete-task-button"
                      onClick={(e) => {
                        e.stopPropagation()
                        setShowDeleteConfirm(task.id)
                      }}
                      title="删除任务"
                    >
                      🗑️
                    </button>
                  </div>
                </div>

                <p className="task-description">{task.description || '暂无描述'}</p>

                <div className="task-footer">
                  <div className="task-reward">
                    <span>🎁</span>
                    <span>+{task.experience_reward || 0} 经验值</span>
                  </div>
                  {task.status === 'pending' && (
                    <button
                      className="apple-button"
                      onClick={(e) => completeTask(task.id, e)}
                      disabled={completingTaskId === task.id}
                    >
                      {completingTaskId === task.id ? '处理中...' : '完成任务'}
                    </button>
                  )}
                  {task.status === 'completed' && task.related_interview_id && (
                    <button
                      className="apple-button"
                      onClick={(e) => {
                        e.stopPropagation()
                        navigate(`/interviews/${task.related_interview_id}`)
                      }}
                      style={{ background: '#34c759' }}
                    >
                      查看面试
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 删除确认弹窗 */}
      {showDeleteConfirm && (
        <div className="delete-confirm-modal">
          <div className="delete-confirm-content">
            <h3>确认删除</h3>
            <p>确定要删除这个任务吗？此操作不可恢复。</p>
            <div className="delete-confirm-actions">
              <button
                className="confirm-delete-btn"
                onClick={() => deleteTask(showDeleteConfirm)}
              >
                确认删除
              </button>
              <button
                className="cancel-delete-btn"
                onClick={() => setShowDeleteConfirm(null)}
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Tasks