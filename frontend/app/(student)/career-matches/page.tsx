'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import { api } from '@/lib/api'
import { storage } from '@/lib/storage'
import type { JobMatch, ArchetypeMatch } from '@/lib/types'
import MatchCard from '@/components/dashboard/MatchCard'
import MatchDetailPanel from '@/components/dashboard/MatchDetailPanel'
import { Button } from '@/components/ui/button'
import { RefreshCw, Loader2, Target, Sparkles } from 'lucide-react'

type AnyMatch = JobMatch | ArchetypeMatch

export default function CareerMatchesPage() {
  const { studentId } = useAuth()
  const [yourTargets, setYourTargets] = useState<JobMatch[]>([])
  const [aiDiscovery, setAiDiscovery] = useState<ArchetypeMatch[]>([])
  const [activeMatch, setActiveMatch] = useState<AnyMatch | null>(null)
  const [savedTargets, setSavedTargets] = useState<string[]>([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    if (!studentId) return
    setLoading(true)
    Promise.all([
      api.matchStudent(studentId, 5),
      api.matchStudentArchetype(studentId, 5),
    ])
      .then(([standard, archetype]) => {
        setYourTargets((standard as any).top_jobs ?? [])
        setAiDiscovery((archetype as any).top_archetypes ?? [])
      })
      .finally(() => setLoading(false))
    setSavedTargets(storage.getTargets())
  }

  useEffect(() => { load() }, [studentId])

  const toggleTarget = (title: string) => {
    if (storage.isTarget(title)) {
      storage.removeTarget(title)
    } else {
      storage.addTarget(title)
    }
    setSavedTargets(storage.getTargets())
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Career Matches</h1>
          <p className="text-gray-500 text-sm mt-1">AI analyzes your profile and ranks careers by compatibility score</p>
        </div>
        <Button onClick={load} className="bg-indigo-600 hover:bg-indigo-500 text-white gap-2">
          <RefreshCw size={15} />
          Re-analyze My Profile
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="animate-spin text-indigo-500" size={32} />
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-8">
          <Column
            title="Your Target"
            subtitle="Based on your career interests and goals."
            icon={<Target size={16} className="text-indigo-500" />}
            matches={yourTargets}
            savedTargets={savedTargets}
            activeMatch={activeMatch}
            onSelect={setActiveMatch}
            onToggleTarget={toggleTarget}
            variant="target"
          />
          <Column
            title="AI Discovery"
            subtitle="Alternative paths where your skills show high success probability."
            icon={<Sparkles size={16} className="text-indigo-500" />}
            matches={aiDiscovery}
            savedTargets={savedTargets}
            activeMatch={activeMatch}
            onSelect={setActiveMatch}
            onToggleTarget={toggleTarget}
            variant="discovery"
          />
        </div>
      )}

      {activeMatch && (
        <div className="fixed right-6 top-20 w-80 z-50">
          <MatchDetailPanel match={activeMatch} onClose={() => setActiveMatch(null)} />
        </div>
      )}
    </div>
  )
}

function Column({
  title, subtitle, icon, matches, savedTargets, activeMatch, onSelect, onToggleTarget, variant,
}: {
  title: string
  subtitle: string
  icon: React.ReactNode
  matches: AnyMatch[]
  savedTargets: string[]
  activeMatch: AnyMatch | null
  onSelect: (m: AnyMatch) => void
  onToggleTarget: (title: string) => void
  variant: 'target' | 'discovery'
}) {
  return (
    <div>
      <div className="mb-4 pb-3 border-b border-l-4 border-l-indigo-500 pl-3">
        <div className="flex items-center gap-2">
          {icon}
          <h2 className="font-semibold text-gray-900">{title}</h2>
        </div>
        <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>
      </div>
      <div className="space-y-4">
        {matches.map((m, i) => {
          const isTarget = savedTargets.includes(m.job_title)
          return (
            <div key={m.job_title + i} className="space-y-2">
              <MatchCard
                match={m}
                index={i}
                isActive={activeMatch === m}
                isTarget={isTarget}
                onClick={() => onSelect(m)}
              />
              <button
                onClick={() => onToggleTarget(m.job_title)}
                className={`w-full py-2 rounded-xl text-xs font-medium transition-colors flex items-center justify-center gap-2 ${
                  isTarget
                    ? variant === 'target'
                      ? 'bg-red-50 text-red-500 hover:bg-red-100 border border-red-100'
                      : 'bg-green-50 text-green-600 border border-green-100'
                    : 'bg-indigo-50 text-indigo-600 hover:bg-indigo-100 border border-indigo-100'
                }`}
              >
                {isTarget
                  ? variant === 'target'
                    ? '🗑 Remove from Targets'
                    : '✓ Current Target'
                  : '🎯 Set as my Target'}
              </button>
            </div>
          )
        })}
      </div>
    </div>
  )
}
