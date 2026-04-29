'use client'

import { createContext, useContext, useEffect, useState } from 'react'
import { storage } from '@/lib/storage'

interface AuthContextType {
  studentId: string | null
  teacherId: string | null
  teacherName: string | null
  role: 'student' | 'teacher' | null
  setStudentId: (id: string) => void
  setTeacher: (id: string, name: string) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextType>({
  studentId: null,
  teacherId: null,
  teacherName: null,
  role: null,
  setStudentId: () => {},
  setTeacher: () => {},
  logout: () => {},
})

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [studentId, setStudentIdState] = useState<string | null>(null)
  const [teacherId, setTeacherIdState] = useState<string | null>(null)
  const [teacherName, setTeacherNameState] = useState<string | null>(null)
  const [role, setRoleState] = useState<'student' | 'teacher' | null>(null)

  useEffect(() => {
    const savedRole = storage.getRole()
    setRoleState(savedRole)
    if (savedRole === 'student') {
      setStudentIdState(storage.getStudentId())
    } else if (savedRole === 'teacher') {
      setTeacherIdState(storage.getTeacherId())
      setTeacherNameState(storage.getTeacherName())
    }
  }, [])

  const setStudentId = (id: string) => {
    storage.setStudentId(id)
    storage.setRole('student')
    setStudentIdState(id)
    setRoleState('student')
  }

  const setTeacher = (id: string, name: string) => {
    storage.setTeacherId(id)
    storage.setTeacherName(name)
    storage.setRole('teacher')
    setTeacherIdState(id)
    setTeacherNameState(name)
    setRoleState('teacher')
  }

  const logout = () => {
    storage.clearStudentId()
    storage.clearTeacherId()
    storage.clearRole()
    setStudentIdState(null)
    setTeacherIdState(null)
    setTeacherNameState(null)
    setRoleState(null)
  }

  return (
    <AuthContext.Provider value={{ studentId, teacherId, teacherName, role, setStudentId, setTeacher, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
