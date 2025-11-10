import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import axios from 'axios'
import './TaskDetail.css'

function TaskDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [task, setTask] = useState(null)
  const [notes, setNotes] = useState([])
  const [highlights, setHighlights] = useState([])
  const [currentNote, setCurrentNote] = useState('')
  const [selectedText, setSelectedText] = useState('')
  const [showNoteModal, setShowNoteModal] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchTaskDetail()
    loadNotes()
    loadHighlights()
  }, [id])

  const fetchTaskDetail = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await axios.get(`http://localhost:8000/api/tasks/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setTask(response.data)
      setLoading(false)
    } catch (error) {
      console.error('获取任务详情失败:', error)
      setLoading(false)
    }
  }

  const loadNotes = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await axios.get(`http://localhost:8000/api/tasks/${id}/notes`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setNotes(response.data.notes || [])
    } catch (error) {
      console.error('加载笔记失败:', error)
    }
  }

  const loadHighlights = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await axios.get(`http://localhost:8000/api/tasks/${id}/highlights`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setHighlights(response.data.highlights || [])
    } catch (error) {
      console.error('加载标注失败:', error)
    }
  }

  const handleTextSelection = () => {
    const selection = window.getSelection()
    const text = selection.toString().trim()
    if (text.length > 0) {
      setSelectedText(text)
      setShowNoteModal(true)
    }
  }

  const saveNote = async () => {
    if (!currentNote.trim()) return

    try {
      const token = localStorage.getItem('token')
      await axios.post(
        `http://localhost:8000/api/tasks/${id}/notes`,
        {
          content: currentNote,
          selected_text: selectedText
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )
      setCurrentNote('')
      setSelectedText('')
      setShowNoteModal(false)
      loadNotes()
    } catch (error) {
      console.error('保存笔记失败:', error)
      alert('保存笔记失败')
    }
  }

  const highlightText = async () => {
    if (!selectedText) return

    try {
      const token = localStorage.getItem('token')
      await axios.post(
        `http://localhost:8000/api/tasks/${id}/highlights`,
        {
          text: selectedText
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )
      setSelectedText('')
      setShowNoteModal(false)
      loadHighlights()
    } catch (error) {
      console.error('标注失败:', error)
    }
  }

  if (loading) {
    return (
      <div className="task-detail-page">
        <Navbar />
        <div className="container">加载中...</div>
      </div>
    )
  }

  if (!task) {
    return (
      <div className="task-detail-page">
        <Navbar />
        <div className="container">任务不存在</div>
      </div>
    )
  }

  return (
    <div className="task-detail-page">
      <Navbar />
      <div className="task-detail-container">
        <div className="task-detail-header">
          <button className="back-button" onClick={() => navigate('/tasks')}>
            ← 返回任务列表
          </button>
          <h1 className="task-detail-title">{task.title}</h1>
        </div>

        <div className="task-detail-content">
          <div className="task-main-content">
            <div className="task-content-wrapper" onMouseUp={handleTextSelection}>
              <div className="task-description">
                <h2>任务描述</h2>
                <div className="content-text" dangerouslySetInnerHTML={{ __html: task.description }} />
              </div>

              {task.content && (
                <div className="task-content">
                  <h2>学习内容</h2>
                  <div className="content-text" dangerouslySetInnerHTML={{ __html: task.content }} />
                </div>
              )}

              {task.resources && task.resources.length > 0 && (
                <div className="task-resources">
                  <h2>学习资源</h2>
                  <ul>
                    {task.resources.map((resource, index) => (
                      <li key={index}>
                        <a href={resource.url || '#'} target="_blank" rel="noopener noreferrer">
                          {resource.title || resource}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>

          <div className="task-sidebar">
            <div className="sidebar-section">
              <h3>我的笔记</h3>
              <button
                className="add-note-button"
                onClick={() => {
                  setSelectedText('')
                  setShowNoteModal(true)
                }}
              >
                + 添加笔记
              </button>
              <div className="notes-list">
                {notes.map((note, index) => (
                  <div key={index} className="note-item">
                    {note.selected_text && (
                      <div className="note-quote">"{note.selected_text}"</div>
                    )}
                    <div className="note-content">{note.content}</div>
                    <div className="note-time">{new Date(note.created_at).toLocaleString()}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="sidebar-section">
              <h3>我的标注</h3>
              <div className="highlights-list">
                {highlights.map((highlight, index) => (
                  <div key={index} className="highlight-item">
                    "{highlight.text}"
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {showNoteModal && (
        <div className="note-modal-overlay" onClick={() => setShowNoteModal(false)}>
          <div className="note-modal" onClick={(e) => e.stopPropagation()}>
            <h3>添加笔记</h3>
            {selectedText && (
              <div className="selected-text-preview">
                选中文本: "{selectedText}"
              </div>
            )}
            <textarea
              className="note-textarea"
              value={currentNote}
              onChange={(e) => setCurrentNote(e.target.value)}
              placeholder="输入你的笔记..."
              rows={6}
            />
            <div className="note-modal-actions">
              {selectedText && (
                <button className="highlight-button" onClick={highlightText}>
                  标注选中文本
                </button>
              )}
              <button className="save-note-button" onClick={saveNote}>
                保存笔记
              </button>
              <button className="cancel-button" onClick={() => setShowNoteModal(false)}>
                取消
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default TaskDetail