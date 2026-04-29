'use client'

import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  ResponsiveContainer,
  Legend,
} from 'recharts'

interface SkillRadarData {
  skill: string
  current: number
  required: number
}

interface SkillRadarProps {
  data: SkillRadarData[]
  title?: string
  theme?: 'light' | 'dark'
}

export default function SkillRadar({ data, title = 'Skills vs Market Demand', theme = 'light' }: SkillRadarProps) {
  const isDark = theme === 'dark'
  
  if (!data.length) {
    return (
      <div className={isDark ? "py-8" : "bg-white rounded-2xl border border-gray-100 p-6 shadow-sm"}>
        {title && <p className={`text-sm font-semibold mb-4 ${isDark ? 'text-white/80' : 'text-gray-700'}`}>{title}</p>}
        <p className={`${isDark ? 'text-white/40' : 'text-gray-400'} text-sm text-center py-8`}>No skill data available</p>
      </div>
    )
  }

  return (
    <div className={isDark ? "" : "bg-white rounded-2xl border border-gray-100 p-6 shadow-sm"}>
      {title && <p className={`text-sm font-semibold mb-4 ${isDark ? 'text-white/80' : 'text-gray-700'}`}>{title}</p>}
      <ResponsiveContainer width="100%" height={isDark ? 220 : 280}>
        <RadarChart cx="50%" cy="50%" outerRadius={isDark ? "60%" : "70%"} data={data} margin={{ top: 10, right: 30, bottom: 10, left: 30 }}>
          <PolarGrid stroke={isDark ? "#ffffff20" : "#e5e7eb"} />
          <PolarAngleAxis
            dataKey="skill"
            tick={{ fontSize: 10, fill: isDark ? '#9ca3af' : '#6b7280' }}
          />
          <Radar
            name="Your Skills"
            dataKey="current"
            stroke="#6366f1"
            fill="#6366f1"
            fillOpacity={0.3}
          />
          <Radar
            name="Market Demand"
            dataKey="required"
            stroke="#3b82f6"
            fill="#3b82f6"
            fillOpacity={0.15}
            strokeDasharray="4 2"
          />
          <Legend
            iconType="square"
            iconSize={10}
            wrapperStyle={{ fontSize: 11, color: isDark ? '#9ca3af' : '#6b7280' }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}
