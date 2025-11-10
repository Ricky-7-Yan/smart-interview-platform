import React, { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import Navbar from '../components/Navbar'
import { useAuth } from '../contexts/AuthContext'
import axios from 'axios'
import './Interviews.css'

// API基础URL配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

function Interviews() {
  const { id } = useParams()
  const { user } = useAuth()
  const navigate = useNavigate()
  const [interviews, setInterviews] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchInterviews()
  }, [])

  const fetchInterviews = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      const response = await axios.get(`${API_BASE_URL}/interviews/`, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 10000
      })
      setInterviews(response.data || [])
    } catch (error) {
      console.error('获取面试列表失败:', error)
      setInterviews([])
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="interviews-page">
        <Navbar />
        <div className="container">
          <div style={{ textAlign: 'center', padding: '40px' }}>加载中...</div>
        </div>
      </div>
    )
  }

  // 面试列表页
  return (
    <div className="interviews-page">
      <Navbar />
      <div className="container">
        <h1 className="page-title">我的面试</h1>

        {interviews.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🎤</div>
            <h2>暂无面试记录</h2>
            <p>完成任务后会自动生成关联面试</p>
            <button
              className="apple-button"
              onClick={() => navigate('/tasks')}
            >
              去完成任务
            </button>
          </div>
        ) : (
          <div className="interviews-list">
            {interviews.map(interview => (
              <div
                key={interview.id}
                className="interview-card"
                onClick={() => navigate(`/interviews/room/${interview.id}`)}
                style={{ cursor: 'pointer' }}
              >
                <div className="interview-card-header">
                  <h3 className="interview-card-title">
                    {interview.interview_type === 'task_based'
                      ? '任务关联面试'
                      : interview.interview_type === 'stage_based'
                      ? '阶段性面试'
                      : '补学验证面试'}
                  </h3>
                  <span className={`interview-status ${interview.status}`}>
                    {interview.status === 'pending' ? '待完成' :
                     interview.status === 'completed' ? '已完成' : '已审核'}
                  </span>
                </div>

                {interview.status === 'completed' && interview.total_score !== null && (
                  <div className="interview-score">
                    <span className="score-label">总分:</span>
                    <span className="score-value">{interview.total_score?.toFixed(1)} / 10.0</span>
                  </div>
                )}

                <div className="interview-meta">
                  <span>创建时间: {new Date(interview.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Interviews