'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'
import { GraduationCap, Loader2 } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import Link from 'next/link'

export default function RegisterPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const [formData, setFormData] = useState({
    student_id: '',
    name: '',
    faculty: '',
    year: '1',
    gpa: '',
    target_career: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)

    try {
      await api.createStudent({
        student_id: formData.student_id.trim(),
        name: formData.name.trim(),
        faculty: formData.faculty.trim(),
        year: parseInt(formData.year),
        gpa: parseFloat(formData.gpa),
        target_career: formData.target_career.trim(),
        skills: [],
        languages: [{ name: 'Thai', level: 'Native' }],
        activities: '',
        key_course_grades: []
      } as any) // Typecast for simplicity
      setSuccess('Profile created successfully! Redirecting to login...')
      setTimeout(() => {
        router.push('/login')
      }, 2000)
    } catch (err: any) {
      setError(err.message || 'Failed to create profile. Student ID might already exist.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#1a1f2e] py-12">
      <div className="w-full max-w-md">
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-indigo-500 flex items-center justify-center mb-4">
            <GraduationCap size={28} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">FutureAlign</h1>
          <p className="text-white/50 text-sm mt-1">Create Student Profile</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-white/5 border border-white/10 rounded-2xl p-8 space-y-5"
        >
          <div className="space-y-2">
            <Label className="text-white/80 text-sm">Student ID</Label>
            <Input
              required
              placeholder="e.g. 6610499999"
              value={formData.student_id}
              onChange={e => setFormData({ ...formData, student_id: e.target.value })}
              className="bg-white/10 border-white/20 text-white placeholder:text-white/30 focus:border-indigo-400"
            />
          </div>

          <div className="space-y-2">
            <Label className="text-white/80 text-sm">Full Name</Label>
            <Input
              required
              placeholder="e.g. John Doe"
              value={formData.name}
              onChange={e => setFormData({ ...formData, name: e.target.value })}
              className="bg-white/10 border-white/20 text-white placeholder:text-white/30 focus:border-indigo-400"
            />
          </div>

          <div className="space-y-2">
            <Label className="text-white/80 text-sm">Faculty</Label>
            <Input
              required
              placeholder="e.g. Computer Engineering"
              value={formData.faculty}
              onChange={e => setFormData({ ...formData, faculty: e.target.value })}
              className="bg-white/10 border-white/20 text-white placeholder:text-white/30 focus:border-indigo-400"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-white/80 text-sm">Year</Label>
              <Input
                required
                type="number"
                min="1"
                max="6"
                value={formData.year}
                onChange={e => setFormData({ ...formData, year: e.target.value })}
                className="bg-white/10 border-white/20 text-white placeholder:text-white/30 focus:border-indigo-400"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-white/80 text-sm">GPA</Label>
              <Input
                required
                type="number"
                step="0.01"
                min="0"
                max="4"
                placeholder="e.g. 3.50"
                value={formData.gpa}
                onChange={e => setFormData({ ...formData, gpa: e.target.value })}
                className="bg-white/10 border-white/20 text-white placeholder:text-white/30 focus:border-indigo-400"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label className="text-white/80 text-sm">Target Career (Optional)</Label>
            <Input
              placeholder="e.g. Software Engineer"
              value={formData.target_career}
              onChange={e => setFormData({ ...formData, target_career: e.target.value })}
              className="bg-white/10 border-white/20 text-white placeholder:text-white/30 focus:border-indigo-400"
            />
          </div>

          {error && (
            <p className="text-red-400 text-sm bg-red-400/10 rounded-lg px-3 py-2">{error}</p>
          )}
          
          {success && (
            <p className="text-green-400 text-sm bg-green-400/10 rounded-lg px-3 py-2">{success}</p>
          )}

          <Button
            type="submit"
            disabled={loading}
            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white"
          >
            {loading ? <Loader2 size={16} className="animate-spin mr-2" /> : null}
            {loading ? 'Creating...' : 'Create Profile'}
          </Button>

          <div className="text-center mt-4">
            <Link href="/login" className="text-indigo-400 hover:text-indigo-300 text-sm">
              Already have an account? Sign in
            </Link>
          </div>
        </form>
      </div>
    </div>
  )
}
