'use client'

import { useEffect, useRef, useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import { api } from '@/lib/api'
import type { ChatMessage as Msg, Student, BlendedResult } from '@/lib/types'
import ChatMessage from '@/components/advisor/ChatMessage'
import ChatInput from '@/components/advisor/ChatInput'
import { GraduationCap, Loader2 } from 'lucide-react'

const SUGGESTIONS = [
  'บอกรายละเอียดเพิ่มเติมหน่อย',
  'ต่อไปไหนแล้ว?',
  'แสดงใบรับรองที่ควรมีหน่อย',
  'What skills should I focus on?',
]

function buildSystemPrompt(student: Student, topJob?: string, matchScore?: number): string {
  const skillList = student.skills.map(s => `${s.name} (${s.level})`).join(', ')
  return `You are FutureAlign AI Advisor, a career guidance assistant for Kasetsart University (KU) students.

Student Profile:
- Name: ${student.name}
- Faculty: ${student.faculty}
- Year: ${student.year}, GPA: ${student.gpa}
- Skills: ${skillList}
- Target career: ${student.target_career}
${topJob ? `- Top career match: ${topJob} (${Math.round((matchScore ?? 0) * 100)}% match)` : ''}

Instructions:
- Be encouraging, specific, and actionable
- Answer in the same language the user writes (Thai or English)
- Reference their actual skills and career match when giving advice
- Keep responses concise (3-5 sentences unless detail is needed)
- Use bullet points for lists`
}

export default function AdvisorPage() {
  const { studentId } = useAuth()
  const [student, setStudent] = useState<Student | null>(null)
  const [blended, setBlended] = useState<BlendedResult | null>(null)
  const [messages, setMessages] = useState<Msg[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [dataLoading, setDataLoading] = useState(true)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!studentId) return
    Promise.all([api.getStudent(studentId), api.matchStudentBlended(studentId, 3)])
      .then(([s, b]) => { setStudent(s); setBlended(b) })
      .finally(() => setDataLoading(false))
  }, [studentId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  useEffect(() => {
    if (!student || messages.length > 0) return
    const topJob = blended?.top_jobs[0]
    const greeting = `สวัสดีครับคุณ ${student.name}! ผมได้วิเคราะห์โปรไฟล์ของคุณแล้ว พบว่าคุณมีพื้นฐานที่ดีมากสำหรับสาย **${topJob?.job_title ?? student.target_career}** มีอะไรให้ช่วยวางแผนหรือแนะนำไหมครับ?`
    setMessages([{ role: 'assistant', content: greeting }])
  }, [student, blended])

  const sendMessage = async (text: string) => {
    if (!student) return
    const userMsg: Msg = { role: 'user', content: text }
    const newMessages = [...messages, userMsg]
    setMessages(newMessages)
    setIsLoading(true)

    try {
      const topJob = blended?.top_jobs[0]
      const systemContext = buildSystemPrompt(student, topJob?.job_title, topJob?.final_score)
      const apiMessages = newMessages.map(m => ({ role: m.role, content: m.content }))

      const res = await fetch('/api/advisor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: apiMessages, systemContext }),
      })
      const data = await res.json()
      if (data.text) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.text,
          rag_used: data.rag_used,
        } as Msg])
      }
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }])
    } finally {
      setIsLoading(false)
    }
  }

  if (dataLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-indigo-500" size={32} />
      </div>
    )
  }

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] -m-8">
      <div className="flex items-center gap-3 px-6 py-4 bg-white border-b border-gray-100 shadow-sm">
        <div className="w-10 h-10 rounded-full bg-indigo-500 flex items-center justify-center">
          <GraduationCap size={20} className="text-white" />
        </div>
        <div>
          <h1 className="font-bold text-gray-900">FutureAlign AI Advisor</h1>
          <p className="text-xs text-gray-400">Smart Academic Advisor · powered by Claude</p>
        </div>
        {isLoading && (
          <div className="ml-auto flex items-center gap-2 text-xs text-gray-400">
            <Loader2 size={12} className="animate-spin" />
            Thinking…
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6 bg-gray-50">
        {messages.length === 0 && !dataLoading && (
          <div className="text-center py-12 text-gray-400">
            <GraduationCap size={40} className="mx-auto mb-3 text-gray-300" />
            <p className="font-medium">Career Guidance AI</p>
            <p className="text-sm mt-1">Ask me anything about your career path</p>
          </div>
        )}
        {messages.map((m, i) => <ChatMessage key={i} message={m} />)}
        {isLoading && (
          <div className="flex gap-3 mb-4">
            <div className="w-8 h-8 rounded-full bg-indigo-500 flex items-center justify-center flex-shrink-0">
              <GraduationCap size={14} className="text-white" />
            </div>
            <div className="bg-white border border-gray-100 rounded-2xl rounded-tl-none px-4 py-3 shadow-sm">
              <div className="flex gap-1">
                {[0, 1, 2].map(i => (
                  <span key={i} className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
                ))}
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <ChatInput onSend={sendMessage} isLoading={isLoading} suggestions={messages.length <= 1 ? SUGGESTIONS : []} />
    </div>
  )
}
