'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import { api } from '@/lib/api'
import { GraduationCap, Loader2 } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'

export default function LoginPage() {
  const [studentId, setStudentId] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { setStudentId: saveStudentId } = useAuth()
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (password !== '1234') {
      setError('Incorrect password.')
      return
    }

    if (!studentId.trim()) {
      setError('Please enter your Student ID.')
      return
    }

    setLoading(true)
    try {
      await api.getStudent(studentId.trim().toUpperCase())
      saveStudentId(studentId.trim().toUpperCase())
      router.push('/')
    } catch {
      setError('Student ID not found. Please check and try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#1a1f2e]">
      <div className="w-full max-w-md">
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-indigo-500 flex items-center justify-center mb-4">
            <GraduationCap size={28} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">FutureAlign</h1>
          <p className="text-white/50 text-sm mt-1">Career Guidance Platform</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-white/5 border border-white/10 rounded-2xl p-8 space-y-5"
        >
          <div className="space-y-2">
            <Label className="text-white/80 text-sm">Student ID</Label>
            <Input
              placeholder="e.g. STU001"
              value={studentId}
              onChange={e => setStudentId(e.target.value)}
              className="bg-white/10 border-white/20 text-white placeholder:text-white/30 focus:border-indigo-400"
              autoFocus
            />
          </div>

          <div className="space-y-2">
            <Label className="text-white/80 text-sm">Password</Label>
            <Input
              type="password"
              placeholder="••••"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="bg-white/10 border-white/20 text-white placeholder:text-white/30 focus:border-indigo-400"
            />
          </div>

          {error && (
            <p className="text-red-400 text-sm bg-red-400/10 rounded-lg px-3 py-2">{error}</p>
          )}

          <Button
            type="submit"
            disabled={loading}
            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white"
          >
            {loading ? <Loader2 size={16} className="animate-spin mr-2" /> : null}
            {loading ? 'Signing in…' : 'Sign in'}
          </Button>
        </form>

        <p className="text-center text-white/30 text-xs mt-6">
          KU AI Career Matcher · FutureAlign
        </p>
      </div>
    </div>
  )
}
