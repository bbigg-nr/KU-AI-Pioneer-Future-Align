import type { Student } from './types'

const LEVEL_SCORE: Record<string, number> = {
  Native: 99, Advanced: 92, Intermediate: 77, Beginner: 52,
}

const LANGUAGE_NAMES = new Set([
  'thai', 'english', 'chinese', 'japanese', 'korean',
  'french', 'german', 'spanish', 'mandarin', 'cantonese',
])

const SOFT_SKILL_KW = [
  'communication', 'leadership', 'teamwork', 'presentation', 'interpersonal',
  'public speaking', 'negotiation', 'time management', 'adaptability',
  'creativity', 'critical thinking', 'problem solving', 'emotional',
  'networking', 'mentoring', 'coaching', 'facilitation',
]

const ANALYTICAL_KW = [
  'data', 'statistics', 'analytics', 'sql', 'excel', 'tableau', 'power bi',
  'looker', 'bigquery', 'spark', 'dbt', 'snowflake', 'databricks',
  'pandas', 'numpy', 'matplotlib', 'scipy', 'stata', 'spss', 'matlab', 'r ',
  'machine learning', 'deep learning', 'neural', 'pytorch', 'tensorflow',
  'keras', 'scikit', 'transformers', 'hugging', 'mlops', 'model', 'llm',
  'nlp', 'computer vision', 'reinforcement', 'langchain', 'embedding',
  'econometrics', 'valuation', 'dcf', 'risk management', 'bloomberg',
  'equity', 'factor invest', 'portfolio', 'quantitative', 'financial model',
  'accounting', 'forecast', 'var', 'cvar', 'derivatives', 'fixed income',
  'algorithm', 'optimization', 'simulation', 'computational', 'numerical',
  'regression', 'modelling', 'research', 'experiment',
]

const COM_ROLES = ['president', 'speaker', 'host', 'pr', 'secretary', 'representative', 'journalist', 'editor', 'writer']
const COL_ROLES = ['lead', 'head', 'team', 'committee', 'member', 'coordinator', 'manager', 'director', 'officer', 'vice']

export interface StatEntry { value: number; incomplete: boolean }
export interface StudentStats {
  tec: StatEntry; ana: StatEntry; com: StatEntry
  col: StatEntry; exp: StatEntry; acd: StatEntry
}

function parseRoles(activities: string): string[] {
  if (!activities) return []
  const results: string[] = []
  for (const m of activities.matchAll(/\[([^\]]+)\]\s+at\s+\[/g)) results.push(m[1])
  if (results.length > 0) return results
  for (const m of activities.matchAll(/\[?([^\]\[|]+?)\]?\s+at\s+\[?[^\]\[|]+\]?/g)) {
    const role = m[1].trim()
    if (role) results.push(role)
  }
  return results
}

function avgLevelScore(items: { level: string }[]): number {
  return Math.round(items.reduce((s, i) => s + (LEVEL_SCORE[i.level] ?? 20), 0) / items.length)
}

export function calcStats(student: Student): StudentStats {
  const techSkills = student.skills.filter(s => {
    const n = s.name.toLowerCase().trim()
    return !LANGUAGE_NAMES.has(n) && !SOFT_SKILL_KW.some(kw => n.includes(kw))
  })
  const tec: StatEntry = techSkills.length > 0
    ? { value: Math.min(99, avgLevelScore(techSkills)), incomplete: false }
    : { value: 20, incomplete: true }

  const analyticalSkills = techSkills.filter(s =>
    ANALYTICAL_KW.some(kw => s.name.toLowerCase().includes(kw))
  )
  const ana: StatEntry = analyticalSkills.length > 0
    ? { value: Math.min(99, avgLevelScore(analyticalSkills)), incomplete: false }
    : { value: 20, incomplete: true }

  const roles = parseRoles(student.activities ?? '')
  const langLen = student.languages.length
  const langAvg = langLen > 0 ? avgLevelScore(student.languages) : 0
  const comRoleCount = roles.filter(r => COM_ROLES.some(k => r.toLowerCase().includes(k))).length
  const comHasData = langLen > 0 || comRoleCount > 0
  const com: StatEntry = comHasData
    ? { value: Math.min(99, Math.round((langLen > 0 ? langAvg * 0.6 : 30) + comRoleCount * 8 + 22)), incomplete: false }
    : { value: 20, incomplete: true }

  const colRoleCount = roles.filter(r => COL_ROLES.some(k => r.toLowerCase().includes(k))).length
  const col: StatEntry = roles.length > 0
    ? { value: Math.min(99, 32 + colRoleCount * 12 + roles.length * 3), incomplete: false }
    : { value: 20, incomplete: true }

  const exp: StatEntry = roles.length > 0
    ? { value: Math.min(99, 28 + roles.length * 11), incomplete: false }
    : { value: 20, incomplete: true }

  const acd: StatEntry = student.gpa > 0
    ? { value: Math.round((student.gpa / 4.0) * 99), incomplete: false }
    : { value: 20, incomplete: true }

  return { tec, ana, com, col, exp, acd }
}

export function calcOVR(stats: StudentStats): number {
  const vals = Object.values(stats).map(s => s.value)
  return Math.round(vals.reduce((a, b) => a + b, 0) / vals.length)
}

export function getStudentScore(student: Student): number {
  return calcOVR(calcStats(student))
}
