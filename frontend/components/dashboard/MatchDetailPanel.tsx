import type { JobMatch, ArchetypeMatch } from '@/lib/types'
import { X, CheckCircle2, XCircle, TrendingUp, Briefcase } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

type AnyMatch = JobMatch | ArchetypeMatch

function isArchetype(m: AnyMatch): m is ArchetypeMatch {
  return 'archetype_name' in m
}

function toSkillName(s: unknown): string {
  if (typeof s === 'string') return s
  if (s && typeof s === 'object') {
    const o = s as Record<string, unknown>
    return String(o.skill ?? o.name ?? o.skill_name ?? '')
  }
  return String(s)
}

interface MatchDetailPanelProps {
  match: AnyMatch
  onClose: () => void
}

export default function MatchDetailPanel({ match, onClose }: MatchDetailPanelProps) {
  const score = Math.round(
    isArchetype(match) ? match.match_score * 100 : (match.final_score ?? match.match_score) * 100
  )
  const successScore = Math.round(score * 0.94)
  const salaryRaw = isArchetype(match) ? match.salary_range : null
  const salary = salaryRaw
    ? typeof salaryRaw === 'object'
      ? `${(salaryRaw as {min:number,max:number}).min?.toLocaleString()} - ${(salaryRaw as {min:number,max:number}).max?.toLocaleString()}`
      : String(salaryRaw)
    : null
  const industry = isArchetype(match) ? match.industry : 'Technology'

  return (
    <div className="bg-white rounded-2xl border border-indigo-200 shadow-lg p-6 sticky top-0">
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-1 mb-1">
            <Briefcase size={13} className="text-gray-400" />
            <span className="text-xs text-gray-400">{industry}</span>
          </div>
          <h2 className="text-lg font-bold text-gray-900">{match.job_title}</h2>
          {isArchetype(match) && (
            <p className="text-xs text-indigo-500 mt-0.5">{match.archetype_name}</p>
          )}
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
          <X size={18} />
        </button>
      </div>

      <div className="space-y-2 mb-5">
        <ScoreBar label="Skill Match" value={score} color="bg-indigo-500" />
        <ScoreBar label="Success Probability" value={successScore} color="bg-emerald-500" />
      </div>

      {salary && (
        <div className="flex items-center gap-2 mb-5 p-3 bg-gray-50 rounded-xl">
          <TrendingUp size={14} className="text-green-500" />
          <span className="text-sm font-medium text-gray-700">฿ {salary}</span>
        </div>
      )}

      {match.matched_skills?.length > 0 && (
        <Section title="Matched Skills" icon={<CheckCircle2 size={14} className="text-green-500" />}>
          <div className="flex flex-wrap gap-1">
            {match.matched_skills.map((s, i) => (
              <Badge key={i} className="text-[10px] bg-green-50 text-green-700 border-green-200">{toSkillName(s)}</Badge>
            ))}
          </div>
        </Section>
      )}

      {match.missing_skills?.length > 0 && (
        <Section title="Skills to Develop" icon={<XCircle size={14} className="text-red-400" />}>
          <div className="flex flex-wrap gap-1">
            {match.missing_skills.map((s, i) => (
              <Badge key={i} variant="outline" className="text-[10px] text-red-500 border-red-200">{toSkillName(s)}</Badge>
            ))}
          </div>
        </Section>
      )}

      {match.skills_to_improve?.length > 0 && (
        <Section title="Skills to Improve" icon={<TrendingUp size={14} className="text-amber-500" />}>
          <div className="flex flex-wrap gap-1">
            {match.skills_to_improve.map((s, i) => (
              <Badge key={i} variant="outline" className="text-[10px] text-amber-600 border-amber-200">{toSkillName(s)}</Badge>
            ))}
          </div>
        </Section>
      )}
    </div>
  )
}

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div>
      <div className="flex justify-between text-xs text-gray-500 mb-1">
        <span>{label}</span>
        <span className="font-semibold text-gray-700">{value}%</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={cn('h-full rounded-full', color)} style={{ width: `${value}%` }} />
      </div>
    </div>
  )
}

function Section({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="mb-4">
      <div className="flex items-center gap-1.5 mb-2">
        {icon}
        <p className="text-xs font-semibold text-gray-600">{title}</p>
      </div>
      {children}
    </div>
  )
}
