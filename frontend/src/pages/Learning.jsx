import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import ChatInterface from '../components/ChatInterface'
import FloatingChat from '../components/FloatingChat'
import axios from 'axios'
import './Learning.css'

function Learning() {
  const navigate = useNavigate()
  const [uploading, setUploading] = useState(false)

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)

      const token = localStorage.getItem('token')
      await axios.post('http://localhost:8000/api/learning/upload-material', formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      })

      alert('学习资料上传成功！')
    } catch (error) {
      console.error('上传失败:', error)
      alert('上传失败，请重试')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="learning-page">
      <Navbar />
      <FloatingChat contextType="learning" />
      <div className="learning-container">
        <div className="learning-header">
          <div>
            <h1 className="page-title">学习模块</h1>
            <p className="page-subtitle">完成学习任务，提升专业知识</p>
          </div>
          <div className="learning-actions">
            <label className="upload-button">
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleFileUpload}
                disabled={uploading}
                style={{ display: 'none' }}
              />
              {uploading ? '上传中...' : '📁 上传学习资料'}
            </label>
            <button
              className="apple-button"
              onClick={() => navigate('/tasks')}
            >
              查看任务
            </button>
          </div>
        </div>

        <div className="learning-content">
          <div className="learning-chat">
            <ChatInterface contextType="learning" onNavigate={navigate} />
          </div>
          <div className="learning-sidebar">
            <div className="sidebar-card">
              <h3>学习功能</h3>
              <ul className="feature-list">
                <li>📚 专业知识学习</li>
                <li>✅ 完成学习任务</li>
                <li>📝 定制化学习内容</li>
                <li>📊 学习进度跟踪</li>
              </ul>
            </div>
            <div className="sidebar-card">
              <h3>快速操作</h3>
              <button
                className="sidebar-button"
                onClick={() => navigate('/tasks')}
              >
                查看我的任务
              </button>
              <button
                className="sidebar-button"
                onClick={() => navigate('/interviews')}
              >
                查看面试记录
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Learning