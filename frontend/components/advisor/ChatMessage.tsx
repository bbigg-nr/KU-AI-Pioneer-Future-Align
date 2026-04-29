'use client'

import dynamic from 'next/dynamic'
const ReactMarkdown = dynamic(() => import('react-markdown'), { ssr: false })
import type { ChatMessage as Msg } from '@/lib/types'
import { GraduationCap } from 'lucide-react'
import { cn } from '@/lib/utils'

export default function ChatMessage({ message }: { message: Msg }) {
  const isUser = message.role === 'user'
  const showRagBadge = !isUser && message.rag_used

  return (
    <div className={cn('flex gap-3 mb-4', isUser ? 'flex-row-reverse' : 'flex-row')}>
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-indigo-500 flex items-center justify-center">
          <GraduationCap size={14} className="text-white" />
        </div>
      )}
      <div
        className={cn(
          'max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed',
          isUser
            ? 'bg-gray-800 text-white rounded-tr-none'
            : 'bg-white border border-gray-100 text-gray-800 rounded-tl-none shadow-sm'
        )}
      >
        {isUser ? (
          <p>{message.content}</p>
        ) : (
          <>
            <ReactMarkdown
              components={{
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                ul: ({ children }) => <ul className="list-disc pl-4 mb-2 space-y-1">{children}</ul>,
                li: ({ children }) => <li>{children}</li>,
                strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
              }}
            >
              {message.content}
            </ReactMarkdown>
            {showRagBadge && (
              <div className="mt-2 pt-2 border-t border-gray-100">
                <span className="text-[10px] text-indigo-400 font-medium flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 inline-block" />
                  Retrieved from database
                </span>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
