/* eslint-disable react-refresh/only-export-components */

import { StatCard, TaskItem, TimelineItem } from '../ui'
import {
  PanelRefreshProps,
  StatCardData,
  TaskData,
  TimelineEntry,
  WorkspaceCopy,
} from '../types'

export const lifeWorkspaceCopy: WorkspaceCopy = {
  title: '生活',
  subtitle: '当前先模拟每日固定的 21:00 健身计划，后续可继续扩展。',
}

export const lifeStatCards: StatCardData[] = [
  {
    label: '今晚安排',
    value: '21:00',
    hint: '固定执行一小时健身计划',
  },
  {
    label: '生活习惯',
    value: '1 项',
    hint: '先从稳定的晚间锻炼开始',
  },
  {
    label: '今日目标',
    value: '动起来',
    hint: '完成运动后简单拉伸和补水',
  },
]

export const lifeTimelineEntries: TimelineEntry[] = [
  {
    time: '21:00 - 22:00',
    title: '每日健身计划',
    type: '固定安排',
  },
]

export const lifeTasks: TaskData[] = [
  { title: '21:00 健身训练', deadline: '今天 21:00 - 22:00', priority: '中' },
]

export function LifePanel({
  onRefresh,
  refreshing = false,
  refreshMessage = '',
  refreshError = '',
}: PanelRefreshProps) {
  return (
    <div className="space-y-8">
      <section>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {lifeStatCards.map((stat) => (
            <StatCard key={stat.label} {...stat} />
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">生活安排</h2>
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-500">固定习惯</span>
            <button
              type="button"
              onClick={() => {
                void onRefresh?.()
              }}
              disabled={refreshing}
              className="rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {refreshing ? '刷新中...' : '刷新'}
            </button>
          </div>
        </div>
        {refreshError ? (
          <p className="text-sm text-red-600">{refreshError}</p>
        ) : null}
        {!refreshError && refreshMessage ? (
          <p className="text-sm text-emerald-600">{refreshMessage}</p>
        ) : null}
        <div className="space-y-3">
          {lifeTimelineEntries.map((item) => (
            <TimelineItem key={`${item.time}-${item.title}`} {...item} />
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">生活提醒</h2>
          <span className="text-sm text-slate-500">模拟内容</span>
        </div>
        <div className="mt-4">
          {lifeTasks.map((task) => (
            <TaskItem key={task.title} {...task} />
          ))}
        </div>
      </section>
    </div>
  )
}
