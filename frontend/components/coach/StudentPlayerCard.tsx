import type { Student } from '@/lib/types'
import { cn } from '@/lib/utils'

function clarityScore(student: Student): number {
  const gpaScore = student.gpa * 10
  const skillScore = Math.min(student.skills.length * 3, 30)
  const raw = gpaScore + skillScore
  return Math.min(Math.round(raw), 99)
}

function getCardColor(score: number) {
  if (score >= 75) return 'from-green-700 to-green-900'
  if (score >= 50) return 'from-blue-700 to-blue-900'
  return 'from-slate-600 to-slate-800'
}

function shortFaculty(faculty: string): string {
  const map: Record<string, string> = {
    'Computer Engineering': 'COM',
    'Computer Science': 'COM',
    'Engineering': 'ENG',
    'Science': 'SCI',
    'Business Administration': 'BUS',
    'Economics': 'ECO',
    'Mathematics': 'MAS',
    'Finance': 'FIN',
    'Psychology': 'PSY',
    'Architecture': 'ARC',
    'Graphic Design': 'GRA',
    'Mechanical Engineering': 'MIC',
    'Biotechnology': 'BIO',
    'Electrical Engineering': 'ELU',
    'Media & Communication': 'MED',
    'Cybersecurity': 'CYS',
    'Data Science': 'DAT',
  }
  return map[faculty] ?? faculty.slice(0, 3).toUpperCase()
}

function initials(name: string) {
  return name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
}

interface StudentPlayerCardProps {
  student: Student
  isSelected?: boolean
  onClick?: () => void
}

export function getScore(student: Student) { return clarityScore(student) }

export default function StudentPlayerCard({ student, isSelected, onClick }: StudentPlayerCardProps) {
  const score = clarityScore(student)
  const color = getCardColor(score)

  return (
    <div
      onClick={onClick}
      className={cn(
        'w-20 rounded-xl cursor-pointer transition-all duration-200 select-none',
        `bg-gradient-to-b ${color}`,
        isSelected && 'ring-2 ring-yellow-400 ring-offset-1 scale-105'
      )}
    >
      <div className="px-2 pt-2 pb-1">
        <div className="flex justify-between items-start">
          <span className="text-white font-black text-base leading-none">{score}</span>
          <span className="text-white/70 text-[8px] font-bold uppercase">{shortFaculty(student.faculty)}</span>
        </div>
        <div className="w-10 h-10 rounded-full bg-black/20 flex items-center justify-center mx-auto my-1">
          <span className="text-white font-black text-sm">{initials(student.name)}</span>
        </div>
        <p className="text-white text-[9px] font-bold text-center leading-tight truncate">
          {student.name.split(' ')[0]}
        </p>
        <p className="text-white/60 text-[7px] text-center truncate">
          {student.name.split(' ').slice(1).join(' ')}
        </p>
        <div className="grid grid-cols-3 gap-0.5 mt-1 pt-1 border-t border-white/20 text-center">
          <div>
            <p className="text-white font-black text-[9px]">{Math.round(student.gpa * 10)}</p>
            <p className="text-white/50 text-[7px]">GPA</p>
          </div>
          <div>
            <p className="text-white font-black text-[9px]">{student.skills.length}</p>
            <p className="text-white/50 text-[7px]">SKL</p>
          </div>
          <div>
            <p className="text-white font-black text-[9px]">{student.year}</p>
            <p className="text-white/50 text-[7px]">YR</p>
          </div>
        </div>
      </div>
    </div>
  )
}
