'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import { api } from '@/lib/api'
import type { Student, SkillItem } from '@/lib/types'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import SkillsInput from '@/components/profile/SkillsInput'
import LanguagesInput from '@/components/profile/LanguagesInput'
import ExtractFromText from '@/components/profile/ExtractFromText'
import { User, BookOpen, Wrench, Loader2, CheckCircle2 } from 'lucide-react'

export default function ProfilePage() {
  const { studentId } = useAuth()
  const [student, setStudent] = useState<Student | null>(null)
  const [skills, setSkills] = useState<SkillItem[]>([])
  const [languages, setLanguages] = useState<SkillItem[]>([])
  const [activities, setActivities] = useState<string[]>([])
  const [actInput, setActInput] = useState('')
  const [loading, setLoading] = useState(true)
  const [saved, setSaved] = useState(false)

  const router = useRouter()
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    if (!studentId) return
    api.getStudent(studentId).then(s => {
      setStudent(s)
      setSkills(s.skills || [])
      setLanguages(s.languages || [])
      setActivities(s.activities ? s.activities.split(' | ').filter(Boolean) : [])
    }).finally(() => setLoading(false))
  }, [studentId])

  const handleSave = async () => {
    if (!studentId) return
    setSaving(true)
    try {
      await api.updateStudent(studentId, {
        skills,
        languages,
        activities: activities.join(' | ')
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } catch (e) {
      console.error(e)
      alert('Failed to save profile')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!studentId) return
    if (!confirm('Are you sure you want to delete your profile? This cannot be undone.')) return
    
    setDeleting(true)
    try {
      await api.deleteStudent(studentId)
      alert('Profile deleted.')
      router.push('/login')
    } catch (e) {
      console.error(e)
      alert('Failed to delete profile')
      setDeleting(false)
    }
  }

  const handleMergeExtracted = (newSkills: SkillItem[], newActivities: string[]) => {
    if (newSkills.length > 0) {
      setSkills(prev => {
        const merged = [...prev]
        for (const s of newSkills) {
          if (!merged.some(e => e.name.toLowerCase() === s.name.toLowerCase())) {
            merged.push(s)
          }
        }
        return merged
      })
    }
    if (newActivities.length > 0) {
      setActivities(prev => {
        const merged = [...prev]
        for (const a of newActivities) {
          if (!merged.includes(a)) merged.push(a)
        }
        return merged
      })
    }
  }

  const addActivity = () => {
    const v = actInput.trim()
    if (v && !activities.includes(v)) {
      setActivities([...activities, v])
      setActInput('')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-indigo-500" size={32} />
      </div>
    )
  }

  if (!student) return null

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Student Profile</h1>
        <p className="text-gray-500 text-sm mt-1">Fill in your details to get personalized career guidance</p>
      </div>

      <div className="space-y-6">
        <Section title="Basic Information" icon={<User size={16} className="text-indigo-500" />}>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Full Name">
              <Input value={student.name} readOnly className="bg-gray-50" />
            </Field>
            <Field label="Education Level">
              <Input value="Bachelor's Degree" readOnly className="bg-gray-50" />
            </Field>
            <Field label="Major / Field of Study">
              <Input value={student.faculty} readOnly className="bg-gray-50" />
            </Field>
            <Field label="GPA">
              <Input value={student.gpa} readOnly className="bg-gray-50" />
            </Field>
          </div>
          <p className="text-xs text-gray-400 mt-2">Basic info is loaded from your student record and is read-only.</p>
        </Section>

        <Section title="Skills & Experience" icon={<Wrench size={16} className="text-indigo-500" />}>
          <ExtractFromText
            existingSkills={skills}
            existingActivities={activities}
            onMerge={handleMergeExtracted}
          />
          <div className="mt-4">
            <SkillsInput skills={skills} onChange={setSkills} />
          </div>
        </Section>

        <Section title="Languages" icon={<BookOpen size={16} className="text-indigo-500" />}>
          <LanguagesInput languages={languages} onChange={setLanguages} />
        </Section>

        <Section title="Activities & Projects" icon={<BookOpen size={16} className="text-indigo-500" />}>
          <div className="flex gap-2 mb-3">
            <Input
              value={actInput}
              onChange={e => setActInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addActivity())}
              placeholder="e.g. Team Lead at [KU Hackathon 2026]"
            />
            <Button onClick={addActivity} variant="outline">Add</Button>
          </div>
          <div className="flex flex-wrap gap-2">
            {activities.map(a => (
              <span
                key={a}
                className="flex items-center gap-1 text-xs bg-indigo-50 text-indigo-700 border border-indigo-200 rounded-full px-3 py-1"
              >
                {a}
                <button onClick={() => setActivities(activities.filter(x => x !== a))} className="ml-1 text-indigo-400 hover:text-indigo-700">×</button>
              </span>
            ))}
          </div>
          <p className="text-xs text-gray-400 mt-2">Format: [Role] at [Project]</p>
        </Section>
      </div>

      <div className="flex justify-between items-center mt-8 pt-6 border-t border-gray-200">
        <Button
          onClick={handleDelete}
          disabled={deleting}
          variant="destructive"
          className="text-white px-6"
        >
          {deleting ? 'Deleting...' : 'Delete Profile'}
        </Button>
        <Button
          onClick={handleSave}
          disabled={saving}
          className="bg-indigo-600 hover:bg-indigo-500 text-white px-8"
        >
          {saving ? <Loader2 className="animate-spin mr-2" size={16} /> : null}
          {saved ? (
            <><CheckCircle2 size={16} className="mr-2" /> Saved!</>
          ) : 'Save Profile'}
        </Button>
      </div>
    </div>
  )
}

function Section({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
      <div className="flex items-center gap-2 mb-5 pb-4 border-b border-gray-100">
        {icon}
        <h2 className="font-semibold text-gray-900">{title}</h2>
      </div>
      {children}
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <Label className="text-sm text-gray-600">{label}</Label>
      {children}
    </div>
  )
}
