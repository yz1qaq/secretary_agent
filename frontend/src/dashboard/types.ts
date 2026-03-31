export type NavigationKey = 'dashboard' | 'today' | 'tasks'
export type RefreshPanelKey = 'study' | 'life'

export type PriorityLevel = '高' | '中' | '低'

export interface WorkspaceCopy {
  title: string
  subtitle: string
}

export interface NavItemData {
  key: NavigationKey
  label: string
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

export interface PanelRefreshProps {
  onRefresh?: () => void | Promise<void>
  refreshing?: boolean
  refreshMessage?: string
  refreshError?: string
}
