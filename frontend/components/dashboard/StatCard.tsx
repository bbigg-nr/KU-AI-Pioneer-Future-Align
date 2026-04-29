import { type LucideIcon } from 'lucide-react'

interface StatCardProps {
  title: string
  value: number | string
  subtitle: string
  icon: LucideIcon
  iconBg: string
  onClick?: () => void
}

export default function StatCard({ title, value, subtitle, icon: Icon, iconBg, onClick }: StatCardProps) {
  return (
    <div 
      onClick={onClick}
      className={`bg-white rounded-2xl border border-gray-100 p-6 flex items-start justify-between shadow-sm transition-all duration-200 ${onClick ? 'cursor-pointer hover:shadow-md hover:border-gray-300 active:scale-[0.98]' : ''}`}
    >
      <div>
        <p className="text-xs text-gray-400 uppercase tracking-wider font-medium mb-2">{title}</p>
        <p className="text-3xl font-bold text-gray-900">{value}</p>
        <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
      </div>
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${iconBg}`}>
        <Icon size={22} className="text-white" />
      </div>
    </div>
  )
}
