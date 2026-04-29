'use client'

import { useState, useEffect, useRef } from 'react'
import type { SkillItem } from '@/lib/types'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { X } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { api } from '@/lib/api'

const LEVELS = ['Beginner', 'Intermediate', 'Advanced'] as const
const LEVEL_COLOR: Record<string, string> = {
  Beginner: 'bg-yellow-100 text-yellow-700',
  Intermediate: 'bg-blue-100 text-blue-700',
  Advanced: 'bg-green-100 text-green-700',
  Native: 'bg-purple-100 text-purple-700',
}

interface SkillsInputProps {
  skills: SkillItem[]
  onChange: (skills: SkillItem[]) => void
  placeholder?: string
}

export default function SkillsInput({ skills, onChange, placeholder = 'Search and add skills…' }: SkillsInputProps) {
  const [input, setInput] = useState('')
  const [level, setLevel] = useState<SkillItem['level']>('Intermediate')
  const [pool, setPool] = useState<string[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const wrapperRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    api.getSkillPool().then(res => setPool(res.skills)).catch(console.error)
  }, [])

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setShowSuggestions(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const query = input.trim().toLowerCase()
  const filteredPool = !query ? [] : pool
    .filter(s => {
      const lowerS = s.toLowerCase()
      return lowerS.includes(query) && !skills.some(es => es.name.toLowerCase() === lowerS)
    })
    .sort((a, b) => {
      const aLower = a.toLowerCase()
      const bLower = b.toLowerCase()
      
      const aExact = aLower === query ? 1 : 0
      const bExact = bLower === query ? 1 : 0
      if (aExact !== bExact) return bExact - aExact
      
      const aStarts = aLower.startsWith(query) ? 1 : 0
      const bStarts = bLower.startsWith(query) ? 1 : 0
      if (aStarts !== bStarts) return bStarts - aStarts
      
      return aLower.localeCompare(bLower)
    })
    .slice(0, 10)

  const add = (skillName?: string) => {
    const name = (skillName || input).trim()
    if (!name || skills.some(s => s.name.toLowerCase() === name.toLowerCase())) return
    onChange([...skills, { name, level }])
    setInput('')
    setShowSuggestions(false)
  }

  const remove = (name: string) => onChange(skills.filter(s => s.name !== name))

  const changeLevel = (name: string, newLevel: SkillItem['level']) =>
    onChange(skills.map(s => s.name === name ? { ...s, level: newLevel } : s))

  return (
    <div className="space-y-3">
      <div className="flex gap-2 relative" ref={wrapperRef}>
        <div className="relative flex-1">
          <Input
            value={input}
            onChange={e => {
              setInput(e.target.value)
              setShowSuggestions(true)
            }}
            onFocus={() => setShowSuggestions(true)}
            onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), add())}
            placeholder={placeholder}
            className="w-full"
          />
          {showSuggestions && input && filteredPool.length > 0 && (
            <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-y-auto">
              {filteredPool.map(skillName => (
                <div
                  key={skillName}
                  className="px-4 py-2 text-sm text-gray-700 hover:bg-indigo-50 cursor-pointer"
                  onClick={() => add(skillName)}
                >
                  {skillName}
                </div>
              ))}
            </div>
          )}
        </div>
        <Select value={level} onValueChange={v => setLevel(v as SkillItem['level'])}>
          <SelectTrigger className="w-36">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {LEVELS.map(l => <SelectItem key={l} value={l}>{l}</SelectItem>)}
          </SelectContent>
        </Select>
        <Button onClick={() => add()} className="bg-indigo-600 hover:bg-indigo-500 text-white px-4">
          Add
        </Button>
      </div>

      <div className="space-y-2">
        {skills.map(skill => (
          <div key={skill.name} className="flex items-center justify-between py-2 border-b border-gray-100">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-700">{skill.name}</span>
              <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${LEVEL_COLOR[skill.level]}`}>
                {skill.level}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Select
                value={skill.level}
                onValueChange={v => changeLevel(skill.name, v as SkillItem['level'])}
              >
                <SelectTrigger className="h-7 w-32 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {LEVELS.map(l => <SelectItem key={l} value={l} className="text-xs">{l}</SelectItem>)}
                </SelectContent>
              </Select>
              <button onClick={() => remove(skill.name)} className="text-red-400 hover:text-red-600">
                <X size={16} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
