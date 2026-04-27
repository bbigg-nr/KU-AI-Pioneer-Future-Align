'use client'

import { useState } from 'react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Send } from 'lucide-react'

interface ChatInputProps {
  onSend: (message: string) => void
  isLoading: boolean
  suggestions?: string[]
}

export default function ChatInput({ onSend, isLoading, suggestions = [] }: ChatInputProps) {
  const [input, setInput] = useState('')

  const send = () => {
    const msg = input.trim()
    if (!msg || isLoading) return
    onSend(msg)
    setInput('')
  }

  return (
    <div className="border-t border-gray-100 bg-white px-6 py-4">
      {suggestions.length > 0 && (
        <div className="flex gap-2 mb-3 flex-wrap">
          {suggestions.map(s => (
            <button
              key={s}
              onClick={() => onSend(s)}
              disabled={isLoading}
              className="text-xs px-3 py-1.5 rounded-full bg-gray-100 text-gray-600 hover:bg-indigo-50 hover:text-indigo-600 transition-colors"
            >
              {s}
            </button>
          ))}
        </div>
      )}
      <div className="flex gap-3">
        <Input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), send())}
          placeholder="ถามเกี่ยวกับเส้นทางอาชีพของคุณ…"
          disabled={isLoading}
          className="flex-1"
        />
        <Button
          onClick={send}
          disabled={isLoading || !input.trim()}
          className="bg-indigo-600 hover:bg-indigo-500 text-white"
        >
          <Send size={16} />
        </Button>
      </div>
    </div>
  )
}
