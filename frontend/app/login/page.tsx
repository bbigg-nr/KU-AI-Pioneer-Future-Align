'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import { api } from '@/lib/api'
import { GraduationCap, Loader2 } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import Link from 'next/link'

type Role = 'student' | 'teacher'

const TEACHER_PASSWORD = 'advisor1234'
const STUDENT_PASSWORD = '1234'

export default function LoginPage() {
  const [role, setRole] = useState<Role>('student')
  const [userId, setUserId] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { setStudentId, setTeacher } = useAuth()
  const router = useRouter()

  const handleRoleSwitch = (r: Role) => {
    setRole(r)
    setError('')
    setUserId('')
    setPassword('')
  }

  const handleSubmit = async (e: React.SyntheticEvent) => {
    e.preventDefault()
    setError('')

    const id = userId.trim().toUpperCase()
    if (!id) {
      setError(role === 'student' ? 'Please enter your Student ID.' : 'Please enter your Teacher ID.')
      return
    }

    const expectedPassword = role === 'student' ? STUDENT_PASSWORD : TEACHER_PASSWORD
    if (password !== expectedPassword) {
      setError('Incorrect password.')
      return
    }

    setLoading(true)
    try {
      if (role === 'student') {
        await api.getStudent(id)
        setStudentId(id)
        router.push('/')
      } else {
        const teacher = await api.getTeacher(id)
        setTeacher(id, teacher.name)
        router.push('/coach')
      }
    } catch {
      setError(role === 'student' ? 'Student ID not found. Please check and try again.' : 'Teacher ID not found. Please check and try again.')
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

        <div className="flex bg-white/5 border border-white/10 rounded-xl p-1 mb-4">
          {(['student', 'teacher'] as Role[]).map(r => (
            <button
              key={r}
              onClick={() => handleRoleSwitch(r)}
              className={cn(
                'flex-1 py-2 rounded-lg text-sm font-medium transition-colors',
                role === r
                  ? 'bg-indigo-600 text-white'
                  : 'text-white/50 hover:text-white/80'
              )}
            >
              {r === 'student' ? 'นิสิต' : 'อาจารย์'}
            </button>
          ))}
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-white/5 border border-white/10 rounded-2xl p-8 space-y-5"
        >
          <div className="space-y-2">
            <Label className="text-white/80 text-sm">
              {role === 'student' ? 'Student ID' : 'Teacher ID'}
            </Label>
            <Input
              placeholder={role === 'student' ? 'e.g. 6610400000' : 'e.g. PROF001'}
              value={userId}
              onChange={e => setUserId(e.target.value)}
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
          
          {role === 'student' && (
            <div className="text-center mt-4">
              <Link href="/register" className="text-indigo-400 hover:text-indigo-300 text-sm">
                New student? Create a profile
              </Link>
            </div>
          )}
        </form>

        <p className="text-center text-white/30 text-xs mt-6">
          KU AI Career Matcher · FutureAlign
        </p>
      </div>
    </div>
  )
}
