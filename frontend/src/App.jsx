import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Tasks from './pages/Tasks'
import Interviews from './pages/Interviews'
import Profile from './pages/Profile'
import Navbar from './components/Navbar'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import './App.css'
import Chat from './pages/Chat'
import Learning from './pages/Learning'
import Personalized from './pages/Personalized'
import TaskDetail from './pages/TaskDetail'
import InterviewRoom from './pages/InterviewRoom'
import FloatingChat from './components/FloatingChat'

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      <div style={{ fontSize: '18px', color: '#666' }}>加载中...</div>
    </div>
  }

  return user ? children : <Navigate to="/login" />
}

function AppRoutes() {
  const { user } = useAuth()

  return (
    <>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        } />
        <Route path="/tasks" element={
          <ProtectedRoute>
            <Tasks />
          </ProtectedRoute>
        } />
        <Route path="/tasks/:id" element={
          <ProtectedRoute>
            <TaskDetail />
          </ProtectedRoute>
        } />
        <Route path="/interviews" element={
          <ProtectedRoute>
            <Interviews />
          </ProtectedRoute>
        } />
        <Route path="/interviews/room/:id" element={
          <ProtectedRoute>
            <InterviewRoom />
          </ProtectedRoute>
        } />
        <Route path="/profile" element={
          <ProtectedRoute>
            <Profile />
          </ProtectedRoute>
        } />
        <Route path="/chat" element={
          <ProtectedRoute>
            <Chat />
          </ProtectedRoute>
        } />
        <Route path="/learning" element={
          <ProtectedRoute>
            <Learning />
          </ProtectedRoute>
        } />
        <Route path="/personalized" element={
          <ProtectedRoute>
            <Personalized />
          </ProtectedRoute>
        } />
      </Routes>
      {user && <FloatingChat contextType="general" />}
    </>
  )
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <AppRoutes />
        </div>
      </Router>
    </AuthProvider>
  )
}

export default App