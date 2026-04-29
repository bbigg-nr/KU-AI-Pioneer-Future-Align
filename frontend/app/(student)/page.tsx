'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import { api } from '@/lib/api'
import { storage } from '@/lib/storage'
import type { Student, BlendedResult, JobMatch } from '@/lib/types'
import StatCard from '@/components/dashboard/StatCard'
import dynamic from 'next/dynamic'
import { levelToScore } from '@/lib/utils'
const SkillRadar = dynamic(() => import('@/components/dashboard/SkillRadar'), { ssr: false })
import FIFACard from '@/components/dashboard/FIFACard'
import MatchCard from '@/components/dashboard/MatchCard'
import MatchDetailPanel from '@/components/dashboard/MatchDetailPanel'
import { motion, AnimatePresence } from 'framer-motion'

import { Briefcase, GraduationCap, AlertCircle, Loader2, Target, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
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
  const { studentId, role } = useAuth()
  const router = useRouter()
  const [student, setStudent] = useState<Student | null>(null)
  const [blended, setBlended] = useState<BlendedResult | null>(null)
  const [savedTitles, setSavedTitles] = useState<string[]>([])
  const [activeMatch, setActiveMatch] = useState<JobMatch | null>(null)
  const [focusedJob, setFocusedJob] = useState<JobMatch | null>(null)
  const [showSkillGaps, setShowSkillGaps] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (role === 'teacher') router.replace('/coach')
  }, [role, router])

  useEffect(() => {
    setSavedTitles(storage.getTargets())
  }, [])

  useEffect(() => {
    if (!studentId) return
    setLoading(true)
    Promise.all([
      api.getStudent(studentId),
      api.matchStudentBlended(studentId, 20),
    ])
      .then(([s, b]) => {
        setStudent(s)
        setBlended(b)
        const groups = groupByTitle(b.top_jobs)
        const saved = storage.getTargets()
        const savedGroup = groups.find(g => saved.includes(g.best.job_title))
        setFocusedJob(savedGroup?.best ?? groups[0]?.best ?? null)
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

  const allGroups = groupByTitle(blended.top_jobs)
  const savedGroups = savedTitles.length > 0
    ? allGroups.filter(g => savedTitles.includes(g.best.job_title))
    : []

  const referenceJob = focusedJob ?? savedGroups[0]?.best ?? allGroups[0]?.best
  const skillGapCount = referenceJob?.missing_skills?.length ?? 0



  const studentSkillMap = new Map(
    student.skills.map(sk => [sk.name.toLowerCase(), sk])
  )

  const coreSkills = [
    ...(referenceJob?.matched_skills ?? []),
    ...(referenceJob?.skills_to_improve ?? []).map((s: string | { skill: string }) => typeof s === 'string' ? s : s.skill),
    ...(referenceJob?.missing_skills ?? []),
  ].slice(0, 8)

  const radarData = coreSkills
    .map(skillName => {
      const found = studentSkillMap.get(skillName.toLowerCase())
      return {
        skill: skillName,
        current: found ? levelToScore(found.level) : 0,
        required: 80,
      }
    })
    .sort((a, b) => b.current - a.current)

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
          onClick={() => router.push('/career-matches')}
        />
        <StatCard
          title="Skills"
          value={student.skills.length}
          subtitle="in your profile"
          icon={GraduationCap}
          iconBg="bg-blue-500"
          onClick={() => router.push('/profile')}
        />
        <StatCard
          title="Skill Gaps"
          value={skillGapCount}
          subtitle={referenceJob ? `for ${referenceJob.job_title}` : 'identified'}
          icon={AlertCircle}
          iconBg="bg-orange-400"
          onClick={() => setShowSkillGaps(true)}
        />
      </div>

      <div className="mb-8 relative overflow-hidden rounded-3xl bg-gradient-to-br from-indigo-900 via-indigo-800 to-purple-900 p-8 shadow-xl text-white">
        <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
          <Target size={120} />
        </div>
        <div className="absolute -left-10 -bottom-10 w-40 h-40 bg-purple-500 rounded-full blur-3xl opacity-30 pointer-events-none"></div>
        
        <div className="relative z-10 flex flex-col md:flex-row md:justify-between md:items-end gap-6">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <div className="bg-indigo-500/30 p-1.5 rounded-lg backdrop-blur-sm">
                <Target size={16} className="text-indigo-200" />
              </div>
              <span className="text-indigo-200 font-medium tracking-wide uppercase text-xs">Target Career</span>
            </div>
            <AnimatePresence mode="wait">
              <motion.div
                key={referenceJob?.job_title || 'empty'}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.3, ease: "easeOut" }}
              >
                <h2 className="text-3xl font-extrabold tracking-tight sm:text-4xl">
                  {referenceJob?.job_title || 'Not Selected'}
                </h2>
                {referenceJob && (
                   <p className="mt-2 text-indigo-200 max-w-xl text-sm leading-relaxed">
                     Based on your profile, you are a {Math.round((referenceJob.final_score ?? referenceJob.match_score) * 100)}% match for this role.
                   </p>
                )}
              </motion.div>
            </AnimatePresence>
          </div>
          
          <div className="text-left md:text-right">
            <AnimatePresence mode="wait">
              <motion.div
                key={referenceJob?.job_title || 'empty'}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                transition={{ duration: 0.3, ease: "easeOut" }}
                className="flex flex-col md:items-end"
              >
                <span className="text-5xl font-black tabular-nums tracking-tighter">
                  {referenceJob ? Math.round((referenceJob.final_score ?? referenceJob.match_score) * 100) : 0}
                  <span className="text-2xl text-indigo-300">%</span>
                </span>
                <span className="text-sm font-medium text-indigo-300 uppercase tracking-wider mt-1">Match Score</span>
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="space-y-6">
          <SkillRadar
            data={radarData}
            title={`Skills vs Market Demand for ${referenceJob?.job_title ?? 'Top Career'}`}
          />
          <FIFACard student={student} matchCount={blended.top_jobs.length} />
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-gray-900">My Target Careers</h2>
              <p className="text-xs text-gray-400">Click a card to view details</p>
            </div>
            <Link href="/career-matches" className="text-xs text-indigo-500 hover:text-indigo-700 font-medium">
              {savedGroups.length > 0 ? 'Manage Targets →' : 'Add Targets →'}
            </Link>
          </div>

          {activeMatch ? (
            <MatchDetailPanel match={activeMatch} onClose={() => setActiveMatch(null)} />
          ) : savedGroups.length === 0 ? (
            <div className="text-center py-12 text-gray-400 border-2 border-dashed border-gray-200 rounded-2xl">
              <Target size={32} className="mx-auto mb-3 opacity-40" />
              <p className="text-sm font-medium">No targets saved yet</p>
              <p className="text-xs mt-1">Go to Career Matches to add your targets</p>
            </div>
          ) : (
            <div className="space-y-3">
              {savedGroups.map(({ best, variations }, i) => (
                <MatchCard
                  key={best.job_id ?? best.job_title}
                  match={best}
                  variations={variations}
                  index={i}
                  isActive={activeMatch === best}
                  isTarget={true}
                  onClick={() => {
                    setActiveMatch(best)
                    setFocusedJob(best)
                    if (student) {
                      api.updateStudent(student.student_id, { target_career: best.job_title }).catch(console.error)
                    }
                    window.scrollTo({ top: 0, behavior: 'smooth' })
                  }}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {showSkillGaps && referenceJob && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-2xl relative overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            <button 
              onClick={() => setShowSkillGaps(false)}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X size={20} />
            </button>
            <div className="mb-5 flex items-center gap-3">
              <div className="p-2 bg-orange-100 text-orange-500 rounded-xl">
                <AlertCircle size={24} />
              </div>
              <div>
                <h3 className="font-bold text-gray-900 text-lg">Skill Gaps</h3>
                <p className="text-xs text-gray-500">Missing skills for {referenceJob.job_title}</p>
              </div>
            </div>
            
            <div className="space-y-2 max-h-[60vh] overflow-y-auto pr-2">
              {(referenceJob.missing_skills?.length ?? 0) > 0 ? (
                referenceJob.missing_skills.map((skill, idx) => (
                  <div key={idx} className="flex items-center justify-between bg-orange-50/50 border border-orange-100 p-3 rounded-xl">
                    <span className="text-sm font-medium text-gray-700">{skill}</span>
                    <span className="text-[10px] font-semibold text-orange-600 bg-orange-200/50 border border-orange-200 px-2.5 py-0.5 rounded-full uppercase tracking-wider">Missing</span>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-gray-400">
                  <p className="text-sm font-medium">No missing skills found! 🎉</p>
                  <p className="text-xs mt-1">You are perfectly aligned for this role.</p>
                </div>
              )}
            </div>
            <div className="mt-6 pt-5 border-t border-gray-100 flex justify-end">
              <Button onClick={() => setShowSkillGaps(false)} className="bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl shadow-md hover:shadow-lg transition-all px-6">
                Got it
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
