import type { SkillItem, ProfileOverrides } from './types'

const KEYS = {
  studentId: 'fa_student_id',
  profileOverrides: 'fa_profile_overrides',
  targets: 'fa_user_targets',
  coachStudents: 'fa_coach_students',
  coachAuth: 'fa_coach_auth',
}

function safe<T>(fn: () => T, fallback: T): T {
  try { return fn() } catch { return fallback }
}

export const storage = {
  getStudentId: () => safe(() => localStorage.getItem(KEYS.studentId), null),
  setStudentId: (id: string) => localStorage.setItem(KEYS.studentId, id),
  clearStudentId: () => localStorage.removeItem(KEYS.studentId),

  getProfileOverrides: (): ProfileOverrides =>
    safe(() => JSON.parse(localStorage.getItem(KEYS.profileOverrides) ?? '{}'), {}),
  setProfileOverrides: (v: ProfileOverrides) =>
    localStorage.setItem(KEYS.profileOverrides, JSON.stringify(v)),

  getTargets: (): string[] =>
    safe(() => JSON.parse(localStorage.getItem(KEYS.targets) ?? '[]'), []),
  setTargets: (v: string[]) => localStorage.setItem(KEYS.targets, JSON.stringify(v)),
  addTarget: (title: string) => {
    const t = storage.getTargets()
    if (!t.includes(title)) storage.setTargets([...t, title])
  },
  removeTarget: (title: string) =>
    storage.setTargets(storage.getTargets().filter(t => t !== title)),
  isTarget: (title: string) => storage.getTargets().includes(title),

  getCoachStudents: (): string[] =>
    safe(() => JSON.parse(localStorage.getItem(KEYS.coachStudents) ?? '[]'), []),
  setCoachStudents: (v: string[]) => localStorage.setItem(KEYS.coachStudents, JSON.stringify(v)),

  setCoachAuth: () => localStorage.setItem(KEYS.coachAuth, '1'),
  getCoachAuth: () => safe(() => localStorage.getItem(KEYS.coachAuth) === '1', false),
  clearCoachAuth: () => localStorage.removeItem(KEYS.coachAuth),

  mergeSkills: (csvSkills: SkillItem[], overrides: ProfileOverrides): SkillItem[] => {
    if (!overrides.skills) return csvSkills
    return overrides.skills
  },
}
