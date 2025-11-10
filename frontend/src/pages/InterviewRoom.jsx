import React, { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import axios from 'axios'
import './InterviewRoom.css'

// API基础URL配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

function InterviewRoom() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [interview, setInterview] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [videoStream, setVideoStream] = useState(null)
  const [isMuted, setIsMuted] = useState(false)
  const [showFeedback, setShowFeedback] = useState(false)
  const [feedbackData, setFeedbackData] = useState(null)
  const [loadingFeedback, setLoadingFeedback] = useState(false)
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [answers, setAnswers] = useState([])
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
      const response = await axios.get(`${API_BASE_URL}/interviews/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setInterview(response.data)

      // 初始化：只显示第一个问题
      if (response.data.questions && response.data.questions.length > 0) {
        setMessages([{
          role: 'assistant',
          content: response.data.questions[0],
          timestamp: new Date(),
          questionIndex: 0
        }])
        setCurrentQuestionIndex(0)
      }
    } catch (error) {
      console.error('获取面试详情失败:', error)
      alert('获取面试详情失败，请重试')
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

  const toggleMute = () => {
    if (videoStream) {
      const audioTracks = videoStream.getAudioTracks()
      audioTracks.forEach(track => {
        track.enabled = isMuted
      })
      setIsMuted(!isMuted)
    }
  }

  const toggleRecording = () => {
    setIsRecording(!isRecording)
  }

  const sendMessage = async () => {
    if (!input.trim()) return

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date(),
      questionIndex: currentQuestionIndex
    }

    setMessages(prev => [...prev, userMessage])
    setAnswers(prev => [...prev, { questionIndex: currentQuestionIndex, answer: input }])
    const currentInput = input
    setInput('')

    // 保存答案后，显示下一个问题或结束
    const nextIndex = currentQuestionIndex + 1
    if (nextIndex < (interview?.questions?.length || 0)) {
      setTimeout(() => {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: interview.questions[nextIndex],
          timestamp: new Date(),
          questionIndex: nextIndex
        }])
        setCurrentQuestionIndex(nextIndex)
      }, 500)
    } else {
      // 所有问题已回答
      setTimeout(() => {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: '很好！你已经回答了所有问题。可以点击"结束面试"查看反馈。',
          timestamp: new Date()
        }])
      }, 500)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const handleEndInterview = async () => {
    setLoadingFeedback(true)
    try {
      const token = localStorage.getItem('token')

      // 整理答案
      const answersList = answers.map(a => ({
        question_id: a.questionIndex,
        answer: a.answer
      }))

      // 提交面试并获取反馈
      const response = await axios.post(
        `${API_BASE_URL}/interviews/${id}/submit`,
        { answers: answersList },
        { headers: { Authorization: `Bearer ${token}` } }
      )

      // 获取详细反馈
      const feedbackResponse = await axios.get(
        `${API_BASE_URL}/interviews/${id}/feedback`,
        { headers: { Authorization: `Bearer ${token}` } }
      )

      setFeedbackData({
        ...feedbackResponse.data,
        questions: interview.questions,
        answers: answersList.map(a => a.answer)
      })
      setShowFeedback(true)
    } catch (error) {
      console.error('获取反馈失败:', error)
      alert('获取反馈失败，请重试')
    } finally {
      setLoadingFeedback(false)
    }
  }

  const getCurrentQuestion = () => {
    const lastAssistantMsg = [...messages].reverse().find(msg => msg.role === 'assistant' && msg.questionIndex !== undefined)
    return lastAssistantMsg ? lastAssistantMsg.content : interview?.questions?.[0] || '欢迎开始面试'
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
            <button
              className="end-interview-button"
              onClick={handleEndInterview}
              disabled={loadingFeedback}
            >
              {loadingFeedback ? '生成反馈中...' : '结束面试'}
            </button>
          </div>
        </div>

        <div className="interview-room-content">
          <div className="video-section">
            <div className="video-container">
              {/* 主屏幕显示面试题目和面试官 */}
              <div className="main-screen">
                <div className="interviewer-avatar">
                  <div className="avatar-circle">
                    <div className="avatar-initial">面</div>
                  </div>
                  <div className="avatar-label">AI面试官</div>
                </div>
                <div className="question-display">
                  <h3 className="current-question-title">当前题目</h3>
                  <p className="current-question-text">{getCurrentQuestion()}</p>
                </div>
              </div>

              {/* 小窗口显示被面试者 */}
              <div className="user-video-corner">
                <video
                  ref={videoRef}
                  autoPlay
                  muted={isMuted}
                  playsInline
                  className="user-video-small"
                />
                <div className="video-label">你</div>
              </div>
            </div>
            <div className="video-controls">
              <button className="control-button" onClick={startVideo}>
                📹 开启摄像头
              </button>
              <button className="control-button" onClick={stopVideo}>
                📵 关闭摄像头
              </button>
              <button className={`control-button ${isMuted ? 'muted' : ''}`} onClick={toggleMute}>
                {isMuted ? '🔇 取消静音' : '🎤 静音'}
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

      {/* 面试反馈弹窗 */}
      {showFeedback && feedbackData && (
        <div className="feedback-modal-overlay" onClick={() => setShowFeedback(false)}>
          <div className="feedback-modal" onClick={(e) => e.stopPropagation()}>
            <div className="feedback-header">
              <h2>面试反馈</h2>
              <button className="close-button" onClick={() => setShowFeedback(false)}>×</button>
            </div>

            <div className="feedback-content">
              {/* 总分 */}
              <div className="feedback-section">
                <h3 className="section-title">总体评分</h3>
                <div className="score-display">
                  <div className="total-score">{feedbackData.total_score?.toFixed(1) || '0.0'}</div>
                  <div className="score-label">总分 / 10.0</div>
                </div>
                {feedbackData.scores && (
                  <div className="score-breakdown">
                    <div className="score-item">
                      <span>逻辑清晰度</span>
                      <span>{feedbackData.scores.logic || 0}/10</span>
                    </div>
                    <div className="score-item">
                      <span>表达流畅度</span>
                      <span>{feedbackData.scores.clarity || 0}/10</span>
                    </div>
                    <div className="score-item">
                      <span>专业深度</span>
                      <span>{feedbackData.scores.professionalism || 0}/10</span>
                    </div>
                    <div className="score-item">
                      <span>问题理解度</span>
                      <span>{feedbackData.scores.understanding || 0}/10</span>
                    </div>
                  </div>
                )}
              </div>

              {/* 题目和答案 */}
              <div className="feedback-section">
                <h3 className="section-title">题目与答案</h3>
                {feedbackData.questions?.map((question, index) => (
                  <div key={index} className="qa-item">
                    <div className="question-block">
                      <div className="question-number">题目 {index + 1}</div>
                      <p className="question-text">{question}</p>
                    </div>
                    <div className="answer-block">
                      <div className="answer-label">你的回答：</div>
                      <p className="answer-text">{feedbackData.answers?.[index] || '未回答'}</p>
                    </div>
                    <div className="standard-answer-block">
                      <div className="standard-answer-label">标准答案参考：</div>
                      <p className="standard-answer-text">
                        {formatFeedbackText(feedbackData.standard_answers?.[index] || '标准答案生成中...')}
                      </p>
                    </div>
                  </div>
                ))}
              </div>

              {/* 面部表情评价 */}
              <div className="feedback-section">
                <h3 className="section-title">面部表情评价</h3>
                <div className="evaluation-item">
                  <p className="evaluation-text">
                    {formatFeedbackText(feedbackData.facial_expression_evaluation || '表情自然，眼神交流良好，整体表现自信。')}
                  </p>
                </div>
              </div>

              {/* 语气和用词评价 */}
              <div className="feedback-section">
                <h3 className="section-title">语气和用词评价</h3>
                <div className="evaluation-item">
                  <p className="evaluation-text">
                    {formatFeedbackText(feedbackData.tone_evaluation || '语气适中，用词准确，表达清晰。')}
                  </p>
                </div>
              </div>

              {/* 后续学习方向 */}
              <div className="feedback-section">
                <h3 className="section-title">后续学习方向</h3>
                <div className="learning-directions">
                  {feedbackData.weaknesses?.map((weakness, index) => (
                    <div key={index} className="learning-item">
                      <span className="learning-icon">📚</span>
                      <span>{weakness}</span>
                    </div>
                  ))}
                  {(!feedbackData.weaknesses || feedbackData.weaknesses.length === 0) && (
                    <p className="no-weaknesses">表现优秀，继续保持！</p>
                  )}
                </div>
              </div>

              {/* 详细反馈 */}
              {feedbackData.feedback && (
                <div className="feedback-section">
                  <h3 className="section-title">详细反馈</h3>
                  <p className="feedback-text">{formatFeedbackText(feedbackData.feedback)}</p>
                </div>
              )}
            </div>

            <div className="feedback-footer">
              <button
                className="feedback-close-btn"
                onClick={() => {
                  setShowFeedback(false)
                  navigate('/interviews')
                }}
              >
                返回面试列表
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// 格式化反馈文本，去掉JSON格式和特殊符号
const formatFeedbackText = (text) => {
  if (!text) return ''

  // 去掉JSON格式
  text = text.replace(/\{[\s\S]*?\}/g, '')
  text = text.replace(/\[[\s\S]*?\]/g, '')

  // 去掉markdown符号
  text = text.replace(/---+/g, '')
  text = text.replace(/\*\*\*/g, '')
  text = text.replace(/\*\*/g, '')
  text = text.replace(/###/g, '')
  text = text.replace(/##/g, '')
  text = text.replace(/#/g, '')

  // 合理分段
  text = text.replace(/([。！？])([^"'"'"\n])/g, '$1\n$2')
  text = text.replace(/\n{3,}/g, '\n\n')

  return text.trim()
}

export default InterviewRoom