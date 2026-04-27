export interface SkillItem {
  name: string
  level: 'Beginner' | 'Intermediate' | 'Advanced' | 'Native'
}

export interface Student {
  student_id: string
  name: string
  faculty: string
  year: number
  gpa: number
  skills: SkillItem[]
  languages: SkillItem[]
  target_career: string
}

export interface JobMatch {
  job_id: string
  job_title: string
  match_score: number
  matched_skills: string[]
  skills_to_improve: string[]
  missing_skills: string[]
  alumni_career_score?: number
  final_score?: number
  supporting_alumni_count?: number
}

export interface ArchetypeMatch {
  job_title: string
  archetype_name: string
  match_score: number
  matched_skills: string[]
  skills_to_improve: string[]
  missing_skills: string[]
  top_skills: string[]
  salary_range: string
  jd_count: number
  industry: string
}

export interface BlendedResult {
  student: Pick<Student, 'student_id' | 'name' | 'faculty' | 'gpa' | 'target_career'>
  top_jobs: JobMatch[]
  total_student_skills: number
  alpha: number
  knn_k: number
  similar_alumni_count: number
}

export interface AlumniMatch {
  alumni_id: string
  faculty: string
  first_job_title: string
  similarity_score: number
  success_score: number
  salary_start: number
  years_to_promotion: number
  skill_overlap: number
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  rag_used?: boolean
}

export interface ProfileOverrides {
  skills?: SkillItem[]
  languages?: SkillItem[]
  activities?: string[]
}

export interface CoachingReport {
  strengths: string[]
  development_areas: string[]
  career_progress: string[]
  recommendations: string[]
}
