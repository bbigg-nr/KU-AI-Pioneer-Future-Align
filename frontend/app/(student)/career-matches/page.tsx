'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import { api } from '@/lib/api'
import { storage } from '@/lib/storage'
import type { ArchetypeMatch, JobMatch } from '@/lib/types'
import MatchCard from '@/components/dashboard/MatchCard'
import MatchDetailPanel from '@/components/dashboard/MatchDetailPanel'
import { Button } from '@/components/ui/button'
import { RefreshCw, Loader2, Target, Sparkles, Plus, Trash2 } from 'lucide-react'

/** Dedup by job_title — keep best final_score per title, sorted desc */
function dedupByTitle(jobs: JobMatch[]): JobMatch[] {
  const map = new Map<string, JobMatch>()
  for (const job of jobs) {
    const cur = map.get(job.job_title)
    const score = (j: JobMatch) => j.final_score ?? j.match_score
    if (!cur || score(job) > score(cur)) map.set(job.job_title, job)
  }
  return Array.from(map.values()).sort(
    (a, b) => (b.final_score ?? b.match_score) - (a.final_score ?? a.match_score)
  )
}

export default function CareerMatchesPage() {
  const { studentId } = useAuth()
  const [blendedJobs, setBlendedJobs] = useState<JobMatch[]>([])
  const [archetypeMap, setArchetypeMap] = useState<Map<string, ArchetypeMatch[]>>(new Map())
  const [activeMatch, setActiveMatch] = useState<JobMatch | null>(null)
  const [savedTitles, setSavedTitles] = useState<string[]>([])
  const [loading, setLoading] = useState(true)

  const refreshSaved = () => setSavedTitles(storage.getTargets())

  const load = () => {
    if (!studentId) return
    setLoading(true)
    refreshSaved()
    Promise.all([
      api.matchStudentBlended(studentId, 20),
      api.matchStudentArchetype(studentId, 20),
    ])
      .then(([blended, archetype]) => {
        setBlendedJobs(dedupByTitle((blended as any).top_jobs ?? []))

        // Build archetype map: job_title → ArchetypeMatch[]
        const aMap = new Map<string, ArchetypeMatch[]>()
        for (const arch of (archetype as any).top_archetypes ?? [] as ArchetypeMatch[]) {
          const list = aMap.get(arch.job_title) ?? []
          list.push(arch)
          aMap.set(arch.job_title, list)
        }
        setArchetypeMap(aMap)
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [studentId])

  const toggleSaved = (title: string) => {
    if (storage.isTarget(title)) {
      storage.removeTarget(title)
    } else {
      storage.addTarget(title)
      if (studentId) {
        api.updateStudent(studentId, { target_career: title }).catch(console.error)
      }
    }
    refreshSaved()
  }

  const savedJobs = blendedJobs.filter(j => savedTitles.includes(j.job_title))
  const discoveryJobs = blendedJobs.filter(j => !savedTitles.includes(j.job_title)).slice(0, 10)

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
          {/* Left: My Saved Targets */}
          <div>
            <div className="mb-4 pb-3 border-b border-l-4 border-l-indigo-500 pl-3">
              <div className="flex items-center gap-2">
                <Target size={16} className="text-indigo-500" />
                <h2 className="font-semibold text-gray-900">My Target Careers</h2>
              </div>
              <p className="text-xs text-gray-400 mt-0.5">
                Careers you&apos;ve added from AI Discovery.
              </p>
            </div>
            <div className="space-y-4">
              {savedJobs.length === 0 ? (
                <div className="text-center py-12 text-gray-400 border-2 border-dashed border-gray-200 rounded-2xl">
                  <Target size={32} className="mx-auto mb-3 opacity-40" />
                  <p className="text-sm font-medium">No targets yet</p>
                  <p className="text-xs mt-1">Add careers from AI Discovery →</p>
                </div>
              ) : (
                savedJobs.map((job, i) => (
                  <div key={job.job_title} className="space-y-2">
                    <MatchCard
                      match={job}
                      variations={archetypeMap.get(job.job_title) ?? []}
                      index={i}
                      isActive={activeMatch?.job_title === job.job_title}
                      isTarget={true}
                      onClick={() => setActiveMatch(job)}
                    />
                    <button
                      onClick={() => toggleSaved(job.job_title)}
                      className="w-full py-2.5 rounded-xl text-xs font-semibold transition-all duration-300 flex items-center justify-center gap-2 bg-white text-slate-400 border border-slate-200 hover:bg-rose-50 hover:text-rose-600 hover:border-rose-200 hover:shadow-md hover:shadow-rose-100/50 hover:-translate-y-0.5 group"
                    >
                      <Trash2 size={14} className="transition-transform duration-300 group-hover:scale-110 group-hover:-rotate-12" />
                      Remove from My List
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Right: AI Discovery */}
          <div>
            <div className="mb-4 pb-3 border-b border-l-4 border-l-indigo-500 pl-3">
              <div className="flex items-center gap-2">
                <Sparkles size={16} className="text-indigo-500" />
                <h2 className="font-semibold text-gray-900">AI Discovery</h2>
              </div>
              <p className="text-xs text-gray-400 mt-0.5">
                Alternative paths where your skills show high success probability.
              </p>
            </div>
            <div className="space-y-4">
              {discoveryJobs.map((job, i) => (
                <div key={job.job_title} className="space-y-2">
                  <MatchCard
                    match={job}
                    variations={archetypeMap.get(job.job_title) ?? []}
                    index={i}
                    isActive={activeMatch?.job_title === job.job_title}
                    isTarget={false}
                    onClick={() => setActiveMatch(job)}
                  />
                  <button
                    onClick={() => toggleSaved(job.job_title)}
                    className="w-full py-2.5 rounded-xl text-xs font-bold transition-all duration-300 flex items-center justify-center gap-2 bg-gradient-to-br from-indigo-50 to-blue-50/50 text-indigo-600 border border-indigo-200/60 hover:border-indigo-400 hover:shadow-lg hover:shadow-indigo-100/60 hover:-translate-y-0.5 group"
                  >
                    <Plus size={14} className="transition-transform duration-300 group-hover:rotate-90 group-hover:scale-125" />
                    Add to My List
                  </button>
                </div>
              ))}
            </div>
          </div>
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
