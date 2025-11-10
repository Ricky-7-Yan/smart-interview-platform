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
  const [learningContent, setLearningContent] = useState(null)

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

      // 根据任务类型加载实际学习内容
      if (response.data.task_type === 'algorithm') {
        loadLeetCodeProblem()
      } else if (response.data.task_type === 'project') {
        loadProjectContent()
      }

      setLoading(false)
    } catch (error) {
      console.error('获取任务详情失败:', error)
      setLoading(false)
    }
  }

  const loadLeetCodeProblem = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await axios.get(`http://localhost:8000/api/tasks/${id}/leetcode`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setLearningContent(response.data)
    } catch (error) {
      // 如果API失败，使用示例题目
      setLearningContent({
        title: "两数之和",
        difficulty: "简单",
        description: "给定一个整数数组 nums 和一个整数目标值 target，请你在该数组中找出 和为目标值 target  的那 两个 整数，并返回它们的数组下标。",
        examples: [
          {
            input: "nums = [2,7,11,15], target = 9",
            output: "[0,1]",
            explanation: "因为 nums[0] + nums[1] == 9 ，返回 [0, 1] 。"
          }
        ],
        constraints: [
          "2 <= nums.length <= 10^4",
          "-10^9 <= nums[i] <= 10^9",
          "-10^9 <= target <= 10^9"
        ],
        leetcodeUrl: "https://leetcode.cn/problems/two-sum/"
      })
    }
  }

  const loadProjectContent = async () => {
    setLearningContent({
      type: 'project',
      content: '项目实践内容...'
    })
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
    if (!currentNote.trim()) {
      alert('请输入笔记内容')
      return
    }

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
      // 重新加载笔记列表
      await loadNotes()
      alert('笔记已保存')
    } catch (error) {
      console.error('保存笔记失败:', error)
      alert('保存笔记失败')
    }
  }

  const highlightText = async () => {
    if (!selectedText) {
      alert('请先选择要标注的文本')
      return
    }

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
      // 重新加载标注列表
      await loadHighlights()
      alert('标注已保存')
    } catch (error) {
      console.error('标注失败:', error)
      alert('标注失败')
    }
  }

  const deleteNote = async (noteId) => {
    if (!window.confirm('确定要删除这条笔记吗？')) return

    try {
      const token = localStorage.getItem('token')
      await axios.delete(`http://localhost:8000/api/tasks/${id}/notes/${noteId}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      await loadNotes()
      alert('笔记已删除')
    } catch (error) {
      console.error('删除笔记失败:', error)
      alert('删除失败')
    }
  }

  const deleteHighlight = async (highlightId) => {
    if (!window.confirm('确定要删除这条标注吗？')) return

    try {
      const token = localStorage.getItem('token')
      await axios.delete(`http://localhost:8000/api/tasks/${id}/highlights/${highlightId}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      await loadHighlights()
      alert('标注已删除')
    } catch (error) {
      console.error('删除标注失败:', error)
      alert('删除失败')
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
                <div className="content-text" dangerouslySetInnerHTML={{ __html: task.description || task.title }} />
              </div>

              {/* LeetCode题目内容 */}
              {learningContent && learningContent.title && (
                <div className="leetcode-problem">
                  <div className="problem-header">
                    <h2>{learningContent.title}</h2>
                    <span className={`difficulty-badge ${learningContent.difficulty?.toLowerCase()}`}>
                      {learningContent.difficulty}
                    </span>
                    {learningContent.leetcodeUrl && (
                      <a
                        href={learningContent.leetcodeUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="leetcode-link"
                      >
                        在LeetCode上查看 →
                      </a>
                    )}
                  </div>

                  <div className="problem-description">
                    <h3>题目描述</h3>
                    <p>{learningContent.description}</p>
                  </div>

                  {learningContent.examples && learningContent.examples.length > 0 && (
                    <div className="problem-examples">
                      <h3>示例</h3>
                      {learningContent.examples.map((example, index) => (
                        <div key={index} className="example-item">
                          <div className="example-label">示例 {index + 1}:</div>
                          <div className="example-content">
                            <div><strong>输入:</strong> {example.input}</div>
                            <div><strong>输出:</strong> {example.output}</div>
                            {example.explanation && (
                              <div><strong>解释:</strong> {example.explanation}</div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {learningContent.constraints && learningContent.constraints.length > 0 && (
                    <div className="problem-constraints">
                      <h3>提示</h3>
                      <ul>
                        {learningContent.constraints.map((constraint, index) => (
                          <li key={index}>{constraint}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="code-editor-section">
                    <h3>代码编辑器</h3>
                    <div className="code-editor">
                      <textarea
                        className="code-textarea"
                        placeholder="在这里编写你的代码..."
                        rows={15}
                      />
                    </div>
                    <div className="editor-actions">
                      <button className="run-button">运行代码</button>
                      <button className="submit-button">提交答案</button>
                    </div>
                  </div>
                </div>
              )}

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
                {notes.length === 0 ? (
                  <p className="empty-hint">暂无笔记</p>
                ) : (
                  notes.map((note) => (
                    <div key={note.id} className="note-item">
                      {note.selected_text && (
                        <div className="note-quote">"{note.selected_text}"</div>
                      )}
                      <div className="note-content">{note.content}</div>
                      <div className="note-footer">
                        <div className="note-time">{new Date(note.created_at).toLocaleString()}</div>
                        <button
                          className="delete-note-btn"
                          onClick={() => deleteNote(note.id)}
                        >
                          删除
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="sidebar-section">
              <h3>我的标注</h3>
              <div className="highlights-list">
                {highlights.length === 0 ? (
                  <p className="empty-hint">暂无标注</p>
                ) : (
                  highlights.map((highlight) => (
                    <div key={highlight.id} className="highlight-item">
                      <div className="highlight-text">"{highlight.text}"</div>
                      <div className="highlight-footer">
                        <div className="highlight-time">{new Date(highlight.created_at).toLocaleString()}</div>
                        <button
                          className="delete-highlight-btn"
                          onClick={() => deleteHighlight(highlight.id)}
                        >
                          删除
                        </button>
                      </div>
                    </div>
                  ))
                )}
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
              <button className="cancel-button" onClick={() => {
                setShowNoteModal(false)
                setCurrentNote('')
                setSelectedText('')
              }}>
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