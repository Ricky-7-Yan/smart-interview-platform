import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import './ChatInterface.css'

// API基础URL配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

function ChatInterface({
  contextType = 'general',
  onNavigate,
  isInterviewMode = false,
  questions = [],
  currentQuestionIndex = 0,
  onAnswerSubmit
}) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const [recommendations, setRecommendations] = useState([])
  const [savedSessions, setSavedSessions] = useState([])
  const [showSessionList, setShowSessionList] = useState(false)
  const [sessionName, setSessionName] = useState('')
  const [showSaveDialog, setShowSaveDialog] = useState(false)
  const [hasLoadedHistory, setHasLoadedHistory] = useState(false)
  const [isInitializing, setIsInitializing] = useState(true)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    // 只在首次加载时加载历史，避免重复打招呼
    if (!hasLoadedHistory) {
      loadHistoryAndGreeting()
      setHasLoadedHistory(true)
    }
    loadSavedSessions()
  }, [contextType])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // 当初始化完成后，聚焦输入框
  useEffect(() => {
    if (!isInitializing && inputRef.current) {
      setTimeout(() => {
        inputRef.current?.focus()
      }, 100)
    }
  }, [isInitializing])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const loadHistoryAndGreeting = async () => {
    setIsInitializing(true)
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        // 如果没有token，生成临时sessionId
        const tempSessionId = `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
        setSessionId(tempSessionId)
        const defaultGreetings = {
          learning: '欢迎进入学习模块！我是你的学习导师"学小面"。在这里，我会为你系统地讲解核心知识点，布置有针对性的学习任务，并提供练习题来巩固掌握程度。你现在想学习哪个方向的内容呢？',
          personalized: '欢迎进入个性化模块！我是你的个性化面试顾问"个小面"。在这里，我会基于你的简历提供个性化的面试建议和针对性问题。请先上传你的简历，让我为你定制专属的面试训练方案。',
          general: '你好！我是你的AI助手"小面"，有什么可以帮你的吗？'
        }
        setMessages([{
          role: 'assistant',
          content: defaultGreetings[contextType] || defaultGreetings.general,
          timestamp: new Date()
        }])
        setIsInitializing(false)
        return
      }

      // 先获取或创建会话
      const greetingResponse = await axios.get(`${API_BASE_URL}/chat/greeting`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { context_type: contextType },
        timeout: 10000 // 10秒超时
      })

      setSessionId(greetingResponse.data.session_id)

      // 加载历史消息
      const historyResponse = await axios.get(`${API_BASE_URL}/chat/history/${greetingResponse.data.session_id}`, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 10000
      })

      if (historyResponse.data.history && historyResponse.data.history.length > 0) {
        // 有历史消息，只显示assistant类型的消息，过滤掉错误消息
        const assistantMessages = historyResponse.data.history.filter(
          msg => msg.role === 'assistant' &&
          !msg.content.includes('生成失败') &&
          !msg.content.includes('Connection error') &&
          !msg.content.includes('错误')
        )

        if (assistantMessages.length > 0) {
          // 只显示最后一条assistant消息作为欢迎消息
          const lastMessage = assistantMessages[assistantMessages.length - 1]
          const formattedMessages = [{
            role: lastMessage.role,
            content: formatText(cleanMarkdown(lastMessage.content)),
            timestamp: new Date(lastMessage.created_at)
          }]
          setMessages(formattedMessages)
        } else {
          // 如果没有有效的assistant消息，显示新的欢迎消息
          setMessages([{
            role: 'assistant',
            content: formatText(cleanMarkdown(greetingResponse.data.message)),
            timestamp: new Date()
          }])
        }
      } else {
        // 没有历史消息，显示欢迎消息
        setMessages([{
          role: 'assistant',
          content: formatText(cleanMarkdown(greetingResponse.data.message)),
          timestamp: new Date()
        }])
      }
    } catch (error) {
      console.error('加载历史失败:', error)
      // 出错时显示友好的默认欢迎消息，不显示错误信息
      const defaultGreetings = {
        learning: '欢迎进入学习模块！我是你的学习导师"学小面"。在这里，我会为你系统地讲解核心知识点，布置有针对性的学习任务，并提供练习题来巩固掌握程度。你现在想学习哪个方向的内容呢？',
        personalized: '欢迎进入个性化模块！我是你的个性化面试顾问"个小面"。在这里，我会基于你的简历提供个性化的面试建议和针对性问题。请先上传你的简历，让我为你定制专属的面试训练方案。',
        general: '你好！我是你的AI助手"小面"，有什么可以帮你的吗？'
      }

      // 即使失败也生成临时sessionId，允许用户输入
      const tempSessionId = `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      setSessionId(tempSessionId)

      setMessages([{
        role: 'assistant',
        content: defaultGreetings[contextType] || defaultGreetings.general,
        timestamp: new Date()
      }])
    } finally {
      setIsInitializing(false)
    }
  }

  const loadSavedSessions = async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      const response = await axios.get(`${API_BASE_URL}/chat/sessions`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { context_type: contextType },
        timeout: 10000
      })
      setSavedSessions(response.data.sessions || [])
    } catch (error) {
      console.error('加载会话列表失败:', error)
    }
  }

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

  const sendMessage = async () => {
    if (!input.trim() || loading || isInitializing) return

    // 如果没有sessionId，先尝试获取
    if (!sessionId) {
      await loadHistoryAndGreeting()
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
          timeout: 30000 // 30秒超时
        }
      )

      // 清理和格式化AI回复，确保只返回一条消息
      let cleanedContent = cleanMarkdown(response.data.response)

      // 如果回复中包含多条消息（通过换行或分段），只取第一段
      if (cleanedContent.includes('\n\n')) {
        const paragraphs = cleanedContent.split('\n\n')
        // 如果第一段太短（少于20字），合并前两段
        if (paragraphs[0].length < 20 && paragraphs.length > 1) {
          cleanedContent = paragraphs[0] + '\n\n' + paragraphs[1]
        } else {
          cleanedContent = paragraphs[0]
        }
      }

      cleanedContent = formatText(cleanedContent)

      // 过滤掉错误消息
      if (cleanedContent.includes('生成失败') || cleanedContent.includes('Connection error') || cleanedContent.includes('错误')) {
        cleanedContent = '抱歉，我暂时无法处理这个问题，请稍后再试。'
      }

      const assistantMessage = {
        role: 'assistant',
        content: cleanedContent,
        timestamp: new Date(),
        recommendations: response.data.recommendations || [],
        suggestedActions: response.data.suggested_actions || []
      }

      setMessages(prev => [...prev, assistantMessage])
      setRecommendations(response.data.recommendations || [])
      if (response.data.session_id) {
        setSessionId(response.data.session_id)
      }

      // 如果是面试模式，处理答案提交
      if (isInterviewMode && onAnswerSubmit) {
        onAnswerSubmit(currentInput)
      }
    } catch (error) {
      console.error('发送消息失败:', error)
      let errorMessage = '抱歉，发送消息时出现错误，请稍后重试。'

      if (error.response?.status === 401) {
        errorMessage = '登录已过期，请重新登录'
      } else if (error.code === 'ERR_NETWORK') {
        errorMessage = '网络错误，请检查后端服务是否运行'
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
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

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const saveSession = async () => {
    if (!sessionName.trim()) {
      alert('请输入会话名称')
      return
    }

    try {
      const token = localStorage.getItem('token')
      if (!token) {
        alert('请先登录')
        return
      }

      await axios.post(
        `${API_BASE_URL}/chat/save-session`,
        {
          session_id: sessionId,
          name: sessionName,
          context_type: contextType
        },
        {
          headers: { Authorization: `Bearer ${token}` },
          timeout: 10000
        }
      )
      alert('会话已保存')
      setShowSaveDialog(false)
      setSessionName('')
      loadSavedSessions()
    } catch (error) {
      console.error('保存会话失败:', error)
      alert('保存失败，请重试')
    }
  }

  const loadSession = async (sid) => {
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        alert('请先登录')
        return
      }

      setSessionId(sid)
      const historyResponse = await axios.get(`${API_BASE_URL}/chat/history/${sid}`, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 10000
      })

      if (historyResponse.data.history && historyResponse.data.history.length > 0) {
        // 过滤掉错误消息
        const validMessages = historyResponse.data.history.filter(
          msg => !msg.content.includes('生成失败') &&
          !msg.content.includes('Connection error') &&
          !msg.content.includes('错误')
        )

        const formattedMessages = validMessages.map(msg => ({
          role: msg.role,
          content: formatText(cleanMarkdown(msg.content)),
          timestamp: new Date(msg.created_at)
        }))
        setMessages(formattedMessages)
      }
      setShowSessionList(false)
    } catch (error) {
      console.error('加载会话失败:', error)
      alert('加载会话失败，请重试')
    }
  }

  const handleRecommendationClick = (rec) => {
    if (rec.action === 'navigate' && rec.path) {
      onNavigate?.(rec.path)
    } else if (rec.action === 'practice') {
      setInput(`我想练习${rec.area}相关的问题`)
      // 自动发送
      setTimeout(() => {
        sendMessage()
      }, 100)
    }
  }

  return (
    <div className="chat-interface">
      <div className="chat-header-bar">
        <button
          className="session-button"
          onClick={() => setShowSessionList(!showSessionList)}
        >
          📚 会话历史
        </button>
        <button
          className="session-button"
          onClick={() => setShowSaveDialog(true)}
        >
          💾 保存会话
        </button>
      </div>

      {showSessionList && (
        <div className="session-list-modal">
          <div className="session-list-content">
            <h3>已保存的会话</h3>
            <button className="close-btn" onClick={() => setShowSessionList(false)}>×</button>
            {savedSessions.length === 0 ? (
              <p>暂无保存的会话</p>
            ) : (
              <div className="sessions-list">
                {savedSessions.map(session => (
                  <div
                    key={session.id}
                    className="session-item"
                    onClick={() => loadSession(session.session_id)}
                  >
                    <div className="session-name">{session.name || '未命名会话'}</div>
                    <div className="session-time">{new Date(session.updated_at).toLocaleString()}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {showSaveDialog && (
        <div className="save-dialog-modal">
          <div className="save-dialog-content">
            <h3>保存会话</h3>
            <input
              type="text"
              className="session-name-input"
              value={sessionName}
              onChange={(e) => setSessionName(e.target.value)}
              placeholder="输入会话名称..."
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  saveSession()
                }
              }}
            />
            <div className="save-dialog-actions">
              <button className="save-btn" onClick={saveSession}>保存</button>
              <button className="cancel-btn" onClick={() => {
                setShowSaveDialog(false)
                setSessionName('')
              }}>取消</button>
            </div>
          </div>
        </div>
      )}

      <div className="chat-messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            <div className="message-avatar">
              {msg.role === 'user' ? '👤' : '🤖'}
            </div>
            <div className="message-content">
              <div className="message-text" style={{ whiteSpace: 'pre-wrap' }}>
                {msg.content}
              </div>
              {msg.recommendations && msg.recommendations.length > 0 && (
                <div className="recommendations">
                  {msg.recommendations.map((rec, i) => (
                    <button
                      key={i}
                      className="recommendation-card"
                      onClick={() => handleRecommendationClick(rec)}
                    >
                      <div className="rec-title">{rec.title}</div>
                      <div className="rec-desc">{rec.description}</div>
                    </button>
                  ))}
                </div>
              )}
              {msg.suggestedActions && msg.suggestedActions.length > 0 && (
                <div className="suggested-actions">
                  {msg.suggestedActions.map((action, i) => (
                    <button
                      key={i}
                      className="action-chip"
                      onClick={() => {
                        setInput(action)
                        // 自动聚焦输入框
                        setTimeout(() => {
                          inputRef.current?.focus()
                        }, 100)
                      }}
                    >
                      {action}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="message assistant">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
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

      <div className="chat-input-container">
        <div className="chat-input-wrapper">
          <textarea
            ref={inputRef}
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={isInitializing ? "初始化中，请稍候..." : "输入消息..."}
            rows={1}
            disabled={loading || isInitializing}
            autoFocus={!isInitializing}
          />
          <button
            className="send-button"
            onClick={sendMessage}
            disabled={!input.trim() || loading || isInitializing}
            title={isInitializing ? "初始化中..." : "发送"}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M22 2L11 13M22 2L15 22L11 13M22 2L2 9L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}

export default ChatInterface