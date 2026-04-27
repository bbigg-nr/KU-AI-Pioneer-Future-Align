import type { Student } from '@/lib/types'

const FACULTY_SHORT: Record<string, string> = {
  'Computer Engineering': 'COMENG',
  'Computer Science': 'CS',
  'Engineering': 'ENG',
  'Science': 'SCI',
  'Business Administration': 'BUS',
  'Economics': 'ECON',
}

function shortFaculty(faculty: string) {
  return FACULTY_SHORT[faculty] ?? faculty.slice(0, 6).toUpperCase()
}

interface StudentCardProps {
  student: Student
  matchCount?: number
}

export default function StudentCard({ student, matchCount = 0 }: StudentCardProps) {
  const initials = student.name
    .split(' ')
    .map(n => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()

  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
      <p className="text-xs text-gray-400 uppercase tracking-wider font-medium mb-4">Your Student Card</p>
      <div
        className="mx-auto w-48 rounded-2xl p-4 text-center"
        style={{
          background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 50%, #b45309 100%)',
        }}
      >
        <div className="flex justify-between items-start mb-2">
          <span className="text-2xl font-black text-white/90">{Math.round(student.gpa * 25)}</span>
          <span className="text-[10px] font-bold text-white/70 uppercase tracking-wider">
            {shortFaculty(student.faculty)}
          </span>
        </div>
        <div className="w-14 h-14 rounded-full bg-black/20 flex items-center justify-center mx-auto mb-2">
          <span className="text-xl font-black text-white">{initials}</span>
        </div>
        <p className="text-white font-bold text-sm leading-tight">{student.name}</p>
        <p className="text-white/70 text-[10px] mt-0.5">Year {student.year} · GPA {student.gpa}</p>
        <div className="grid grid-cols-3 gap-1 mt-3 pt-3 border-t border-white/20">
          <div className="text-center">
            <p className="text-white font-black text-sm">{student.skills.length}</p>
            <p className="text-white/60 text-[9px]">SKILLS</p>
          </div>
          <div className="text-center">
            <p className="text-white font-black text-sm">{student.languages.length}</p>
            <p className="text-white/60 text-[9px]">LANG</p>
          </div>
          <div className="text-center">
            <p className="text-white font-black text-sm">{matchCount}</p>
            <p className="text-white/60 text-[9px]">MATCH</p>
          </div>
        </div>
      </div>
    </div>
  )
}
