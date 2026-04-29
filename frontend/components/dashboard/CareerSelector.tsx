'use client'

import { cn } from '@/lib/utils'
import type { JobMatch } from '@/lib/types'
import { Star } from 'lucide-react'

interface CareerSelectorProps {
  jobs: JobMatch[]
  savedTitles: string[]
  selected: JobMatch | null
  onSelect: (job: JobMatch) => void
}

export default function CareerSelector({ jobs, savedTitles, selected, onSelect }: CareerSelectorProps) {
  if (!jobs.length) return null

  return (
    <div className="mb-6">
      <p className="text-xs text-gray-400 mb-2 font-medium uppercase tracking-wide">Focus Career</p>
      <div className="flex flex-wrap gap-2">
        {jobs.map((job) => {
          const isSaved = savedTitles.includes(job.job_title)
          const isSelected = selected?.job_title === job.job_title
          return (
            <button
              key={job.job_id ?? job.job_title}
              onClick={() => onSelect(job)}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-all',
                isSelected
                  ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                  : isSaved
                  ? 'bg-indigo-50 text-indigo-700 border-indigo-200 hover:bg-indigo-100'
                  : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50 hover:border-gray-300'
              )}
            >
              {isSaved && (
                <Star
                  size={10}
                  className={isSelected ? 'text-yellow-300' : 'text-indigo-400'}
                  fill="currentColor"
                />
              )}
              {job.job_title}
              <span className={cn('text-[10px]', isSelected ? 'text-indigo-200' : 'text-gray-400')}>
                {Math.round((job.final_score ?? job.match_score) * 100)}%
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
