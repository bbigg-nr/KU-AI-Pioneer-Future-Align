'use client'

import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { storage } from '@/lib/storage'
import { useAuth } from '@/context/AuthContext'
import type { Student } from '@/lib/types'
import FieldLayout from '@/components/coach/FieldLayout'
import InsightPanel from '@/components/coach/InsightPanel'
import { getScore } from '@/components/coach/StudentPlayerCard'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { GraduationCap, Plus, X, Loader2, Users, UserPlus } from 'lucide-react'
import StudentModal from '@/components/coach/StudentModal'

const DEFAULT_STUDENTS = ['6610400000', '6610400003', '6610400004', '6610400007', '6610400010', '6610400013', '6610400015', '6610400017', '6610400018', '6610400019', '6610400020', '6610400022', '6610400023', '6610400024', '6610400026']

export default function CoachPage() {
  const { role, teacherId } = useAuth()
  const [studentIds, setStudentIds] = useState<string[]>([])
  const [students, setStudents] = useState<Student[]>([])
  const [selected, setSelected] = useState<Student | null>(null)
  const [newId, setNewId] = useState('')
  const [loading, setLoading] = useState(true)
  
  // CRUD Modal State
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [modalData, setModalData] = useState<Student | null>(null)

  useEffect(() => {
    if (role === 'teacher' && teacherId) {
      api.getTeacher(teacherId)
        .then(t => {
          setStudentIds(t.assigned_students)
          storage.setCoachStudents(t.assigned_students)
        })
        .catch(() => {
          const saved = storage.getCoachStudents()
          setStudentIds(saved.length > 0 ? saved : DEFAULT_STUDENTS)
        })
      return
    }
    const saved = storage.getCoachStudents()
    const ids = saved.length > 0 ? saved : DEFAULT_STUDENTS
    setStudentIds(ids)
    if (saved.length === 0) storage.setCoachStudents(DEFAULT_STUDENTS)
  }, [role, teacherId])

  useEffect(() => {
    if (studentIds.length === 0) return
    setLoading(true)
    Promise.all(studentIds.map(id => api.getStudent(id).catch(() => null)))
      .then(results => {
        const valid = results.filter(Boolean) as Student[]
        setStudents(valid)
        if (valid.length > 0 && !selected) setSelected(valid[0])
      })
      .finally(() => setLoading(false))
  }, [studentIds])

  const addStudent = async () => {
    const id = newId.trim().toUpperCase()
    if (!id || studentIds.includes(id)) return
    try {
      await api.getStudent(id)
      const updated = [...studentIds, id]
      setStudentIds(updated)
      storage.setCoachStudents(updated)
      setNewId('')
    } catch {
      alert('Student ID not found')
    }
  }

  const removeStudent = (id: string) => {
    const updated = studentIds.filter(s => s !== id)
    setStudentIds(updated)
    storage.setCoachStudents(updated)
    if (selected?.student_id === id) setSelected(null)
  }

  const handleSaveStudent = (student: Student) => {
    setIsModalOpen(false)
    setStudents(prev => {
      const idx = prev.findIndex(s => s.student_id === student.student_id)
      if (idx >= 0) {
        const next = [...prev]
        next[idx] = student
        return next
      }
      return [...prev, student]
    })
    if (!studentIds.includes(student.student_id)) {
      const updated = [...studentIds, student.student_id]
      setStudentIds(updated)
      storage.setCoachStudents(updated)
    }
    setSelected(student)
  }

  const handleDeleteStudent = async (id: string) => {
    if (!confirm('Are you sure you want to permanently delete this student?')) return
    try {
      await api.deleteStudent(id)
      removeStudent(id)
      setStudents(prev => prev.filter(s => s.student_id !== id))
    } catch (err) {
      alert('Failed to delete student')
    }
  }

  const scores = students.map(getScore)
  const avgScore = scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0
  const highClarity = students.filter(s => getScore(s) >= 75).length
  const developing = students.filter(s => getScore(s) >= 50 && getScore(s) < 75).length
  const needsHelp = students.filter(s => getScore(s) < 50).length

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-500 flex items-center justify-center">
            <GraduationCap size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">Coach Mode</h1>
            <p className="text-xs text-gray-400">Advisor Dashboard · Career Readiness Overview</p>
          </div>
        </div>

        <div className="flex gap-3">
          {[
            { label: 'Students', value: students.length, icon: <Users size={14} /> },
            { label: 'High Clarity', value: highClarity, color: 'text-green-600' },
            { label: 'Developing', value: developing, color: 'text-blue-500' },
            { label: 'Needs Help', value: needsHelp, color: 'text-red-500' },
            { label: 'Avg Rating', value: avgScore, color: 'text-yellow-500' },
          ].map(({ label, value, color, icon }) => (
            <div key={label} className="bg-white border border-gray-100 rounded-xl px-3 py-2 text-center shadow-sm min-w-16">
              <div className={`font-bold text-sm ${color ?? 'text-gray-800'} flex items-center justify-center gap-1`}>
                {icon}{value}
              </div>
              <p className="text-[10px] text-gray-400 uppercase tracking-wider">{label}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="flex gap-2 mb-4">
        <Input
          value={newId}
          onChange={e => setNewId(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && addStudent()}
          placeholder="Add student ID (e.g. 6610400020)"
          className="max-w-xs"
        />
        <Button onClick={addStudent} className="bg-indigo-600 hover:bg-indigo-500 text-white gap-1">
          <Plus size={15} /> Add
        </Button>
        <Button onClick={() => { setModalData(null); setIsModalOpen(true); }} className="bg-emerald-600 hover:bg-emerald-500 text-white gap-1 ml-2">
          <UserPlus size={15} /> New Student
        </Button>
        <div className="flex flex-wrap gap-1 ml-2">
          {studentIds.map(id => (
            <span key={id} className="flex items-center gap-1 text-xs bg-gray-100 rounded-full px-2 py-1">
              {id}
              <button onClick={() => removeStudent(id)} className="text-gray-400 hover:text-red-500">
                <X size={11} />
              </button>
            </span>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="animate-spin text-indigo-500" size={32} />
        </div>
      ) : (
        <div className="grid grid-cols-[1fr_360px] gap-6">
          <FieldLayout students={students} selectedStudent={selected} onSelect={setSelected} />
          {selected ? (
            <InsightPanel 
              key={selected.student_id} 
              student={selected} 
              onEdit={s => { setModalData(s); setIsModalOpen(true); }}
              onDelete={handleDeleteStudent}
            />
          ) : (
            <div className="bg-[#1a2035] rounded-2xl flex items-center justify-center text-white/30 text-sm">
              Select a student to view insights
            </div>
          )}
        </div>
      )}
      
      <StudentModal 
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSaveStudent}
        initialData={modalData}
      />
    </div>
  )
}
