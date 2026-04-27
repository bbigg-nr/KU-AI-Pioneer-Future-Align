'use client'

import { createContext, useContext, useEffect, useState } from 'react'
import { storage } from '@/lib/storage'

interface AuthContextType {
  studentId: string | null
  setStudentId: (id: string) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextType>({
  studentId: null,
  setStudentId: () => {},
  logout: () => {},
})

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [studentId, setStudentIdState] = useState<string | null>(null)

  useEffect(() => {
    setStudentIdState(storage.getStudentId())
  }, [])

  const setStudentId = (id: string) => {
    storage.setStudentId(id)
    setStudentIdState(id)
  }

  const logout = () => {
    storage.clearStudentId()
    setStudentIdState(null)
  }

  return (
    <AuthContext.Provider value={{ studentId, setStudentId, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
