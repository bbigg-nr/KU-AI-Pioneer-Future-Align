'use client'

import { useRef } from 'react'
import { motion, useMotionValue, useMotionTemplate, animate } from 'framer-motion'
import type { Student } from '@/lib/types'
import { calcStats, calcOVR } from '@/lib/studentScore'

const FACULTY_SHORT: Record<string, string> = {
  'Computer Engineering': 'CPE',
  'Computer Science': 'CS',
  'Engineering': 'ENG',
  'Science': 'SCI',
  'Business Administration': 'BBA',
  'Economics': 'ECON',
}

// ─── Theme ──────────────────────────────────────────────────────────────────

interface Theme {
  cardGrad: string
  photoGrad: string
  statsGrad: string
  textDark: string
  textMid: string
  divider: string
  glow: string
  tier: string
}

function getTheme(ovr: number): Theme {
  if (ovr >= 80) return {
    cardGrad: 'linear-gradient(155deg, #a07320 0%, #e8c840 30%, #f5d860 55%, #c8a030 80%, #8a6010 100%)',
    photoGrad: 'linear-gradient(180deg, #f0d050 0%, #c09030 60%, #906010 100%)',
    statsGrad: 'linear-gradient(180deg, #b08828 0%, #907018 100%)',
    textDark: '#3a2400',
    textMid: '#6a4400cc',
    divider: 'rgba(50,30,0,0.28)',
    glow: '#f0d06055',
    tier: 'GOLD',
  }
  if (ovr >= 65) return {
    cardGrad: 'linear-gradient(155deg, #808288 0%, #c8cad4 30%, #dcdee8 55%, #a8aaB2 80%, #686a70 100%)',
    photoGrad: 'linear-gradient(180deg, #d0d2dc 0%, #a0a2aa 60%, #787a80 100%)',
    statsGrad: 'linear-gradient(180deg, #989aa4 0%, #787a82 100%)',
    textDark: '#1a1c24',
    textMid: '#3a3c44cc',
    divider: 'rgba(20,22,30,0.22)',
    glow: '#c8cad455',
    tier: 'SILVER',
  }
  return {
    cardGrad: 'linear-gradient(155deg, #8a4818 0%, #cc7830 30%, #e09040 55%, #a85c20 80%, #6a3008 100%)',
    photoGrad: 'linear-gradient(180deg, #d08030 0%, #a05c18 60%, #703a08 100%)',
    statsGrad: 'linear-gradient(180deg, #9a5a18 0%, #7a4010 100%)',
    textDark: '#2a1000',
    textMid: '#5a3000cc',
    divider: 'rgba(40,15,0,0.28)',
    glow: '#d0803055',
    tier: 'BRONZE',
  }
}

// ─── Player Silhouette SVG ───────────────────────────────────────────────────

function Silhouette({ color }: { color: string }) {
  return (
    <svg viewBox="0 0 100 140" fill="none" className="w-full h-full">
      <ellipse cx="50" cy="32" rx="20" ry="22" fill={color} opacity="0.82" />
      <path
        d="M18 140 C18 100 28 82 50 78 C72 82 82 100 82 140Z"
        fill={color} opacity="0.78"
      />
      <path
        d="M34 58 C31 68 24 78 18 86 C28 90 40 88 50 88
           C60 88 72 90 82 86 C76 78 69 68 66 58
           C61 66 56 70 50 70 C44 70 39 66 34 58Z"
        fill={color} opacity="0.80"
      />
    </svg>
  )
}

// ─── KU Logo badge ───────────────────────────────────────────────────────────

function KUBadge({ textDark, divider }: { textDark: string; divider: string }) {
  return (
    <div
      className="w-9 h-9 rounded-full flex items-center justify-center"
      style={{ border: `1.5px solid ${divider}`, background: 'rgba(255,255,255,0.18)' }}
    >
      <span style={{ color: textDark, fontSize: 9, fontWeight: 900, letterSpacing: '0.05em' }}>KU</span>
    </div>
  )
}

// ─── Main Card ───────────────────────────────────────────────────────────────

