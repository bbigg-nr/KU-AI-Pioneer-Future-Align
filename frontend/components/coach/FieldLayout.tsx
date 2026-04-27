import type { Student } from '@/lib/types'
import StudentPlayerCard, { getScore } from './StudentPlayerCard'

interface FieldLayoutProps {
  students: Student[]
  selectedStudent: Student | null
  onSelect: (s: Student) => void
}

export default function FieldLayout({ students, selectedStudent, onSelect }: FieldLayoutProps) {
  const high = students.filter(s => getScore(s) >= 75)
  const developing = students.filter(s => getScore(s) >= 50 && getScore(s) < 75)
  const needs = students.filter(s => getScore(s) < 50)

  return (
    <div
      className="relative rounded-2xl overflow-hidden flex flex-col"
      style={{ background: 'linear-gradient(180deg, #1a5c1a 0%, #2d8b2d 40%, #2d8b2d 60%, #1a5c1a 100%)', minHeight: 500 }}
    >
      <div className="absolute inset-0 opacity-10">
        <div className="border-2 border-white rounded-full w-32 h-32 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
        <div className="border-t-2 border-white absolute left-0 right-0 top-1/2" />
      </div>

      <Zone label="HIGH CAREER CLARITY" color="text-yellow-300" students={high} selected={selectedStudent} onSelect={onSelect} />
      <Zone label="DEVELOPING DIRECTION" color="text-yellow-200" students={developing} selected={selectedStudent} onSelect={onSelect} />
      <Zone label="NEEDS GUIDANCE" color="text-red-300" students={needs} selected={selectedStudent} onSelect={onSelect} />

      {students.length === 0 && (
        <div className="flex-1 flex items-center justify-center text-white/50 text-sm">
          No students added yet
        </div>
      )}

      <div className="relative px-4 py-2 border-t border-white/20 flex justify-center gap-6 text-xs text-white/70">
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-green-500 inline-block" /> Elite (80+)</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-green-600 inline-block" /> Strong (65–79)</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-blue-700 inline-block" /> Building (40–64)</span>
      </div>
    </div>
  )
}

function Zone({
  label, color, students, selected, onSelect,
}: {
  label: string
  color: string
  students: Student[]
  selected: Student | null
  onSelect: (s: Student) => void
}) {
  return (
    <div className="relative flex-1 p-4 border-b border-white/10 last:border-0">
      <p className={`text-[10px] font-bold uppercase tracking-widest mb-3 text-center ${color} flex items-center justify-center gap-1`}>
        <span className="text-yellow-300">●</span> {label}
      </p>
      <div className="flex flex-wrap justify-center gap-3">
        {students.map(s => (
          <StudentPlayerCard
            key={s.student_id}
            student={s}
            isSelected={selected?.student_id === s.student_id}
            onClick={() => onSelect(s)}
          />
        ))}
        {students.length === 0 && (
          <p className="text-white/30 text-xs py-4">No students in this zone</p>
        )}
      </div>
    </div>
  )
}
