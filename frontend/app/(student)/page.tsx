'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import { api } from '@/lib/api'
import type { Student, BlendedResult, JobMatch } from '@/lib/types'
import StatCard from '@/components/dashboard/StatCard'
import SkillRadar, { levelToScore } from '@/components/dashboard/SkillRadar'
import StudentCard from '@/components/dashboard/StudentCard'
import MatchCard from '@/components/dashboard/MatchCard'
import MatchDetailPanel from '@/components/dashboard/MatchDetailPanel'
import { Briefcase, GraduationCap, AlertCircle, Loader2 } from 'lucide-react'
import Link from 'next/link'

function groupByTitle(jobs: JobMatch[]): { best: JobMatch; variations: JobMatch[] }[] {
  const map = new Map<string, JobMatch[]>()
  for (const job of jobs) {
    const key = job.job_title
    if (!map.has(key)) map.set(key, [])
    map.get(key)!.push(job)
  }
  return Array.from(map.values()).map(group => {
    const sorted = [...group].sort((a, b) =>
      (b.final_score ?? b.match_score) - (a.final_score ?? a.match_score)
    )
    return { best: sorted[0], variations: sorted.slice(1) }
  }).sort((a, b) =>
    (b.best.final_score ?? b.best.match_score) - (a.best.final_score ?? a.best.match_score)
  )
}

export default function DashboardPage() {
  const { studentId } = useAuth()
  const [student, setStudent] = useState<Student | null>(null)
  const [blended, setBlended] = useState<BlendedResult | null>(null)
  const [activeMatch, setActiveMatch] = useState<JobMatch | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!studentId) return
    setLoading(true)
    Promise.all([
      api.getStudent(studentId),
      api.matchStudentBlended(studentId, 5),
    ])
      .then(([s, b]) => {
        setStudent(s)
        setBlended(b)
      })
      .catch(() => setError('Failed to load data. Is the backend running?'))
      .finally(() => setLoading(false))
  }, [studentId])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-indigo-500" size={32} />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center gap-3 text-red-500 bg-red-50 rounded-xl p-4">
        <AlertCircle size={20} />
        <p>{error}</p>
      </div>
    )
  }

  if (!student || !blended) return null

  const topJob = blended.top_jobs[0]
  const skillGapCount = topJob?.missing_skills?.length ?? 0

  const radarData = student.skills.slice(0, 8).map(sk => ({
    skill: sk.name,
    current: levelToScore(sk.level),
    required: topJob?.matched_skills?.includes(sk.name) ? 80 : 40,
  }))

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Welcome back, {student.name}</h1>
        <p className="text-gray-500 text-sm mt-1">Your career guidance dashboard powered by FutureAlign AI</p>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-8">
        <StatCard
          title="Career Matches"
          value={blended.top_jobs.length}
          subtitle="positions found"
          icon={Briefcase}
          iconBg="bg-indigo-500"
        />
        <StatCard
          title="Skills"
          value={student.skills.length}
          subtitle="in your profile"
          icon={GraduationCap}
          iconBg="bg-blue-500"
        />
        <StatCard
          title="Skill Gaps"
          value={skillGapCount}
          subtitle={topJob ? `for ${topJob.job_title}` : 'identified'}
          icon={AlertCircle}
          iconBg="bg-orange-400"
        />
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="space-y-6">
          <SkillRadar
            data={radarData}
            title={`Skills vs Market Demand for ${topJob?.job_title ?? 'Top Career'}`}
          />
          <StudentCard student={student} matchCount={blended.top_jobs.length} />
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-gray-900">Your Target Careers</h2>
              <p className="text-xs text-gray-400">Click a card to view details</p>
            </div>
            <Link href="/career-matches" className="text-xs text-indigo-500 hover:text-indigo-700 font-medium">
              View All →
            </Link>
          </div>

          {activeMatch ? (
            <MatchDetailPanel match={activeMatch} onClose={() => setActiveMatch(null)} />
          ) : (
            <div className="space-y-3">
              {groupByTitle(blended.top_jobs).map(({ best, variations }, i) => (
                <MatchCard
                  key={best.job_id ?? best.job_title}
                  match={best}
                  variations={variations}
                  index={i}
                  isActive={activeMatch === best}
                  onClick={() => setActiveMatch(best)}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