const STAT_ROWS = [
  [{ key: 'tec', label: 'TEC' }, { key: 'col', label: 'COL' }],
  [{ key: 'ana', label: 'ANA' }, { key: 'exp', label: 'EXP' }],
  [{ key: 'com', label: 'COM' }, { key: 'acd', label: 'ACD' }],
] as const

interface FIFACardProps { student: Student; matchCount?: number }

export default function FIFACard({ student, matchCount = 0 }: FIFACardProps) {
  const stats = calcStats(student)
  const ovr = calcOVR(stats)
  const theme = getTheme(ovr)
  const fac = FACULTY_SHORT[student.faculty] ?? student.faculty.slice(0, 4).toUpperCase()
  const displayName = student.name.toUpperCase()
  const hasIncomplete = Object.values(stats).some(s => s.incomplete)

  // FIFA 18 octagonal clip-path
  const clip = 'polygon(13% 0%, 87% 0%, 100% 6%, 100% 94%, 87% 100%, 13% 100%, 0% 94%, 0% 6%)'

  // 3D tilt
  const tiltRef = useRef<HTMLDivElement>(null)
  const rotateX = useMotionValue(0)
  const rotateY = useMotionValue(0)
  const glareX = useMotionValue(50)
  const glareY = useMotionValue(50)
  const glareBackground = useMotionTemplate`radial-gradient(circle at ${glareX}% ${glareY}%, rgba(255,255,255,0.32) 0%, transparent 62%)`

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = tiltRef.current?.getBoundingClientRect()
    if (!rect) return
    const x = (e.clientX - rect.left) / rect.width - 0.5
    const y = (e.clientY - rect.top) / rect.height - 0.5
    rotateX.set(-y * 16)
    rotateY.set(x * 16)
    glareX.set(((e.clientX - rect.left) / rect.width) * 100)
    glareY.set(((e.clientY - rect.top) / rect.height) * 100)
  }

  const handleMouseLeave = () => {
    animate(rotateX, 0, { duration: 0.6, ease: 'easeOut' })
    animate(rotateY, 0, { duration: 0.6, ease: 'easeOut' })
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
      <p className="text-xs text-gray-400 uppercase tracking-wider font-semibold mb-4">
        Student Card
      </p>

      {/* Perspective container — fixed width so mx-auto works */}
      <div
        ref={tiltRef}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        className="mx-auto relative select-none cursor-pointer"
        style={{ width: 208, perspective: '900px' }}
      >
      {/* Tilt + entrance — perspective is on parent so rotation feels grounded */}
      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.5, ease: [0.34, 1.3, 0.64, 1] }}
        style={{ rotateX, rotateY, position: 'relative' }}
        whileTap={{ scale: 0.97 }}
      >
      <div
        className="overflow-hidden"
        style={{
          width: 208,
          clipPath: clip,
          background: theme.cardGrad,
          boxShadow: `0 28px 70px ${theme.glow}, 0 8px 30px rgba(0,0,0,0.45)`,
        }}
      >
        {/* ── Top Row: OVR + Position | KU Logo + Year ── */}
        <div className="flex justify-between items-start px-4 pt-5 pb-0">
          <div className="leading-none">
            <div
              style={{
                color: theme.textDark,
                fontSize: 52,
                fontWeight: 900,
                lineHeight: 1,
                fontVariantNumeric: 'tabular-nums',
              }}
            >
              {ovr}
            </div>
            <div style={{ color: theme.textDark, fontSize: 11, fontWeight: 800, letterSpacing: '0.12em', marginTop: 2 }}>
              {fac}
            </div>
          </div>
          <div className="flex flex-col items-center gap-1.5 mt-1">
            <KUBadge textDark={theme.textDark} divider={theme.divider} />
            <div
              style={{
                color: theme.textDark,
                fontSize: 9,
                fontWeight: 800,
                letterSpacing: '0.1em',
                background: 'rgba(255,255,255,0.18)',
                border: `1px solid ${theme.divider}`,
                borderRadius: 3,
                padding: '1px 6px',
              }}
            >
              Y{student.year}
            </div>
          </div>
        </div>

        {/* ── Photo / Silhouette ── */}
        <div className="relative" style={{ height: 136, overflow: 'hidden' }}>
          {/* soft ground shadow under silhouette */}
          <div
            className="absolute inset-0"
            style={{
              background: `radial-gradient(ellipse 90% 75% at 50% 80%, rgba(0,0,0,0.22) 0%, transparent 70%), radial-gradient(ellipse 70% 60% at 50% 40%, ${theme.glow} 0%, transparent 80%)`,
            }}
          />
          {/* side-light sheen on right edge of silhouette area */}
          <div
            className="absolute inset-0"
            style={{
              background: 'linear-gradient(100deg, transparent 55%, rgba(255,255,255,0.10) 75%, transparent 90%)',
            }}
          />
          <div className="absolute bottom-0 left-1/2" style={{ transform: 'translateX(-50%)', width: 104, height: 128 }}>
            <Silhouette color={theme.textDark} />
          </div>
        </div>

        {/* ── Name ── */}
        <div
          className="text-center px-3 py-1.5"
          style={{ borderBottom: `1px solid ${theme.divider}` }}
        >
          <span
            style={{
              color: theme.textDark,
              fontSize: 13,
              fontWeight: 900,
              letterSpacing: '0.18em',
            }}
          >
            {displayName}
          </span>
          {matchCount > 0 && (
            <div style={{ color: theme.textMid, fontSize: 8, marginTop: 1 }}>
              {matchCount} career matches
            </div>
          )}
        </div>

        {/* ── Stats Section ── */}
        <div style={{ background: theme.statsGrad, padding: '10px 16px 6px' }}>
          {STAT_ROWS.map((row, ri) => (
            <div key={ri} className="flex justify-between mb-1.5">
              {row.map(({ key, label }) => {
                const s = stats[key]
                return (
                  <div key={key} className="flex items-baseline gap-1">
                    <span
                      style={{
                        color: s.incomplete ? '#e05050' : 'white',
                        fontSize: 15,
                        fontWeight: 900,
                        fontVariantNumeric: 'tabular-nums',
                        lineHeight: 1,
                      }}
                    >
                      {s.incomplete ? '–' : s.value}
                    </span>
                    <span
                      style={{
                        color: 'rgba(255,255,255,0.72)',
                        fontSize: 8,
                        fontWeight: 700,
                        letterSpacing: '0.08em',
                      }}
                    >
                      {label}
                    </span>
                  </div>
                )
              })}
            </div>
          ))}

          {/* Card-type row */}
          <div
            className="flex items-center justify-center gap-1 mt-2 pt-1.5"
            style={{ borderTop: `1px solid rgba(255,255,255,0.2)` }}
          >
            {/* small play icon */}
            <svg width="10" height="10" viewBox="0 0 24 24" fill="rgba(255,255,255,0.7)">
              <path d="M8 5v14l11-7z" />
            </svg>
            <span style={{ color: 'rgba(255,255,255,0.75)', fontSize: 8, fontWeight: 800, letterSpacing: '0.18em' }}>
              STUDENT
            </span>
          </div>
        </div>
      </div>

      {/* ── Static shine overlay ── */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          clipPath: clip,
          background: 'linear-gradient(135deg, rgba(255,255,255,0.30) 0%, rgba(255,255,255,0.10) 28%, transparent 55%)',
        }}
      />
      {/* ── Dynamic glare that follows mouse ── */}
      <motion.div
        className="absolute inset-0 pointer-events-none"
        style={{ clipPath: clip, background: glareBackground }}
      />
      {/* ── Top edge bright line ── */}
      <div
        className="absolute pointer-events-none"
        style={{
          top: 0, left: '13%', right: '13%',
          height: '2px',
          background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.75) 40%, rgba(255,255,255,0.75) 60%, transparent)',
        }}
      />
      </motion.div>
      </div>

      {hasIncomplete && (
        <p className="text-center text-[10px] text-gray-400 mt-3">
          – = data not yet filled in profile
        </p>
      )}
    </div>
  )
}
