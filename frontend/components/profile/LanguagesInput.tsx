'use client'

import { useState } from 'react'
import type { SkillItem } from '@/lib/types'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { X } from 'lucide-react'

const LEVELS = ['Beginner', 'Intermediate', 'Advanced', 'Native'] as const
const LEVEL_COLOR: Record<string, string> = {
  Beginner: 'bg-yellow-100 text-yellow-700',
  Intermediate: 'bg-blue-100 text-blue-700',
  Advanced: 'bg-green-100 text-green-700',
  Native: 'bg-purple-100 text-purple-700',
}

interface LanguagesInputProps {
  languages: SkillItem[]
  onChange: (languages: SkillItem[]) => void
}

export default function LanguagesInput({ languages, onChange }: LanguagesInputProps) {
  const [input, setInput] = useState('')
  const [level, setLevel] = useState<SkillItem['level']>('Intermediate')

  const add = () => {
    const name = input.trim()
    if (!name || languages.some(l => l.name.toLowerCase() === name.toLowerCase())) return
    onChange([...languages, { name, level }])
    setInput('')
  }

  const remove = (name: string) => onChange(languages.filter(l => l.name !== name))

  const changeLevel = (name: string, newLevel: SkillItem['level']) =>
    onChange(languages.map(l => l.name === name ? { ...l, level: newLevel } : l))

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <Input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), add())}
          placeholder="Search and add languages…"
          className="flex-1"
        />
        <Select value={level} onValueChange={v => setLevel(v as SkillItem['level'])}>
          <SelectTrigger className="w-36">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {LEVELS.map(l => <SelectItem key={l} value={l}>{l}</SelectItem>)}
          </SelectContent>
        </Select>
        <Button onClick={add} className="bg-indigo-600 hover:bg-indigo-500 text-white px-4">
          Add
        </Button>
      </div>

      <div className="space-y-2">
        {languages.map(lang => (
          <div key={lang.name} className="flex items-center justify-between py-2 border-b border-gray-100">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-700">{lang.name}</span>
              <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${LEVEL_COLOR[lang.level]}`}>
                {lang.level}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Select
                value={lang.level}
                onValueChange={v => changeLevel(lang.name, v as SkillItem['level'])}
              >
                <SelectTrigger className="h-7 w-32 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {LEVELS.map(l => <SelectItem key={l} value={l} className="text-xs">{l}</SelectItem>)}
                </SelectContent>
              </Select>
              <button onClick={() => remove(lang.name)} className="text-red-400 hover:text-red-600">
                <X size={16} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
