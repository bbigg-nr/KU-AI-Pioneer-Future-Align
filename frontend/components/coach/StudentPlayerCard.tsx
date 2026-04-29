import type { Student } from '@/lib/types'
import { cn } from '@/lib/utils'
import { getStudentScore } from '@/lib/studentScore'

function getCardGradient(score: number): { bg: string; statsBg: string; glow: string } {
  if (score >= 80) return {
    bg: 'linear-gradient(180deg, #a07320 0%, #e8c840 30%, #f5d860 55%, #c8a030 80%, #8a6010 100%)',
    statsBg: 'linear-gradient(180deg, #b08828 0%, #907018 100%)',
    glow: 'rgba(240,208,96,0.45)',
  }
  if (score >= 65) return {
    bg: 'linear-gradient(180deg, #808288 0%, #c8cad4 30%, #dcdee8 55%, #a8aab2 80%, #686a70 100%)',
    statsBg: 'linear-gradient(180deg, #989aa4 0%, #787a82 100%)',
    glow: 'rgba(200,202,212,0.35)',
  }
  return {
    bg: 'linear-gradient(180deg, #8a4818 0%, #cc7830 30%, #e09040 55%, #a85c20 80%, #6a3008 100%)',
    statsBg: 'linear-gradient(180deg, #9a5a18 0%, #7a4010 100%)',
    glow: 'rgba(208,128,48,0.4)',
  }
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

export function getScore(student: Student) { return getStudentScore(student) }

export default function StudentPlayerCard({ student, isSelected, onClick }: StudentPlayerCardProps) {
  const score = getStudentScore(student)
  const { bg, statsBg, glow } = getCardGradient(score)

  return (
    <div
      onClick={onClick}
      className={cn(
        'w-20 rounded-xl cursor-pointer transition-all duration-200 select-none',
        isSelected && 'ring-2 ring-yellow-400 ring-offset-1 scale-105'
      )}
      style={{ background: bg, boxShadow: `0 6px 20px ${glow}` }}
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
        <div
          className="grid grid-cols-3 gap-0.5 mt-1 pt-1 border-t border-white/20 text-center"
          style={{ background: statsBg, margin: '4px -8px -4px', padding: '4px 8px 4px', borderRadius: '0 0 10px 10px' }}
        >
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
