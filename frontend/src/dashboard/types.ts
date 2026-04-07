export type NavigationKey = 'dashboard' | 'today' | 'tasks' | 'settings'
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

export interface ModelSettingsData {
  base_url: string
  api_key_masked: string
  api_key_configured: boolean
  model_name: string
}

export interface UserProfileFormData {
  name: string
  alias: string
  role: string
  school: string
  major: string
  grade_or_stage: string
  advisor: string
  goals: string
  preferences: string
  constraints: string
  notes: string
}

export interface AssistantProfileFormData {
  name: string
  role: string
  tone: string
  core_responsibilities: string
  response_style: string
  tool_usage_style: string
  boundaries: string
  notes: string
}

export interface LongTermProfileData<TProfile> {
  manual_profile: TProfile
  inferred_profile: TProfile
  merged_profile_text: string
  knowledge: Array<Record<string, unknown>>
}

export interface ShortTermMemoryItem {
  id?: string
  thread_id?: string
  user_input?: string
  agent_response?: string
  timestamp?: string
  meta_data?: Record<string, unknown>
}

export interface MidTermMemoryItem {
  id?: string
  title?: string
  summary?: string
  keywords?: string[]
  heat?: number
  retrieval_count?: number
  updated_at?: string
  analyzed?: boolean
}

export interface SettingsMemoryData {
  short_term: ShortTermMemoryItem[]
  mid_term: MidTermMemoryItem[]
  long_term: {
    user: LongTermProfileData<UserProfileFormData>
    assistant: LongTermProfileData<AssistantProfileFormData>
  }
}

export interface SettingsData {
  model: ModelSettingsData
  memory: SettingsMemoryData
}
