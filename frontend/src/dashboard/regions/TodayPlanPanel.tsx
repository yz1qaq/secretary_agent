/* eslint-disable react-refresh/only-export-components */

import { lifeTimelineEntries } from './LifePanel'
import { studyTimelineEntries } from './StudyPanel'
import { EmptyStateCard, StatCard, TimelineItem } from '../ui'
import { StatCardData, TimelineEntry, WorkspaceCopy } from '../types'

export const todayPlanWorkspaceCopy: WorkspaceCopy = {
  title: '今日计划',
  subtitle: '汇总学习与生活中今天应该执行的安排，帮助你快速进入状态。',
}

function buildTodayPlanCards(): StatCardData[] {
  return [
    {
      label: '学习安排',
      value: `${studyTimelineEntries.length} 项`,
      hint: studyTimelineEntries.map((item) => item.title.replace('课程：', '')).join('、'),
    },
    {
      label: '生活安排',
      value: `${lifeTimelineEntries.length} 项`,
      hint: lifeTimelineEntries.map((item) => item.title).join('、'),
    },
    {
      label: '今日重点',
      value: '先学后练',
      hint: '白天学习，晚间锻炼',
    },
  ]
}

function buildTodayTimeline(): TimelineEntry[] {
  return [...studyTimelineEntries, ...lifeTimelineEntries].sort((a, b) =>
    a.time.localeCompare(b.time),
  )
}

export function TodayPlanPanel() {
  const todayPlanCards = buildTodayPlanCards()
  const todayTimeline = buildTodayTimeline()

  return (
    <div className="space-y-8">
      <section>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {todayPlanCards.map((stat) => (
            <StatCard key={stat.label} {...stat} />
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">今日执行清单</h2>
          <span className="text-sm text-slate-500">学习 + 生活</span>
        </div>
        <div className="space-y-3">
          {todayTimeline.map((item) => (
            <TimelineItem key={`${item.time}-${item.title}`} {...item} />
          ))}
        </div>
      </section>

      <EmptyStateCard
        title="今日建议"
        description="优先完成上午课程和下午的学习任务，21:00 之后切换到健身计划，让学习和生活安排各自保持节奏。"
      />
    </div>
  )
}
