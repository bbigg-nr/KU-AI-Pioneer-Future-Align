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
}

const LEVEL_SCORE: Record<string, number> = {
  Beginner: 33,
  Intermediate: 66,
  Advanced: 100,
  Native: 100,
}

export function levelToScore(level: string) {
  return LEVEL_SCORE[level] ?? 50
}

export default function SkillRadar({ data, title = 'Skills vs Market Demand' }: SkillRadarProps) {
  if (!data.length) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
        <p className="text-sm font-semibold text-gray-700 mb-4">{title}</p>
        <p className="text-gray-400 text-sm text-center py-8">No skill data available</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
      <p className="text-sm font-semibold text-gray-700 mb-4">{title}</p>
      <ResponsiveContainer width="100%" height={280}>
        <RadarChart data={data} margin={{ top: 10, right: 20, bottom: 10, left: 20 }}>
          <PolarGrid stroke="#e5e7eb" />
          <PolarAngleAxis
            dataKey="skill"
            tick={{ fontSize: 11, fill: '#6b7280' }}
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
            wrapperStyle={{ fontSize: 12 }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}
