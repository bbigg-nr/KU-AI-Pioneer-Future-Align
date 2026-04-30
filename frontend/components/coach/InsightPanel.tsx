'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import type { Student, CoachingReport, JobMatch, BlendedResult } from '@/lib/types'
import { Button } from '@/components/ui/button'
import {
  Sparkles, Loader2, TrendingUp, AlertTriangle, CheckCircle2,
  Lightbulb, AlertCircle, Target, Briefcase,
} from 'lucide-react'
import FIFACard from '@/components/dashboard/FIFACard'
import dynamic from 'next/dynamic'
import { levelToScore } from '@/lib/utils'
const SkillRadar = dynamic(() => import('@/components/dashboard/SkillRadar'), { ssr: false })
import { getStudentScore } from '@/lib/studentScore'

interface InsightPanelProps {
  student: Student
  onEdit?: (student: Student) => void
  onDelete?: (id: string) => void
}

export default function InsightPanel({ student, onEdit, onDelete }: InsightPanelProps) {
  const [blended, setBlended] = useState<BlendedResult | null>(null)
  const [blendedLoading, setBlendedLoading] = useState(true)
  const [report, setReport] = useState<CoachingReport | null>(null)
  const [reportError, setReportError] = useState('')
  const [reportLoading, setReportLoading] = useState(false)

  const score = getStudentScore(student)

  useEffect(() => {
    setBlendedLoading(true)
    setBlended(null)
    setReport(null)
    setReportError('')
    api.matchStudentBlended(student.student_id, 5)
      .then(setBlended)
      .catch(() => {})
      .finally(() => setBlendedLoading(false))
  }, [student.student_id])

  const topJob = blended?.top_jobs[0] ?? null

  const studentSkillMap = new Map(student.skills.map(sk => [sk.name.toLowerCase(), sk]))
  const coreSkills = topJob
    ? [
        ...(topJob.matched_skills ?? []),
        ...(topJob.skills_to_improve ?? []).map((s: string | { skill: string }) =>
          typeof s === 'string' ? s : s.skill
        ),
        ...(topJob.missing_skills ?? []),
      ].slice(0, 6)
    : []

  const radarData = coreSkills
    .map(skillName => {
      const found = studentSkillMap.get(skillName.toLowerCase())
      return { skill: skillName, current: found ? levelToScore(found.level) : 0, required: 80 }
    })
    .sort((a, b) => b.current - a.current)

  const generateReport = async () => {
    setReportLoading(true)
    setReportError('')
    try {
      const topJobs: JobMatch[] = blended?.top_jobs.slice(0, 3) ?? []
      const topJ = topJobs[0]
      const skillList = student.skills.map(s => `${s.name} (${s.level})`).join(', ')
      const matchedSkills = topJ?.matched_skills?.slice(0, 5).join(', ') ?? 'none'
      const missingSkills = topJ?.missing_skills?.slice(0, 5).join(', ') ?? 'none'
      const skillsToImprove = topJ?.skills_to_improve?.slice(0, 3).join(', ') ?? 'none'
      const topJobsText = topJobs
        .map((j, i) => `${i + 1}. ${j.job_title} (${Math.round((j.final_score ?? j.match_score) * 100)}%)`)
        .join('\n')
      const gpaCtx = student.gpa >= 3.5 ? 'excellent' : student.gpa >= 3.0 ? 'good' : student.gpa >= 2.5 ? 'average' : 'below average'

      const systemContext = `You are a university career advisor generating a coaching report.
Student: ${student.name}, Faculty of ${student.faculty}, Year ${student.year}, GPA ${student.gpa} (${gpaCtx})
Skills: ${skillList}
Target career: ${student.target_career}
Career readiness score: ${score}/100
Top career matches:
${topJobsText}
For top match "${topJ?.job_title ?? student.target_career}":
- Already has: ${matchedSkills}
- Missing: ${missingSkills}
- Needs improvement: ${skillsToImprove}
Always respond with valid JSON only. DO NOT include any preamble, introduction, or explanation. DO NOT use markdown code blocks. Start your response with "{" and end it with "}". All generated text must be in Thai language.`

      const prompt = `Generate a realistic, specific coaching report based on actual skills and career match data.
Return JSON with exactly these keys:
- strengths: array of 3 strings (based on actual matched skills and profile)
- development_areas: array of 3 strings (based on actual missing/weak skills)
- career_progress: array of 3 strings (honest assessment vs target career)
- recommendations: array of 3 strings (specific, actionable next steps referencing real skill gaps)
Each string must be 1 concise sentence in Thai language (ภาษาไทย). Do not use generic filler text.`

      const res = await fetch('/api/advisor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: [{ role: 'user', content: prompt }], systemContext }),
      })
      if (!res.ok) throw new Error(`API error ${res.status}`)
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      
      let cleanText = data.text.trim();
      
      // Try to find JSON block in markdown
      const jsonMatch = cleanText.match(/```(?:json)?\s*([\s\S]*?)\s*```/);
      if (jsonMatch) {
        cleanText = jsonMatch[1].trim();
      } else {
        // Find first { and last }
        const firstBrace = cleanText.indexOf('{');
        const lastBrace = cleanText.lastIndexOf('}');
        if (firstBrace !== -1 && lastBrace !== -1) {
          cleanText = cleanText.substring(firstBrace, lastBrace + 1);
        }
      }

      if (!cleanText.startsWith('{')) {
        console.error('Failed to find JSON in response:', data.text);
        throw new Error('AI response was not in the expected format. Please try again.');
      }
      
      setReport(JSON.parse(cleanText))
    } catch (err) {
      setReportError(err instanceof Error ? err.message : 'Failed to generate report.')
    } finally {
      setReportLoading(false)
    }
  }

  return (
    <div className="bg-[#1a2035] rounded-2xl p-5 text-white flex flex-col overflow-y-auto gap-5 max-h-[calc(100vh-160px)]">

      {/* ── Header ── */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-indigo-500 flex items-center justify-center font-black text-sm flex-shrink-0">
          {student.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
        </div>
        <div className="min-w-0">
          <p className="font-bold text-sm truncate">{student.name}</p>
          <p className="text-white/50 text-xs truncate">{student.faculty} · Year {student.year}</p>
        </div>
        <div className="ml-auto flex items-center gap-3">
          <span className="text-yellow-400 font-black text-xl flex-shrink-0">{score}</span>
          <div className="flex gap-1">
            {onEdit && (
              <button onClick={() => onEdit(student)} className="p-1.5 bg-white/10 hover:bg-white/20 rounded-lg text-white/70 hover:text-white transition-colors" title="Edit Student">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
              </button>
            )}
            {onDelete && (
              <button onClick={() => onDelete(student.student_id)} className="p-1.5 bg-white/10 hover:bg-red-500/20 rounded-lg text-white/70 hover:text-red-400 transition-colors" title="Delete Student">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* ── Target Career Banner ── */}
      <div className="bg-indigo-600/30 border border-indigo-500/30 rounded-xl p-3">
        <div className="flex items-center gap-1.5 mb-1.5">
          <Target size={11} className="text-indigo-300" />
          <p className="text-[10px] text-indigo-300 uppercase tracking-wider font-semibold">Target Career</p>
        </div>
        {blendedLoading ? (
          <div className="flex items-center gap-2">
            <Loader2 size={11} className="animate-spin text-white/40" />
            <span className="text-xs text-white/40">Loading match data…</span>
          </div>
        ) : (
          <div className="flex items-start justify-between gap-2">
            <p className="text-sm font-bold text-white leading-tight">{student.target_career || 'Not set'}</p>
            {(() => {
              if (!student.target_career) return null;
              const targetMatch = blended?.top_jobs.find(j => j.job_title.toLowerCase() === student.target_career.toLowerCase());
              if (!targetMatch) {
                return <span className="font-bold text-white/30 text-xs mt-0.5">Not in Top 5</span>;
              }
              const score = targetMatch.final_score ?? targetMatch.match_score;
              return (
                <span className={`font-black text-base flex-shrink-0 ${
                  score >= 0.7 ? 'text-green-400' :
                  score >= 0.5 ? 'text-yellow-400' : 'text-red-400'
                }`}>
                  {Math.round(score * 100)}%
                </span>
              );
            })()}
          </div>
        )}
      </div>

      {/* ── FIFA Card ── */}
      <div>
        <FIFACard student={student} matchCount={blended?.top_jobs.length ?? 0} />
      </div>

      {/* ── Top Career Matches ── */}
      <div>
        <div className="flex items-center gap-1.5 mb-3">
          <Briefcase size={11} className="text-blue-300" />
          <p className="text-[10px] text-blue-300 uppercase tracking-wider font-semibold">Top Career Matches</p>
        </div>
        {blendedLoading ? (
          <div className="flex items-center gap-2 text-white/40 py-2">
            <Loader2 size={11} className="animate-spin" />
            <span className="text-xs">Fetching matches…</span>
          </div>
        ) : blended?.top_jobs.slice(0, 3).map((job, i) => {
          const pct = Math.round((job.final_score ?? job.match_score) * 100)
          return (
            <div key={job.job_id ?? i} className="flex items-center justify-between py-2 border-b border-white/10 last:border-0">
              <div className="min-w-0">
                <p className="text-xs font-semibold text-white truncate">{job.job_title}</p>
                <p className="text-[10px] text-white/40">{job.matched_skills?.length ?? 0} skills matched</p>
              </div>
              <span className={`text-xs font-black flex-shrink-0 ml-2 tabular-nums ${
                pct >= 70 ? 'text-green-400' : pct >= 50 ? 'text-yellow-400' : 'text-red-400'
              }`}>
                {pct}%
              </span>
            </div>
          )
        })}
      </div>

      {/* ── Skill Radar ── */}
      {radarData.length > 0 && (
        <div>
          <p className="text-[10px] text-white/40 uppercase tracking-wider font-semibold mb-2">
            Skills vs Demand · {topJob?.job_title}
          </p>
          <SkillRadar data={radarData} title="" theme="dark" />
        </div>
      )}

      {/* ── AI Report ── */}
      {!report && (
        <Button
          onClick={generateReport}
          disabled={reportLoading || blendedLoading}
          className="w-full bg-indigo-600 hover:bg-indigo-500 text-white gap-2"
        >
          {reportLoading ? <Loader2 size={15} className="animate-spin" /> : <Sparkles size={15} />}
          {reportLoading ? 'Analysing…' : 'Generate AI Report'}
        </Button>
      )}

      {reportError && (
        <div className="flex items-start gap-2 text-red-400 bg-red-400/10 rounded-xl px-3 py-2 text-xs">
          <AlertCircle size={13} className="mt-0.5 flex-shrink-0" />
          {reportError}
        </div>
      )}

      {report && (
        <div className="space-y-4">
          <ReportSection title="Strengths" icon={<CheckCircle2 size={13} className="text-green-400" />} items={report.strengths} color="text-green-400" />
          <ReportSection title="Development Areas" icon={<AlertTriangle size={13} className="text-yellow-400" />} items={report.development_areas} color="text-yellow-400" />
          <ReportSection title="Career Progress" icon={<TrendingUp size={13} className="text-blue-400" />} items={report.career_progress} color="text-blue-400" />
          <ReportSection title="Recommendations" icon={<Lightbulb size={13} className="text-purple-400" />} items={report.recommendations} color="text-purple-400" />
          <Button
            onClick={generateReport}
            disabled={reportLoading}
            variant="outline"
            className="w-full text-xs border-white/20 text-white/60 hover:text-white gap-2"
          >
            {reportLoading ? <Loader2 size={12} className="animate-spin" /> : <Sparkles size={12} />}
            Regenerate
          </Button>
        </div>
      )}
    </div>
  )
}

function ReportSection({ title, icon, items, color }: {
  title: string; icon: React.ReactNode; items: string[]; color: string
}) {
  return (
    <div>
      <div className="flex items-center gap-1.5 mb-2">
        {icon}
        <p className={`text-xs font-semibold uppercase tracking-wider ${color}`}>{title}</p>
      </div>
      <ul className="space-y-1.5">
        {items.map((item, i) => (
          <li key={i} className="text-xs text-white/70 flex gap-2">
            <span className="text-white/30 mt-0.5 flex-shrink-0">•</span>
            {item}
          </li>
        ))}
      </ul>
    </div>
  )
}
