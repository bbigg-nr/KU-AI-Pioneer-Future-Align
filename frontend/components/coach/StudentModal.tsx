import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import type { Student, SkillItem } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { X, Plus, Trash2, Loader2 } from 'lucide-react'

interface StudentModalProps {
  isOpen: boolean
  onClose: () => void
  onSave: (student: Student) => void
  initialData?: Student | null
}

const DEFAULT_STUDENT: Student = {
  student_id: '',
  name: '',
  faculty: 'Engineering',
  year: 1,
  gpa: 0,
  skills: [],
  languages: [],
  target_career: '',
  activities: ''
}

export default function StudentModal({ isOpen, onClose, onSave, initialData }: StudentModalProps) {
  const [formData, setFormData] = useState<Student>(DEFAULT_STUDENT)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (isOpen) {
      if (initialData) {
        setFormData(initialData)
      } else {
        setFormData({ ...DEFAULT_STUDENT, student_id: `6610400${Math.floor(Math.random() * 900 + 100)}` })
      }
      setError('')
    }
  }, [isOpen, initialData])

  if (!isOpen) return null

  const handleChange = (field: keyof Student, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleSkillChange = (type: 'skills' | 'languages', index: number, field: keyof SkillItem, value: string) => {
    const updated = [...formData[type]]
    updated[index] = { ...updated[index], [field]: value } as SkillItem
    setFormData(prev => ({ ...prev, [type]: updated }))
  }

  const addSkill = (type: 'skills' | 'languages') => {
    setFormData(prev => ({ ...prev, [type]: [...prev[type], { name: '', level: 'Beginner' }] }))
  }

  const removeSkill = (type: 'skills' | 'languages', index: number) => {
    const updated = [...formData[type]]
    updated.splice(index, 1)
    setFormData(prev => ({ ...prev, [type]: updated }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.student_id || !formData.name) {
      setError('Student ID and Name are required')
      return
    }

    setLoading(true)
    setError('')
    try {
      if (initialData) {
        const res = await api.updateStudent(formData.student_id, formData)
        onSave(res.student)
      } else {
        const res = await api.createStudent(formData)
        onSave(res.student)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to save student')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="bg-white rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden shadow-2xl">
        <div className="flex justify-between items-center p-4 border-b border-gray-100">
          <h2 className="text-xl font-bold text-gray-900">{initialData ? 'Edit Student' : 'Create New Student'}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-700">
            <X size={20} />
          </button>
        </div>

        <div className="p-6 overflow-y-auto flex-1">
          {error && <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-lg text-sm">{error}</div>}
          
          <form id="student-form" onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Student ID</label>
                <Input 
                  value={formData.student_id} 
                  onChange={e => handleChange('student_id', e.target.value)} 
                  disabled={!!initialData}
                  placeholder="e.g. 6610400000"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Name</label>
                <Input 
                  value={formData.name} 
                  onChange={e => handleChange('name', e.target.value)} 
                  placeholder="e.g. John Doe"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Faculty</label>
                <Input 
                  value={formData.faculty} 
                  onChange={e => handleChange('faculty', e.target.value)} 
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Target Career</label>
                <Input 
                  value={formData.target_career} 
                  onChange={e => handleChange('target_career', e.target.value)} 
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Year</label>
                <Input 
                  type="number" 
                  min={1} max={6}
                  value={formData.year} 
                  onChange={e => handleChange('year', parseInt(e.target.value) || 1)} 
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">GPA</label>
                <Input 
                  type="number" 
                  step="0.01" min={0} max={4}
                  value={formData.gpa} 
                  onChange={e => handleChange('gpa', parseFloat(e.target.value) || 0)} 
                />
              </div>
            </div>

            {/* Skills */}
            <div className="mt-6">
              <div className="flex justify-between items-center mb-2">
                <label className="block text-xs font-semibold text-gray-600">Technical Skills</label>
                <Button type="button" variant="outline" size="sm" className="h-7 text-xs" onClick={() => addSkill('skills')}>
                  <Plus size={12} className="mr-1" /> Add
                </Button>
              </div>
              {formData.skills.map((skill, index) => (
                <div key={index} className="flex gap-2 mb-2">
                  <Input 
                    value={skill.name} 
                    onChange={e => handleSkillChange('skills', index, 'name', e.target.value)} 
                    placeholder="Skill name" className="flex-1"
                  />
                  <select 
                    value={skill.level} 
                    onChange={e => handleSkillChange('skills', index, 'level', e.target.value)}
                    className="flex-1 border rounded-md px-3 py-1 text-sm bg-white"
                  >
                    <option value="Beginner">Beginner</option>
                    <option value="Intermediate">Intermediate</option>
                    <option value="Advanced">Advanced</option>
                    <option value="Native">Native</option>
                  </select>
                  <Button type="button" variant="ghost" className="px-2 text-red-500 hover:text-red-700" onClick={() => removeSkill('skills', index)}>
                    <Trash2 size={16} />
                  </Button>
                </div>
              ))}
            </div>

            {/* Languages */}
            <div className="mt-4">
              <div className="flex justify-between items-center mb-2">
                <label className="block text-xs font-semibold text-gray-600">Languages</label>
                <Button type="button" variant="outline" size="sm" className="h-7 text-xs" onClick={() => addSkill('languages')}>
                  <Plus size={12} className="mr-1" /> Add
                </Button>
              </div>
              {formData.languages.map((skill, index) => (
                <div key={index} className="flex gap-2 mb-2">
                  <Input 
                    value={skill.name} 
                    onChange={e => handleSkillChange('languages', index, 'name', e.target.value)} 
                    placeholder="Language name" className="flex-1"
                  />
                  <select 
                    value={skill.level} 
                    onChange={e => handleSkillChange('languages', index, 'level', e.target.value)}
                    className="flex-1 border rounded-md px-3 py-1 text-sm bg-white"
                  >
                    <option value="Beginner">Beginner</option>
                    <option value="Intermediate">Intermediate</option>
                    <option value="Advanced">Advanced</option>
                    <option value="Native">Native</option>
                  </select>
                  <Button type="button" variant="ghost" className="px-2 text-red-500 hover:text-red-700" onClick={() => removeSkill('languages', index)}>
                    <Trash2 size={16} />
                  </Button>
                </div>
              ))}
            </div>
            
            <div className="mt-4">
              <label className="block text-xs font-semibold text-gray-600 mb-1">Activities (comma separated)</label>
              <Input 
                value={formData.activities} 
                onChange={e => handleChange('activities', e.target.value)} 
                placeholder="e.g. Coding Club, Hackathon"
              />
            </div>
          </form>
        </div>

        <div className="p-4 border-t border-gray-100 bg-gray-50 flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
          <Button type="submit" form="student-form" className="bg-indigo-600 text-white hover:bg-indigo-700 min-w-24" disabled={loading}>
            {loading ? <Loader2 size={16} className="animate-spin" /> : 'Save'}
          </Button>
        </div>
      </div>
    </div>
  )
}
