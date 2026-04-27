import Anthropic from '@anthropic-ai/sdk'
import { NextRequest, NextResponse } from 'next/server'

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY })
const BACKEND = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8001'

interface RelevantJob {
  job_title: string
  relevance: number
  skills: string[]
}

interface RelevantAlumni {
  alumni_id: string
  first_job_title: string
  faculty: string
  salary_start: number
  success_score: number
  years_to_promotion: number
  similarity: number
}

async function fetchRAGContext(query: string): Promise<string> {
  try {
    const res = await fetch(`${BACKEND}/rag/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, top_k_jobs: 4, top_k_alumni: 3 }),
      signal: AbortSignal.timeout(8000),
    })
    if (!res.ok) return ''

    const data = await res.json()
    const jobs: RelevantJob[] = data.relevant_jobs ?? []
    const alumni: RelevantAlumni[] = data.relevant_alumni ?? []

    const lines: string[] = []

    if (jobs.length > 0) {
      lines.push('## Relevant Job Listings (from database)')
      jobs.forEach((j, i) => {
        const skills = j.skills.slice(0, 6).join(', ')
        lines.push(`${i + 1}. **${j.job_title}** — requires: ${skills}`)
      })
    }

    if (alumni.length > 0) {
      lines.push('\n## Similar Alumni Profiles (from database)')
      alumni.forEach((a, i) => {
        lines.push(
          `${i + 1}. ${a.first_job_title} (${a.faculty}) — ` +
          `starting salary ฿${a.salary_start.toLocaleString()}, ` +
          `promoted in ${a.years_to_promotion} yr(s), ` +
          `success score ${a.success_score}/99`
        )
      })
    }

    return lines.length > 0
      ? `\n\n---\n### Retrieved from Database\n${lines.join('\n')}\n---\n`
      : ''
  } catch {
    return ''
  }
}

function buildRagQuery(userMessage: string, systemContext: string): string {
  const skillsMatch = systemContext.match(/Skills: (.+)/)
  const targetMatch = systemContext.match(/Target career: (.+)/)
  const topJobMatch = systemContext.match(/Top career match: (.+?) \(/)
  const skills = skillsMatch?.[1] ?? ''
  const target = targetMatch?.[1] ?? ''
  const topJob = topJobMatch?.[1] ?? ''
  return [userMessage, skills, target, topJob].filter(Boolean).join(' ')
}

export async function POST(req: NextRequest) {
  try {
    const { messages, systemContext } = await req.json()

    // Extract the latest user message to use as RAG query
    const lastUserMsg = [...messages].reverse().find((m: { role: string }) => m.role === 'user')
    const ragQuery = lastUserMsg?.content ?? ''

    // Enrich query with student skill context for better retrieval
    const enrichedQuery = ragQuery ? buildRagQuery(ragQuery, systemContext) : ''

    // Fetch RAG context in parallel with minimal latency impact
    const ragContext = enrichedQuery ? await fetchRAGContext(enrichedQuery) : ''

    // Inject RAG context into system prompt
    const enrichedSystem = ragContext
      ? `${systemContext}${ragContext}\nUse the retrieved data as silent background context only. Reference specific job titles or alumni examples only when they directly match the student's skills and career path. Do not mention or quote retrieved data that does not match — simply advise based on the student's actual profile.`
      : systemContext

    const response = await client.messages.create({
      model: 'claude-sonnet-4-6',
      max_tokens: 1024,
      system: enrichedSystem,
      messages,
    })

    const text = response.content[0].type === 'text' ? response.content[0].text : ''
    return NextResponse.json({ text, rag_used: ragContext.length > 0 })
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Unknown error'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}
