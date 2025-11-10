import React, { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import axios from 'axios'
import './InterviewRoom.css'

function InterviewRoom() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [interview, setInterview] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [videoStream, setVideoStream] = useState(null)
  const videoRef = useRef(null)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    fetchInterview()
    startVideo()
    return () => {
      stopVideo()
    }
  }, [id])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const fetchInterview = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await axios.get(`http://localhost:8000/api/interviews/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setInterview(response.data)

      // 初始化消息
      if (response.data.questions) {
        const initMessages = response.data.questions.map((q, index) => ({
          role: 'assistant',
          content: q,
          timestamp: new Date()
        }))
        setMessages(initMessages)
      }
    } catch (error) {
      console.error('获取面试详情失败:', error)
    }
  }

  const startVideo = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true
      })
      setVideoStream(stream)
      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }
    } catch (error) {
      console.error('无法访问摄像头:', error)
      alert('无法访问摄像头，请检查权限设置')
    }
  }

  const stopVideo = () => {
    if (videoStream) {
      videoStream.getTracks().forEach(track => track.stop())
      setVideoStream(null)
    }
  }

  const toggleRecording = () => {
    setIsRecording(!isRecording)
    // 这里可以添加录制逻辑
  }

  const sendMessage = async () => {
    if (!input.trim()) return

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')

    // 模拟AI回复
    setTimeout(() => {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '收到你的回答，请继续。',
        timestamp: new Date()
      }])
    }, 1000)
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  if (!interview) {
    return (
      <div className="interview-room-page">
        <Navbar />
        <div className="container">加载中...</div>
      </div>
    )
  }

  return (
    <div className="interview-room-page">
      <Navbar />
      <div className="interview-room-container">
        <div className="interview-room-header">
          <button className="back-button" onClick={() => navigate('/interviews')}>
            ← 返回面试列表
          </button>
          <h1 className="interview-title">模拟面试</h1>
          <div className="interview-controls">
            <button
              className={`record-button ${isRecording ? 'recording' : ''}`}
              onClick={toggleRecording}
            >
              {isRecording ? '⏹ 停止录制' : '● 开始录制'}
            </button>
            <button className="end-interview-button" onClick={() => navigate('/interviews')}>
              结束面试
            </button>
          </div>
        </div>

        <div className="interview-room-content">
          <div className="video-section">
            <div className="video-container">
              <video
                ref={videoRef}
                autoPlay
                muted
                playsInline
                className="user-video"
              />
              <div className="video-overlay">
                <div className="interview-info">
                  <h2>{interview.interview_type === 'task_based' ? '任务关联面试' : '模拟面试'}</h2>
                  <p>请保持摄像头开启，认真回答问题</p>
                </div>
              </div>
            </div>
            <div className="video-controls">
              <button className="control-button" onClick={startVideo}>
                📹 开启摄像头
              </button>
              <button className="control-button" onClick={stopVideo}>
                📵 关闭摄像头
              </button>
              <button className="control-button">
                🎤 静音
              </button>
            </div>
          </div>

          <div className="chat-section">
            <div className="chat-header">
              <h3>面试对话</h3>
            </div>
            <div className="chat-messages">
              {messages.map((msg, index) => (
                <div key={index} className={`chat-message ${msg.role}`}>
                  <div className="chat-avatar">
                    {msg.role === 'user' ? '👤' : '🤖'}
                  </div>
                  <div className="chat-content">
                    {msg.content}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
            <div className="chat-input">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="输入你的回答..."
                className="chat-input-field"
              />
              <button className="send-button" onClick={sendMessage}>
                发送
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default InterviewRoom