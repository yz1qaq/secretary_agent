export type NavigationKey = 'dashboard' | 'today' | 'tasks'
export type RefreshPanelKey = 'study' | 'life'

export type PriorityLevel = '高' | '中' | '低'
export type PlanTone = 'study' | 'life' | 'blend'

export interface WorkspaceCopy {
  eyebrow?: string
  title: string
  subtitle: string
}

export interface NavItemData {
  key: NavigationKey
  label: string
  caption?: string
}

export interface StatCardData {
  label: string
  value: string
  hint: string
}

export interface TimelineEntry {
  time: string
  title: string
  type: '固定安排' | '建议任务'
}

export interface TaskData {
  title: string
  deadline: string
  priority: PriorityLevel
}

export interface PlanItemData {
  time: string
  title: string
  detail: string
  label: string
}

export interface PlanDrawerData {
  id: string
  title: string
  summary: string
  hint: string
  tone: PlanTone
  items: PlanItemData[]
}

export interface PanelRefreshProps {
  onRefresh?: () => void | Promise<void>
  refreshing?: boolean
  refreshMessage?: string
  refreshError?: string
}
