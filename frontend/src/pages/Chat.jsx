import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import ChatInterface from '../components/ChatInterface'
import './Chat.css'

function Chat() {
  const navigate = useNavigate()
  const [contextType, setContextType] = useState('general')

  const handleNavigate = (path) => {
    navigate(path)
  }

  return (
    <div className="chat-page">
      <Navbar />
      <div className="chat-container">
        <div className="chat-header">
          <h1 className="page-title">AI 助手</h1>
          <div className="context-tabs">
            <button
              className={`context-tab ${contextType === 'general' ? 'active' : ''}`}
              onClick={() => setContextType('general')}
            >
              通用
            </button>
            <button
              className={`context-tab ${contextType === 'learning' ? 'active' : ''}`}
              onClick={() => setContextType('learning')}
            >
              学习模块
            </button>
            <button
              className={`context-tab ${contextType === 'personalized' ? 'active' : ''}`}
              onClick={() => setContextType('personalized')}
            >
              个性化模块
            </button>
          </div>
        </div>
        <div className="chat-wrapper">
          <ChatInterface contextType={contextType} onNavigate={handleNavigate} />
        </div>
      </div>
    </div>
  )
}

export default Chat