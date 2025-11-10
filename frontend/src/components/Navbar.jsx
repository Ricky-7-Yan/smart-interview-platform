import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import './Navbar.css'

function Navbar() {
  const { user, logout } = useAuth()
  const location = useLocation()

  const isActive = (path) => location.pathname === path

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-logo">
          智能面试平台
        </Link>

        <div className="navbar-links">
          <Link
            to="/"
            className={isActive('/') ? 'nav-link active' : 'nav-link'}
          >
            仪表盘
          </Link>
          <Link
            to="/learning"
            className={isActive('/learning') ? 'nav-link active' : 'nav-link'}
          >
            学习模块
          </Link>
          <Link
            to="/personalized"
            className={isActive('/personalized') ? 'nav-link active' : 'nav-link'}
          >
            个性化
          </Link>
          <Link
            to="/tasks"
            className={isActive('/tasks') ? 'nav-link active' : 'nav-link'}
          >
            任务
          </Link>
          <Link
            to="/interviews"
            className={isActive('/interviews') ? 'nav-link active' : 'nav-link'}
          >
            面试
          </Link>
          <Link
            to="/profile"
            className={isActive('/profile') ? 'nav-link active' : 'nav-link'}
          >
            个人中心
          </Link>
        </div>

        <div className="navbar-user">
          <span className="user-name">{user?.username}</span>
          <button className="logout-btn" onClick={logout}>退出</button>
        </div>
      </div>
    </nav>
  )
}

export default Navbar