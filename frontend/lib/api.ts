import type { Student, BlendedResult, ArchetypeMatch, AlumniMatch, SkillItem } from './types'

const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8080'

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`)
  return res.json()
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`)
  return res.json()
}

export const api = {
  getStudent: (id: string) => get<Student>(`/students/${id}`),

  listStudents: (limit = 500) =>
    get<{ students: Pick<Student, 'student_id' | 'name' | 'faculty' | 'year' | 'gpa' | 'target_career'>[], total: number }>(`/students?limit=${limit}`),

  matchStudentBlended: (student_id: string, top_n = 5) =>
    post<BlendedResult>('/match/student/blended', { student_id, top_n }),

  matchStudent: (student_id: string, top_n = 5) =>
    post<{ student: Student['student_id'], top_jobs: BlendedResult['top_jobs'] }>('/match/student', { student_id, top_n }),

  matchStudentArchetype: (student_id: string, top_n = 5) =>
    post<{ student: unknown, top_archetypes: ArchetypeMatch[] }>('/match/student/archetype', { student_id, top_n }),

  matchStudentAlumni: (student_id: string, top_k = 10) =>
    post<{ student: unknown, similar_alumni: AlumniMatch[], total_found: number }>('/match/student/alumni', { student_id, top_k }),

  matchSkills: (skills: SkillItem[], top_n = 5) =>
    post<{ top_jobs: BlendedResult['top_jobs'] }>('/match', { skills, top_n }),
}
