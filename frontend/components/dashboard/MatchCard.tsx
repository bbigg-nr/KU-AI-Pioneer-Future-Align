'use client'

import { useState } from 'react'
import type { JobMatch, ArchetypeMatch } from '@/lib/types'
import { Badge } from '@/components/ui/badge'
import { Briefcase, Target, ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'

type AnyMatch = JobMatch | ArchetypeMatch

function isArchetype(m: AnyMatch): m is ArchetypeMatch {
  return 'archetype_name' in m
}

export function toSkillName(s: unknown): string {
  if (typeof s === 'string') return s
  if (s && typeof s === 'object') {
    const o = s as Record<string, unknown>
    return String(o.skill ?? o.name ?? o.skill_name ?? '')
  }
  return String(s)
}

function formatSalary(raw: unknown): string | null {
  if (!raw) return null
  if (typeof raw === 'object') {
    const o = raw as { min?: number; max?: number }
    if (o.min != null && o.max != null)
      return `${o.min.toLocaleString()} - ${o.max.toLocaleString()}`
  }
  return String(raw)
}

function getScore(m: AnyMatch) {
  return Math.round(
    isArchetype(m) ? m.match_score * 100 : (m.final_score ?? m.match_score) * 100
  )
}

interface MatchCardProps {
  match: AnyMatch
  variations?: AnyMatch[]
  index: number
  isActive?: boolean
  isTarget?: boolean
  onClick?: () => void
}

export default function MatchCard({ match, variations = [], index, isActive, isTarget, onClick }: MatchCardProps) {
  const [expanded, setExpanded] = useState(false)

  const score = getScore(match)
  const successScore = Math.round(score * 0.94)
  const skills = (isArchetype(match)
    ? match.top_skills?.slice(0, 4)
    : match.matched_skills?.slice(0, 4)
  )?.map(toSkillName)
  const salary = formatSalary(isArchetype(match) ? match.salary_range : null)
  const industry = isArchetype(match) ? match.industry : 'Technology'
  const totalSkills = (isArchetype(match) ? match.top_skills?.length : match.matched_skills?.length) ?? 0

  return (
    <div className={cn(
      'bg-white rounded-2xl border transition-all',
      isActive ? 'border-indigo-400 ring-2 ring-indigo-100 shadow-md' : 'border-gray-100 shadow-sm hover:shadow-md'
    )}>
      <div className="p-5 cursor-pointer" onClick={onClick}>
        <div className="flex items-start justify-between mb-3">
          <div>
            <p className="text-xs text-indigo-500 font-semibold mb-1">#{index + 1}</p>
            <h3 className="font-bold text-gray-900 text-sm">{match.job_title}</h3>
            <div className="flex items-center gap-1 mt-0.5">
              <Briefcase size={11} className="text-gray-400" />
              <p className="text-xs text-gray-400">{industry}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {isTarget && <Target size={16} className="text-indigo-500 flex-shrink-0" />}
            {variations.length > 0 && (
              <span className="text-[10px] bg-indigo-50 text-indigo-500 font-semibold px-2 py-0.5 rounded-full">
                +{variations.length} var
              </span>
            )}
          </div>
        </div>

        <div className="space-y-2 mb-3">
          <ScoreBar label="Skill Match" value={score} color="bg-indigo-500" />
          <ScoreBar label="Success Probability" value={successScore} color="bg-emerald-500" />
        </div>

        <div className="flex flex-wrap gap-1 mb-2">
          {skills?.map(s => (
            <Badge key={s} variant="secondary" className="text-[10px] px-2 py-0">{s}</Badge>
          ))}
          {totalSkills > 4 && (
            <Badge variant="outline" className="text-[10px] px-2 py-0">+{totalSkills - 4} more</Badge>
          )}
        </div>

        {salary && <p className="text-xs text-gray-500">฿ {salary}</p>}
      </div>

      {variations.length > 0 && (
        <div className="border-t border-gray-100">
          <button
            onClick={() => setExpanded(e => !e)}
            className="w-full flex items-center justify-between px-5 py-2.5 text-xs text-gray-500 hover:text-indigo-600 hover:bg-gray-50 transition-colors"
          >
            <span>{expanded ? 'Hide' : 'Show'} {variations.length} variation{variations.length > 1 ? 's' : ''}</span>
            <ChevronDown size={14} className={cn('transition-transform', expanded && 'rotate-180')} />
          </button>

          {expanded && (
            <div className="px-4 pb-4 space-y-2">
              {variations.map((v, i) => (
                <VariationRow key={i} match={v} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function VariationRow({ match }: { match: AnyMatch }) {
  const score = getScore(match)
  const skills = (isArchetype(match)
    ? match.top_skills?.slice(0, 3)
    : match.matched_skills?.slice(0, 3)
  )?.map(toSkillName)
  const label = isArchetype(match) ? match.archetype_name : `Variant (${score}%)`

  return (
    <div className="bg-gray-50 rounded-xl p-3 flex items-center justify-between gap-3">
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-gray-600 truncate">{label}</p>
        <div className="flex flex-wrap gap-1 mt-1">
          {skills?.map(s => (
            <span key={s} className="text-[9px] bg-white border border-gray-200 text-gray-500 px-1.5 py-0.5 rounded">{s}</span>
          ))}
        </div>
      </div>
      <div className="flex-shrink-0 text-right">
        <p className="text-sm font-bold text-indigo-600">{score}%</p>
        <p className="text-[9px] text-gray-400">match</p>
      </div>
    </div>
  )
}

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div>
      <div className="flex justify-between text-xs text-gray-500 mb-1">
        <span>{label}</span>
        <span className="font-medium text-gray-700">{value}%</span>
      </div>
      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div className={cn('h-full rounded-full', color)} style={{ width: `${value}%` }} />
      </div>
    </div>
  )
}
