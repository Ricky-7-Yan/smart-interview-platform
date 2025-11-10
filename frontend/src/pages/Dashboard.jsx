import React, { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import Navbar from '../components/Navbar'
import axios from 'axios'
import './Dashboard.css'

// API基础URL配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

function Dashboard() {
  const { user } = useAuth()
  const [stats, setStats] = useState({
    totalTasks: 0,
    completedTasks: 0,
    totalInterviews: 0,
    avgScore: 0
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')

      const [tasksRes, interviewsRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/tasks/`, {
          headers: { Authorization: `Bearer ${token}` },
          timeout: 10000
        }),
        axios.get(`${API_BASE_URL}/interviews/`, {
          headers: { Authorization: `Bearer ${token}` },
          timeout: 10000
        })
      ])

      const tasks = tasksRes.data || []
      const interviews = interviewsRes.data || []

      const completedTasks = tasks.filter(t => t.status === 'completed' || t.status === 'COMPLETED').length
      const completedInterviews = interviews.filter(i => i.status === 'completed' || i.status === 'COMPLETED')
      const avgScore = completedInterviews.length > 0
        ? completedInterviews.reduce((sum, i) => sum + (parseFloat(i.total_score) || 0), 0) / completedInterviews.length
        : 0

      setStats({
        totalTasks: tasks.length,
        completedTasks,
        totalInterviews: interviews.length,
        avgScore: avgScore.toFixed(1)
      })
    } catch (error) {
      console.error('获取统计数据失败:', error)
      // 即使失败也设置默认值
      setStats({
        totalTasks: 0,
        completedTasks: 0,
        totalInterviews: 0,
        avgScore: 0
      })
    } finally {
      setLoading(false)
    }
  }

  const getTitleDescription = () => {
    const titles = {
      '新手': '刚刚开始你的面试学习之旅',
      '面试新秀': '已解锁面试题库和简历模板',
      '面经达人': '可使用AI模拟面试逐字稿优化服务',
      '面霸': '解锁真实企业面试真题和内推机会'
    }
    return titles[user?.title] || titles['新手']
  }

  const getFeatureName = (feature) => {
    const names = {
      'basic_interview': '基础面试',
      'basic_tasks': '基础任务',
      'interview_question_bank': '面试题库',
      'resume_templates': '简历模板',
      'ai_interview_review': 'AI面试回顾',
      'word_by_word_optimization': '逐字稿优化',
      'real_company_interviews': '真实企业面试',
      'internal_referral': '内推机会'
    }
    return names[feature] || feature
  }

  if (loading) {
    return (
      <div className="dashboard">
        <Navbar />
        <div className="container">
          <div style={{ textAlign: 'center', padding: '40px' }}>加载中...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="dashboard">
      <Navbar />
      <div className="container">
        <div className="welcome-section">
          <h1 className="welcome-title">欢迎回来, {user?.username}</h1>
          <p className="welcome-subtitle">继续你的面试学习之旅</p>
        </div>

        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">📊</div>
            <div className="stat-value">{stats.totalTasks}</div>
            <div className="stat-label">总任务数</div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">✅</div>
            <div className="stat-value">{stats.completedTasks}</div>
            <div className="stat-label">已完成</div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">🎤</div>
            <div className="stat-value">{stats.totalInterviews}</div>
            <div className="stat-label">面试次数</div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">⭐</div>
            <div className="stat-value">{stats.avgScore}</div>
            <div className="stat-label">平均分数</div>
          </div>
        </div>

        <div className="profile-card">
          <div className="profile-header">
            <div>
              <h2 className="section-title">个人资料</h2>
              <p className="profile-subtitle">{getTitleDescription()}</p>
            </div>
            <div className="level-badge">
              <div className="level-number">Lv.{user?.current_level || 1}</div>
              <div className="level-title">{user?.title || '新手'}</div>
            </div>
          </div>

          <div className="progress-bar-container">
            <div className="progress-info">
              <span>经验值: {user?.experience_points || 0}</span>
              <span>下一级需要: {((user?.current_level || 1) * 100) - (user?.experience_points || 0)}</span>
            </div>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{
                  width: `${((user?.experience_points || 0) % 100)}%`
                }}
              />
            </div>
          </div>

          <div className="benefits-list">
            <h3 className="benefits-title">当前权益</h3>
            {user?.benefits?.unlocked_features?.map((feature, index) => (
              <div key={index} className="benefit-item">
                <span className="benefit-icon">✨</span>
                <span>{getFeatureName(feature)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard