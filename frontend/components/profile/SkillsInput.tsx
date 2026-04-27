'use client'

import { useState } from 'react'
import type { SkillItem } from '@/lib/types'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { X } from 'lucide-react'
import { Badge } from '@/components/ui/badge'

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

  const add = () => {
    const name = input.trim()
    if (!name || skills.some(s => s.name.toLowerCase() === name.toLowerCase())) return
    onChange([...skills, { name, level }])
    setInput('')
  }

  const remove = (name: string) => onChange(skills.filter(s => s.name !== name))

  const changeLevel = (name: string, newLevel: SkillItem['level']) =>
    onChange(skills.map(s => s.name === name ? { ...s, level: newLevel } : s))

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <Input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), add())}
          placeholder={placeholder}
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
