import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import ChatInterface from '../components/ChatInterface'
import FloatingChat from '../components/FloatingChat'
import axios from 'axios'
import './Personalized.css'

// API基础URL配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

function Personalized() {
  const navigate = useNavigate()
  const [resume, setResume] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [isInterviewMode, setIsInterviewMode] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    loadResume()
  }, [])

  const loadResume = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await axios.get(`${API_BASE_URL}/resume/`, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 10000
      })
      setResume(response.data)
      setError('')
    } catch (error) {
      if (error.response?.status !== 404) {
        console.error('加载简历失败:', error)
        setError('加载简历失败，请重试')
      }
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    // 验证文件类型
    const fileType = file.name.split('.').pop().toLowerCase()
    if (!['pdf', 'docx', 'txt'].includes(fileType)) {
      setError('不支持的文件类型，请上传PDF、DOCX或TXT文件')
      return
    }

    // 验证文件大小（限制为10MB）
    const maxSize = 10 * 1024 * 1024 // 10MB
    if (file.size > maxSize) {
      setError('文件大小不能超过10MB')
      return
    }

    setUploading(true)
    setError('')

    try {
      const formData = new FormData()
      formData.append('file', file)

      const token = localStorage.getItem('token')
      const response = await axios.post(
        `${API_BASE_URL}/resume/upload`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          },
          timeout: 60000, // 60秒超时，因为文件上传可能需要更长时间
          onUploadProgress: (progressEvent) => {
            // 可以在这里显示上传进度
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            )
            console.log(`上传进度: ${percentCompleted}%`)
          }
        }
      )

      setResume(response.data)
      setError('')
      alert('简历上传成功！')

      // 清空文件输入，允许重新选择同一文件
      e.target.value = ''
    } catch (error) {
      console.error('上传失败:', error)
      let errorMessage = '上传失败，请重试'

      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        errorMessage = '上传超时，请检查网络连接或文件大小'
      } else if (error.code === 'ERR_NETWORK' || error.message.includes('Network Error')) {
        errorMessage = '网络错误，请检查后端服务是否运行'
      } else if (error.response) {
        errorMessage = error.response.data?.detail || error.response.data?.message || errorMessage
      } else if (error.request) {
        errorMessage = '无法连接到服务器，请检查后端服务是否启动'
      }

      setError(errorMessage)
      alert(`上传失败：${errorMessage}`)
    } finally {
      setUploading(false)
    }
  }

  const startInterview = async () => {
    if (!resume) {
      alert('请先上传简历')
      return
    }

    setIsInterviewMode(true)

    // 通过ChatInterface发送开始面试的消息
    // AI会根据简历自然引导对话
    const chatEvent = new CustomEvent('startInterviewMode', {
      detail: { resume: resume }
    })
    window.dispatchEvent(chatEvent)
  }

  return (
    <div className="personalized-page">
      <Navbar />
      <FloatingChat contextType="personalized" />
      <div className="personalized-container">
        <div className="personalized-header">
          <div>
            <h1 className="page-title">个性化模块</h1>
            <p className="page-subtitle">基于简历的个性化面试训练</p>
          </div>
          <label className="upload-button" style={{ position: 'relative' }}>
            <input
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={handleFileUpload}
              disabled={uploading}
              style={{ display: 'none' }}
            />
            {uploading ? '上传中...' : '📄 上传简历'}
          </label>
        </div>

        {error && (
          <div style={{
            margin: '16px',
            padding: '12px',
            background: '#ffe5e5',
            color: '#ff3b30',
            borderRadius: '8px',
            fontSize: '14px'
          }}>
            {error}
          </div>
        )}

        <div className="personalized-content">
          <div className="personalized-chat">
            <ChatInterface
              contextType="personalized"
              onNavigate={navigate}
              isInterviewMode={isInterviewMode}
            />
          </div>
          <div className="personalized-sidebar">
            {resume ? (
              <>
                <div className="sidebar-card">
                  <h3>简历信息</h3>
                  <div className="resume-info">
                    <p><strong>文件名：</strong>{resume.file_name}</p>
                    {resume.parsed_data?.name && (
                      <p><strong>姓名：</strong>{resume.parsed_data.name}</p>
                    )}
                    {resume.parsed_data?.education && (
                      <p><strong>教育：</strong>{resume.parsed_data.education}</p>
                    )}
                  </div>
                </div>
                <div className="sidebar-card">
                  <h3>面试训练</h3>
                  <button
                    className="apple-button start-interview-btn"
                    onClick={startInterview}
                    disabled={isInterviewMode}
                  >
                    {isInterviewMode ? '面试进行中...' : '开始对话'}
                  </button>
                </div>
              </>
            ) : (
              <div className="sidebar-card">
                <h3>上传简历</h3>
                <p>上传你的简历，AI将基于简历内容生成针对性的面试问题。</p>
                <label className="upload-button">
                  <input
                    type="file"
                    accept=".pdf,.docx,.txt"
                    onChange={handleFileUpload}
                    disabled={uploading}
                    style={{ display: 'none' }}
                  />
                  {uploading ? '上传中...' : '选择文件'}
                </label>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Personalized