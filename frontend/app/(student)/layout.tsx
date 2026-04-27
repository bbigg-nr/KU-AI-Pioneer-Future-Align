'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import Sidebar from '@/components/layout/Sidebar'

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  const { studentId } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (studentId === null) {
      router.push('/login')
    }
  }, [studentId, router])

  if (!studentId) return null

  return (
    <div className="flex h-full min-h-screen">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-8 bg-gray-50">
        {children}
      </main>
    </div>
  )
}
