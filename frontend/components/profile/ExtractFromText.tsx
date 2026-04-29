'use client'

import { useRef, useState } from 'react'
import type { SkillItem } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Loader2, Sparkles, ChevronDown, ChevronUp, Plus, Check, FileText, UploadCloud, X } from 'lucide-react'

const LEVEL_COLOR: Record<string, string> = {
  Beginner: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  Intermediate: 'bg-blue-100 text-blue-700 border-blue-200',
  Advanced: 'bg-green-100 text-green-700 border-green-200',
}

interface ExtractResult {
  skills: SkillItem[]
  activities: string[]
}

interface ExtractFromTextProps {
  existingSkills: SkillItem[]
  existingActivities: string[]
  onMerge: (skills: SkillItem[], activities: string[]) => void
}

export default function ExtractFromText({ existingSkills, existingActivities, onMerge }: ExtractFromTextProps) {
  const [open, setOpen] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<ExtractResult | null>(null)
  const [selectedSkills, setSelectedSkills] = useState<Set<string>>(new Set())
  const [selectedActivities, setSelectedActivities] = useState<Set<string>>(new Set())
  const inputRef = useRef<HTMLInputElement>(null)

  const acceptFile = (f: File | null) => {
    if (!f) return
    if (f.type !== 'application/pdf') { setError('Please upload a PDF file.'); return }
    if (f.size > 10 * 1024 * 1024) { setError('PDF must be under 10 MB.'); return }
    setFile(f)
    setError('')
    setResult(null)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    acceptFile(e.dataTransfer.files[0] ?? null)
  }

  const handleExtract = async () => {
    if (!file) return
    setLoading(true)
    setError('')
    setResult(null)

    try {
      const form = new FormData()
      form.append('pdf', file)

      const res = await fetch('/api/extract-skills', { method: 'POST', body: form })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error ?? 'Extraction failed')

      const newSkills: SkillItem[] = (data.skills as SkillItem[]).filter(
        s => !existingSkills.some(e => e.name.toLowerCase() === s.name.toLowerCase())
      )
      const newActivities: string[] = (data.activities as string[]).filter(
        a => !existingActivities.includes(a)
      )

      setResult({ skills: newSkills, activities: newActivities })
      setSelectedSkills(new Set(newSkills.map(s => s.name)))
      setSelectedActivities(new Set(newActivities))
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const toggleSkill = (name: string) =>
    setSelectedSkills(prev => { const n = new Set(prev); n.has(name) ? n.delete(name) : n.add(name); return n })

  const toggleActivity = (a: string) =>
    setSelectedActivities(prev => { const n = new Set(prev); n.has(a) ? n.delete(a) : n.add(a); return n })

  const handleAddSelected = () => {
    onMerge(
      result?.skills.filter(s => selectedSkills.has(s.name)) ?? [],
      result?.activities.filter(a => selectedActivities.has(a)) ?? [],
    )
    setResult(null)
    setFile(null)
    setSelectedSkills(new Set())
    setSelectedActivities(new Set())
  }

  const reset = () => { setFile(null); setResult(null); setError('') }

  const totalSelected = selectedSkills.size + selectedActivities.size
  const hasResult = result && (result.skills.length > 0 || result.activities.length > 0)
  const isEmpty = result && result.skills.length === 0 && result.activities.length === 0

  return (
    <div className="rounded-xl border border-dashed border-indigo-300 bg-indigo-50/40 overflow-hidden">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-indigo-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Sparkles size={15} className="text-indigo-500" />
          <span className="text-sm font-medium text-indigo-700">Extract from Resume PDF</span>
          <span className="text-xs text-indigo-400">— upload your CV and let AI extract your skills</span>
        </div>
        {open ? <ChevronUp size={15} className="text-indigo-400" /> : <ChevronDown size={15} className="text-indigo-400" />}
      </button>

      {open && (
        <div className="px-4 pb-4 space-y-3 border-t border-indigo-200">
          {/* Drop zone */}
          {!file ? (
            <div
              onDragOver={e => { e.preventDefault(); setDragging(true) }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
              onClick={() => inputRef.current?.click()}
              className={`mt-3 flex flex-col items-center justify-center gap-2 h-28 rounded-lg border-2 border-dashed cursor-pointer transition-colors ${
                dragging ? 'border-indigo-400 bg-indigo-100' : 'border-indigo-200 bg-white hover:bg-indigo-50'
              }`}
            >
              <UploadCloud size={24} className="text-indigo-400" />
              <p className="text-sm text-indigo-600 font-medium">Drop your PDF here or click to browse</p>
              <p className="text-xs text-gray-400">PDF only · max 10 MB</p>
              <input
                ref={inputRef}
                type="file"
                accept="application/pdf"
                className="hidden"
                onChange={e => acceptFile(e.target.files?.[0] ?? null)}
              />
            </div>
          ) : (
            <div className="mt-3 flex items-center justify-between rounded-lg border border-indigo-200 bg-white px-3 py-2.5">
              <div className="flex items-center gap-2">
                <FileText size={16} className="text-indigo-500 shrink-0" />
                <span className="text-sm text-gray-700 truncate max-w-xs">{file.name}</span>
                <span className="text-xs text-gray-400">({(file.size / 1024).toFixed(0)} KB)</span>
              </div>
              <button onClick={reset} className="text-gray-400 hover:text-gray-600 ml-2">
                <X size={14} />
              </button>
            </div>
          )}

          <div className="flex items-center gap-2">
            <Button
              onClick={handleExtract}
              disabled={loading || !file}
              className="bg-indigo-600 hover:bg-indigo-500 text-white text-sm px-4 h-8"
            >
              {loading
                ? <><Loader2 size={14} className="animate-spin mr-1.5" />Extracting…</>
                : <><Sparkles size={14} className="mr-1.5" />Extract</>}
            </Button>
            {result && (
              <button onClick={reset} className="text-xs text-gray-400 hover:text-gray-600">Clear</button>
            )}
          </div>

          {error && <p className="text-xs text-red-500">{error}</p>}

          {isEmpty && (
            <p className="text-xs text-gray-500 italic">No new skills or activities found in this PDF.</p>
          )}

          {hasResult && (
            <div className="space-y-4 pt-1">
              {result.skills.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                    Skills found ({result.skills.length} new)
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {result.skills.map(skill => {
                      const selected = selectedSkills.has(skill.name)
                      return (
                        <button
                          key={skill.name}
                          onClick={() => toggleSkill(skill.name)}
                          className={`flex items-center gap-1.5 text-xs rounded-full px-3 py-1 border transition-all ${
                            selected
                              ? LEVEL_COLOR[skill.level] + ' ring-1 ring-indigo-400'
                              : 'bg-gray-100 text-gray-400 border-gray-200 opacity-60'
                          }`}
                        >
                          {selected ? <Check size={10} /> : <Plus size={10} />}
                          {skill.name}
                          <span className="font-medium">{skill.level}</span>
                        </button>
                      )
                    })}
                  </div>
                </div>
              )}

              {result.activities.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                    Activities found ({result.activities.length} new)
                  </p>
                  <div className="space-y-1.5">
                    {result.activities.map(a => {
                      const selected = selectedActivities.has(a)
                      return (
                        <button
                          key={a}
                          onClick={() => toggleActivity(a)}
                          className={`flex items-center gap-2 w-full text-left text-xs rounded-lg px-3 py-2 border transition-all ${
                            selected
                              ? 'bg-indigo-50 border-indigo-300 text-indigo-800 ring-1 ring-indigo-300'
                              : 'bg-gray-50 border-gray-200 text-gray-400 opacity-60'
                          }`}
                        >
                          {selected
                            ? <Check size={11} className="shrink-0 text-indigo-500" />
                            : <Plus size={11} className="shrink-0" />}
                          {a}
                        </button>
                      )
                    })}
                  </div>
                </div>
              )}

              <Button
                onClick={handleAddSelected}
                disabled={totalSelected === 0}
                className="w-full h-9 bg-indigo-600 hover:bg-indigo-500 text-white text-sm"
              >
                <Plus size={14} className="mr-1.5" />
                Add {totalSelected} selected item{totalSelected !== 1 ? 's' : ''} to profile
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
