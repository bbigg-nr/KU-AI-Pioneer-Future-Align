import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
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
