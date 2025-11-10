import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import './FloatingChat.css'

// API基础URL配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

function FloatingChat({ contextType = 'general' }) {
  const [isOpen, setIsOpen] = useState(false)
  const [isMinimized, setIsMinimized] = useState(false)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const [isInitializing, setIsInitializing] = useState(false)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 })
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const windowRef = useRef(null)

  useEffect(() => {
    if (isOpen && !sessionId && !isInitializing) {
      loadGreeting()
    }
  }, [isOpen, contextType])

  useEffect(() => {
    if (isOpen) {
      scrollToBottom()
    }
  }, [messages, isOpen])

  // 初始化位置（右下角）
  useEffect(() => {
    if (isOpen && windowRef.current) {
      const rect = windowRef.current.getBoundingClientRect()
      setPosition({
        x: window.innerWidth - rect.width - 24,
        y: window.innerHeight - rect.height - 24
      })
    }
  }, [isOpen])

  // 处理窗口大小变化
  useEffect(() => {
    const handleResize = () => {
      if (windowRef.current && isOpen) {
        const rect = windowRef.current.getBoundingClientRect()
        const newX = Math.min(
          position.x,
          window.innerWidth - rect.width - 24
        )
        const newY = Math.min(
          position.y,
          window.innerHeight - rect.height - 24
        )
        setPosition({ x: Math.max(0, newX), y: Math.max(0, newY) })
      }
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [isOpen, position])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const loadGreeting = async () => {
    setIsInitializing(true)
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        // 如果没有token，生成一个临时sessionId
        const tempSessionId = `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
        setSessionId(tempSessionId)
        setMessages([{
          role: 'assistant',
          content: '你好！我是你的AI助手，有什么可以帮你的吗？',
          timestamp: new Date()
        }])
        setIsInitializing(false)
        return
      }

      const response = await axios.get(`${API_BASE_URL}/chat/greeting`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { context_type: contextType },
        timeout: 10000
      })

      setSessionId(response.data.session_id)
      setMessages([{
        role: 'assistant',
        content: response.data.message,
        timestamp: new Date()
      }])
    } catch (error) {
      console.error('加载欢迎消息失败:', error)
      // 即使失败也生成一个临时sessionId，允许用户输入
      const tempSessionId = `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      setSessionId(tempSessionId)
      setMessages([{
        role: 'assistant',
        content: '你好！我是你的AI助手，有什么可以帮你的吗？',
        timestamp: new Date()
      }])
    } finally {
      setIsInitializing(false)
    }
  }

  // 拖拽开始
  const handleDragStart = (e) => {
    if (e.button !== 0) return // 只处理左键
    e.preventDefault()
    setIsDragging(true)

    if (windowRef.current) {
      const rect = windowRef.current.getBoundingClientRect()
      setDragOffset({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      })
    }
  }

  // 拖拽中
  const handleDrag = (e) => {
    if (!isDragging) return

    e.preventDefault()

    if (windowRef.current) {
      const rect = windowRef.current.getBoundingClientRect()
      const newX = e.clientX - dragOffset.x
      const newY = e.clientY - dragOffset.y

      // 限制在窗口内
      const maxX = window.innerWidth - rect.width
      const maxY = window.innerHeight - rect.height

      setPosition({
        x: Math.max(0, Math.min(newX, maxX)),
        y: Math.max(0, Math.min(newY, maxY))
      })
    }
  }

  // 拖拽结束
  const handleDragEnd = () => {
    setIsDragging(false)
  }

  // 添加全局事件监听器
  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleDrag)
      document.addEventListener('mouseup', handleDragEnd)

      return () => {
        document.removeEventListener('mousemove', handleDrag)
        document.removeEventListener('mouseup', handleDragEnd)
      }
    }
  }, [isDragging, dragOffset])

  const sendMessage = async () => {
    if (!input.trim() || loading || isInitializing) return

    // 如果没有sessionId，先尝试获取
    if (!sessionId) {
      await loadGreeting()
      // 如果还是没有sessionId，生成临时ID
      if (!sessionId) {
        const tempSessionId = `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
        setSessionId(tempSessionId)
      }
    }

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    const currentInput = input
    setInput('')
    setLoading(true)

    try {
      const token = localStorage.getItem('token')
      if (!token) {
        throw new Error('未登录，请先登录')
      }

      const response = await axios.post(
        `${API_BASE_URL}/chat/message`,
        {
          message: currentInput,
          session_id: sessionId,
          context_type: contextType
        },
        {
          headers: { Authorization: `Bearer ${token}` },
          timeout: 30000
        }
      )

      // 清理AI回复中的markdown符号并格式化
      let cleanedContent = cleanMarkdown(response.data.response)

      // 确保只返回一条消息
      if (cleanedContent.includes('\n\n')) {
        const paragraphs = cleanedContent.split('\n\n')
        if (paragraphs[0].length < 50 && paragraphs.length > 1) {
          cleanedContent = paragraphs[0] + '\n\n' + paragraphs[1]
        } else {
          cleanedContent = paragraphs[0]
        }
      }

      cleanedContent = formatText(cleanedContent)

      // 过滤错误消息
      if (cleanedContent.includes('生成失败') || cleanedContent.includes('Connection error') || cleanedContent.includes('错误')) {
        cleanedContent = '抱歉，我暂时无法处理这个问题，请稍后再试。'
      }

      const assistantMessage = {
        role: 'assistant',
        content: cleanedContent,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
      if (response.data.session_id) {
        setSessionId(response.data.session_id)
      }
    } catch (error) {
      console.error('发送消息失败:', error)
      let errorMessage = '抱歉，发送消息时出现错误，请稍后重试。'

      if (error.response?.status === 401) {
        errorMessage = '登录已过期，请重新登录'
      } else if (error.code === 'ERR_NETWORK') {
        errorMessage = '网络错误，请检查后端服务是否运行'
      }

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: errorMessage,
        timestamp: new Date(),
        error: true
      }])
    } finally {
      setLoading(false)
      // 延迟聚焦，确保DOM已更新
      setTimeout(() => {
        inputRef.current?.focus()
      }, 100)
    }
  }

  // 清理markdown符号
  const cleanMarkdown = (text) => {
    if (!text) return ''
    return text
      .replace(/---+/g, '')
      .replace(/\*\*\*/g, '')
      .replace(/\*\*/g, '')
      .replace(/###/g, '')
      .replace(/##/g, '')
      .replace(/#/g, '')
      .replace(/\*\s/g, '')
      .trim()
  }

  // 格式化文本，合理分段
  const formatText = (text) => {
    if (!text) return ''
    // 在"第一部分"、"第二部分"等地方换行
    text = text.replace(/(第[一二三四五六七八九十\d]+部分[：:])/g, '\n\n$1\n')
    // 在数字编号后换行
    text = text.replace(/(\d+[、.])/g, '\n$1')
    // 在句号、问号、感叹号后换行（如果后面不是引号）
    text = text.replace(/([。！？])([^"\'\n])/g, '$1\n$2')
    // 清理多余的空行
    text = text.replace(/\n{3,}/g, '\n\n')
    return text.trim()
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  if (!isOpen) {
    return (
      <button
        className="floating-chat-button"
        onClick={() => setIsOpen(true)}
        title="打开AI助手"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path d="M20 2H4C2.9 2 2 2.9 2 4V22L6 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        <span className="floating-button-text">AI助手</span>
      </button>
    )
  }

  return (
    <div
      ref={windowRef}
      className={`floating-chat-window ${isMinimized ? 'minimized' : ''} ${isDragging ? 'dragging' : ''}`}
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
        right: 'auto',
        bottom: 'auto'
      }}
    >
      <div
        className="floating-chat-header"
        onMouseDown={handleDragStart}
      >
        <div className="chat-header-title">
          <span className="chat-avatar">🤖</span>
          <span>AI助手</span>
        </div>
        <div className="chat-header-actions">
          <button
            className="header-button"
            onClick={(e) => {
              e.stopPropagation()
              setIsMinimized(!isMinimized)
            }}
            title={isMinimized ? "展开" : "最小化"}
          >
            {isMinimized ? '□' : '—'}
          </button>
          <button
            className="header-button"
            onClick={(e) => {
              e.stopPropagation()
              setIsOpen(false)
              setIsMinimized(false)
            }}
            title="关闭"
          >
            ×
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          <div className="floating-chat-messages">
            {messages.map((msg, index) => (
              <div key={index} className={`floating-message ${msg.role}`}>
                <div className="floating-message-avatar">
                  {msg.role === 'user' ? '👤' : '🤖'}
                </div>
                <div className={`floating-message-content ${msg.error ? 'error' : ''}`}>
                  <div className="message-text-formatted" dangerouslySetInnerHTML={{ __html: formatMessageText(msg.content) }} />
                </div>
              </div>
            ))}
            {loading && (
              <div className="floating-message assistant">
                <div className="floating-message-avatar">🤖</div>
                <div className="floating-message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="floating-chat-input">
            <input
              ref={inputRef}
              className="floating-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={isInitializing ? "初始化中..." : "输入消息..."}
              disabled={loading || isInitializing}
              autoFocus
            />
            <button
              className="floating-send-button"
              onClick={sendMessage}
              disabled={!input.trim() || loading || isInitializing}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <path d="M22 2L11 13M22 2L15 22L11 13M22 2L2 9L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>
        </>
      )}
    </div>
  )
}

// 格式化消息文本为HTML
const formatMessageText = (text) => {
  if (!text) return ''
  // 将换行转换为<br>
  return text.split('\n').map((line, i) => {
    if (line.trim() === '') return '<br/>'
    return `<div style="margin-bottom: 8px;">${line}</div>`
  }).join('')
}

export default FloatingChat