'use client'

import { useState } from 'react'
import type { Student, CoachingReport } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Sparkles, Loader2, TrendingUp, AlertTriangle, CheckCircle2, Lightbulb } from 'lucide-react'
import { getScore } from './StudentPlayerCard'

interface InsightPanelProps {
  student: Student
}

export default function InsightPanel({ student }: InsightPanelProps) {
  const [report, setReport] = useState<CoachingReport | null>(null)
  const [loading, setLoading] = useState(false)
  const score = getScore(student)

  const generateReport = async () => {
    setLoading(true)
    const skillList = student.skills.map(s => `${s.name} (${s.level})`).join(', ')
    const prompt = `Generate a coaching report for this student in JSON format.
Student: ${student.name}, ${student.faculty}, Year ${student.year}, GPA ${student.gpa}
Skills: ${skillList}
Target career: ${student.target_career}

Return JSON with keys: strengths (array of 3 strings), development_areas (array of 3 strings), career_progress (array of 3 strings), recommendations (array of 3 strings).
Each string should be 1 concise sentence.`

    try {
      const res = await fetch('/api/advisor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [{ role: 'user', content: prompt }],
          systemContext: 'You are a career coaching AI. Always respond with valid JSON only, no markdown.',
        }),
      })
      const data = await res.json()
      const parsed = JSON.parse(data.text)
      setReport(parsed)
    } catch {
      setReport({
        strengths: [`GPA ${student.gpa} indicates strong academic performance`, 'Diverse skill set shows broad capabilities', 'Clear career target direction'],
        development_areas: ['Expand technical skills depth', 'Build industry-specific experience', 'Develop professional network'],
        career_progress: ['On track for target career path', 'Skills align with market demand', 'Year ' + student.year + ' progress appropriate'],
        recommendations: ['Seek internship opportunities', 'Join relevant student organizations', 'Build portfolio projects'],
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-[#1a2035] rounded-2xl p-5 text-white h-full flex flex-col overflow-y-auto">
      <div className="flex items-center gap-3 mb-5">
        <div className="w-10 h-10 rounded-full bg-indigo-500 flex items-center justify-center font-black text-sm">
          {student.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
        </div>
        <div>
          <p className="font-bold text-sm">{student.name}</p>
          <p className="text-white/50 text-xs">{student.faculty}</p>
        </div>
        <span className="ml-auto text-yellow-400 font-black text-xl">{score}</span>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-5">
        <Stat label="GPA" value={student.gpa} />
        <Stat label="Skills" value={student.skills.length} />
      </div>

      {!report && (
        <Button
          onClick={generateReport}
          disabled={loading}
          className="w-full bg-indigo-600 hover:bg-indigo-500 text-white mb-4 gap-2"
        >
          {loading ? <Loader2 size={15} className="animate-spin" /> : <Sparkles size={15} />}
          {loading ? 'Generating Report…' : 'Generate AI Report'}
        </Button>
      )}

      {report && (
        <div className="space-y-4 flex-1">
          <ReportSection title="Strengths" icon={<CheckCircle2 size={13} className="text-green-400" />} items={report.strengths} color="text-green-400" />
          <ReportSection title="Development Areas" icon={<AlertTriangle size={13} className="text-yellow-400" />} items={report.development_areas} color="text-yellow-400" />
          <ReportSection title="Career Progress" icon={<TrendingUp size={13} className="text-blue-400" />} items={report.career_progress} color="text-blue-400" />
          <ReportSection title="Recommendations" icon={<Lightbulb size={13} className="text-purple-400" />} items={report.recommendations} color="text-purple-400" />
          <Button
            onClick={generateReport}
            disabled={loading}
            variant="outline"
            className="w-full text-xs border-white/20 text-white/60 hover:text-white gap-2"
          >
            <Sparkles size={12} />Regenerate
          </Button>
        </div>
      )}
    </div>
  )
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-white/5 rounded-xl p-3 text-center">
      <p className="text-xl font-black text-white">{value}</p>
      <p className="text-white/50 text-xs uppercase tracking-wider">{label}</p>
    </div>
  )
}

function ReportSection({ title, icon, items, color }: { title: string; icon: React.ReactNode; items: string[]; color: string }) {
  return (
    <div>
      <div className="flex items-center gap-1.5 mb-2">
        {icon}
        <p className={`text-xs font-semibold uppercase tracking-wider ${color}`}>{title}</p>
      </div>
      <ul className="space-y-1.5">
        {items.map((item, i) => (
          <li key={i} className="text-xs text-white/70 flex gap-2">
            <span className="text-white/30 mt-0.5">•</span>
            {item}
          </li>
        ))}
      </ul>
    </div>
  )
}
