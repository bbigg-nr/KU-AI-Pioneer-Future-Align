import { NextRequest, NextResponse } from 'next/server'

const BACKEND = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8080'

export async function POST(req: NextRequest) {
  try {
    const { messages, systemContext, student_id } = await req.json()

    // Proxy to backend LangChain AI Advisor
    const res = await fetch(`${BACKEND}/ai/advisor/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages, system_context: systemContext, student_id }),
      signal: AbortSignal.timeout(30000),
    })

    if (!res.ok) {
      const err = await res.text()
      return NextResponse.json({ error: err }, { status: res.status })
    }

    const data = await res.json()
    return NextResponse.json({
      text: data.text,
      rag_used: data.rag_used ?? false,
      tools_used: data.tools_used ?? [],
    })
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Unknown error'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}
