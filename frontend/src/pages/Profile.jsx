import React, { useEffect, useState } from 'react'
import Navbar from '../components/Navbar'
import { useAuth } from '../contexts/AuthContext'
import PositionSelector from '../components/PositionSelector'
import axios from 'axios'
import './Profile.css'

// API基础URL配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

function Profile() {
  const { user } = useAuth()
  const [editing, setEditing] = useState(false)
  const [targetPositions, setTargetPositions] = useState([])
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState({
    completedTasks: 0,
    completedInterviews: 0,
    avgScore: 0,
    learningDays: 0
  })
  const [statsLoading, setStatsLoading] = useState(true)

  useEffect(() => {
    // 初始化岗位列表
    if (user?.target_positions) {
      setTargetPositions(Array.isArray(user.target_positions) ? user.target_positions : [user.target_positions])
    }
    // 加载统计数据
    loadStats()
  }, [user])

  const loadStats = async () => {
    try {
      setStatsLoading(true)
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

      const allTasks = tasksRes.data || []
      const allInterviews = interviewsRes.data || []

      // 计算已完成的任务
      const completedTasks = allTasks.filter(t =>
        t.status === 'completed' || t.status === 'COMPLETED'
      ).length

      // 计算已完成的面试
      const completedInterviews = allInterviews.filter(i =>
        i.status === 'completed' || i.status === 'COMPLETED'
      )

      // 计算平均分数
      const avgScore = completedInterviews.length > 0
        ? completedInterviews.reduce((sum, i) => sum + (parseFloat(i.total_score) || 0), 0) / completedInterviews.length
        : 0

      // 计算学习天数（从第一次完成任务或面试开始）
      let firstActivityDate = null

      // 从已完成任务中找最早日期
      const completedTasksList = allTasks.filter(t =>
        t.status === 'completed' || t.status === 'COMPLETED'
      )
      if (completedTasksList.length > 0) {
        const taskDates = completedTasksList
          .map(t => t.completed_at ? new Date(t.completed_at) : null)
          .filter(d => d !== null)
        if (taskDates.length > 0) {
          firstActivityDate = new Date(Math.min(...taskDates.map(d => d.getTime())))
        }
      }

      // 从已完成面试中找最早日期
      if (completedInterviews.length > 0) {
        const interviewDates = completedInterviews
          .map(i => i.completed_at ? new Date(i.completed_at) : i.created_at ? new Date(i.created_at) : null)
          .filter(d => d !== null)
        if (interviewDates.length > 0) {
          const earliestInterview = new Date(Math.min(...interviewDates.map(d => d.getTime())))
          if (!firstActivityDate || earliestInterview < firstActivityDate) {
            firstActivityDate = earliestInterview
          }
        }
      }

      // 如果没有完成记录，从创建时间计算
      if (!firstActivityDate && allTasks.length > 0) {
        const taskDates = allTasks
          .map(t => t.created_at ? new Date(t.created_at) : null)
          .filter(d => d !== null)
        if (taskDates.length > 0) {
          firstActivityDate = new Date(Math.min(...taskDates.map(d => d.getTime())))
        }
      }

      if (!firstActivityDate && allInterviews.length > 0) {
        const interviewDates = allInterviews
          .map(i => i.created_at ? new Date(i.created_at) : null)
          .filter(d => d !== null)
        if (interviewDates.length > 0) {
          firstActivityDate = new Date(Math.min(...interviewDates.map(d => d.getTime())))
        }
      }

      const learningDays = firstActivityDate
        ? Math.max(1, Math.ceil((new Date() - firstActivityDate) / (1000 * 60 * 60 * 24)))
        : 0

      setStats({
        completedTasks,
        completedInterviews: completedInterviews.length,
        avgScore: avgScore.toFixed(1),
        learningDays
      })
    } catch (error) {
      console.error('加载统计数据失败:', error)
      // 设置默认值
      setStats({
        completedTasks: 0,
        completedInterviews: 0,
        avgScore: 0,
        learningDays: 0
      })
    } finally {
      setStatsLoading(false)
    }
  }

  const handleUpdatePositions = async () => {
    if (targetPositions.length === 0) {
      alert('请至少保留一个目标岗位')
      return
    }

    if (targetPositions.length > 10) {
      alert('最多只能选择10个岗位')
      return
    }

    setLoading(true)
    try {
      const token = localStorage.getItem('token')
      const response = await axios.put(`${API_BASE_URL}/auth/update-positions`, {
        target_positions: targetPositions
      }, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 10000
      })
      alert('目标岗位已更新')
      setEditing(false)
      // 刷新用户信息
      window.location.reload()
    } catch (error) {
      console.error('更新失败:', error)
      let errorMessage = '更新失败'
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      }
      alert(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const getTitleInfo = () => {
    const titles = {
      '新手': {
        description: '刚刚开始你的面试学习之旅',
        color: '#86868b',
        nextLevel: '面试新秀 (Lv.1)',
        nextBenefit: '解锁面试题库和简历模板'
      },
      '面试新秀': {
        description: '已解锁行业通用面试题库和简历模板库',
        color: '#007aff',
        nextLevel: '面经达人 (Lv.4)',
        nextBenefit: '获得AI模拟面试逐字稿优化服务'
      },
      '面经达人': {
        description: '可使用AI模拟面试后的逐字稿优化服务',
        color: '#5ac8fa',
        nextLevel: '面霸 (Lv.7)',
        nextBenefit: '解锁企业真实面试真题和内推机会'
      },
      '面霸': {
        description: '已解锁企业HR/业务负责人录制的真实岗位面试真题，并可获得内推机会对接',
        color: '#667eea',
        nextLevel: '已达到最高等级',
        nextBenefit: '继续学习提升技能'
      }
    }
    return titles[user?.title] || titles['新手']
  }

  const titleInfo = getTitleInfo()
  const nextLevelXP = (user?.current_level || 1) * 100
  const currentXP = user?.experience_points || 0
  const progress = (currentXP % 100) / 100

  return (
    <div className="profile-page">
      <Navbar />
      <div className="container">
        <h1 className="page-title">个人中心</h1>

        <div className="profile-grid">
          <div className="profile-card main-card">
            <div className="avatar-section">
              <div className="avatar" style={{ background: `linear-gradient(135deg, ${titleInfo.color}, ${titleInfo.color}88)` }}>
                {user?.username?.[0]?.toUpperCase() || 'U'}
              </div>
              <div className="user-info">
                <h2 className="user-name">{user?.username}</h2>
                <p className="user-email">{user?.email}</p>
              </div>
            </div>

            <div className="level-section">
              <div className="level-header">
                <div>
                  <div className="current-level">等级 {user?.current_level || 1}</div>
                  <div className="current-title" style={{ color: titleInfo.color }}>
                    {user?.title || '新手'}
                  </div>
                </div>
                <div className="level-badge" style={{ background: titleInfo.color }}>
                  <div className="badge-icon">🏆</div>
                </div>
              </div>

              <div className="progress-section">
                <div className="progress-header">
                  <span>经验值: {currentXP}</span>
                  <span>下一级: {nextLevelXP - currentXP} XP</span>
                </div>
                <div className="progress-bar-large">
                  <div
                    className="progress-fill-large"
                    style={{
                      width: `${progress * 100}%`,
                      background: `linear-gradient(90deg, ${titleInfo.color}, ${titleInfo.color}88)`
                    }}
                  />
                </div>
              </div>
            </div>

            <div className="target-position-section">
              <div className="section-header">
                <h3>目标岗位 ({targetPositions.length}/10)</h3>
                {!editing ? (
                  <button className="edit-button" onClick={() => setEditing(true)}>
                    编辑
                  </button>
                ) : (
                  <div className="edit-actions">
                    <button
                      className="save-button"
                      onClick={handleUpdatePositions}
                      disabled={loading || targetPositions.length === 0}
                    >
                      {loading ? '保存中...' : '保存'}
                    </button>
                    <button
                      className="cancel-button"
                      onClick={() => {
                        setEditing(false)
                        setTargetPositions(Array.isArray(user?.target_positions) ? user.target_positions : (user?.target_positions ? [user.target_positions] : []))
                      }}
                    >
                      取消
                    </button>
                  </div>
                )}
              </div>

              {editing ? (
                <PositionSelector
                  selectedPositions={targetPositions}
                  onChange={setTargetPositions}
                  maxSelections={10}
                  singleSelect={false}
                />
              ) : (
                <div className="positions-display">
                  {targetPositions.length > 0 ? (
                    <div className="positions-tags">
                      {targetPositions.map((pos, index) => (
                        <span key={index} className="position-display-tag">{pos}</span>
                      ))}
                    </div>
                  ) : (
                    <div className="no-positions">未设置目标岗位</div>
                  )}
                </div>
              )}
            </div>
          </div>

          <div className="profile-card benefits-card">
            <h3 className="card-title">当前权益</h3>
            <div className="benefits-list">
              {user?.benefits?.unlocked_features?.map((feature, index) => (
                <div key={index} className="benefit-item-large">
                  <span className="benefit-icon-large">✨</span>
                  <div>
                    <div className="benefit-name">{getFeatureName(feature)}</div>
                    <div className="benefit-desc">{getFeatureDesc(feature)}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="profile-card next-level-card">
            <h3 className="card-title">下一等级</h3>
            <div className="next-level-info">
              <div className="next-level-name">{titleInfo.nextLevel}</div>
              <div className="next-level-benefit">
                <span className="benefit-icon">🎁</span>
                <span>{titleInfo.nextBenefit}</span>
              </div>
              <div className="xp-remaining">
                还需 {nextLevelXP - currentXP} 经验值
              </div>
            </div>
          </div>

          <div className="profile-card stats-card">
            <h3 className="card-title">学习统计</h3>
            {statsLoading ? (
              <div style={{ textAlign: 'center', padding: '20px' }}>加载中...</div>
            ) : (
              <div className="stats-list">
                <div className="stat-item">
                  <div className="stat-label">完成任务</div>
                  <div className="stat-value">{stats.completedTasks}</div>
                </div>
                <div className="stat-item">
                  <div className="stat-label">完成面试</div>
                  <div className="stat-value">{stats.completedInterviews}</div>
                </div>
                <div className="stat-item">
                  <div className="stat-label">平均分数</div>
                  <div className="stat-value">{stats.avgScore}</div>
                </div>
                <div className="stat-item">
                  <div className="stat-label">学习天数</div>
                  <div className="stat-value">{stats.learningDays}</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function getFeatureName(feature) {
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

function getFeatureDesc(feature) {
  const descs = {
    'basic_interview': '可以使用基础的面试功能',
    'basic_tasks': '可以接收和完成基础任务',
    'interview_question_bank': '访问行业通用面试题库',
    'resume_templates': '使用专业简历模板',
    'ai_interview_review': '获得AI智能面试分析',
    'word_by_word_optimization': '获得面试逐字稿优化建议',
    'real_company_interviews': '访问真实企业面试真题',
    'internal_referral': '获得内推机会对接服务'
  }
  return descs[feature] || '功能描述'
}

export default Profile