/* eslint-disable react-refresh/only-export-components */

import { PlanDrawer, StatCard } from '../ui'
import {
  PanelRefreshProps,
  PlanDrawerData,
  StatCardData,
  WorkspaceCopy,
} from '../types'

export const lifeWorkspaceCopy: WorkspaceCopy = {
  eyebrow: 'Campus Life Board',
  title: '生活',
  subtitle: '把日常习惯、明日准备和长期状态拆开看，生活区会更像一个温和但持续的节奏面板。',
}

export const lifeOverviewStats: StatCardData[] = [
  { label: '今晚习惯', value: '21:00', hint: '固定给自己一小时运动和舒展时间。' },
  { label: '明日生活', value: '3 项', hint: '作息、早餐和课前整理要提前准备。' },
  { label: '生活状态', value: '平稳', hint: '今天以恢复和规律为主，不额外堆任务。' },
  { label: '长期目标', value: '2 条', hint: '继续稳定运动频率和宿舍整理节奏。' },
]

export const lifeTodayPlan: PlanDrawerData = {
  id: 'life-today',
  title: '今日生活计划',
  summary: '今天的生活安排要尽量为学习让出空间，但晚上仍然保留固定的运动与放松时段，让节奏不会绷得太紧。',
  hint: '今日生活',
  tone: 'life',
  items: [
    {
      time: '20:40 - 21:00',
      title: '切换到运动状态',
      detail: '简单热身、收好桌面，给自己一个从学习切换到身体活动的过渡。',
      label: '状态切换',
    },
    {
      time: '21:00 - 22:00',
      title: '每日健身计划',
      detail: '以稳定出汗和舒展为目标，不追求强度爆发，完成后记得补水和拉伸。',
      label: '固定习惯',
    },
    {
      time: '22:10 - 22:30',
      title: '洗漱与放松',
      detail: '让身体慢慢降下来，避免运动后立刻重新刷手机或回到高强度学习。',
      label: '恢复缓冲',
    },
    {
      time: '23:20',
      title: '准备休息',
      detail: '把第二天要带的东西提前放好，让睡前最后十分钟只做收尾，不再临时找东西。',
      label: '收束日程',
    },
  ],
}

export const lifeTomorrowPlan: PlanDrawerData = {
  id: 'life-tomorrow',
  title: '明日生活计划',
  summary: '明天的生活安排主要服务于“顺畅开局”。只要早晨不慌，整天的学习状态通常就更稳定。',
  hint: '明日生活',
  tone: 'life',
  items: [
    {
      time: '07:30 - 08:00',
      title: '起床、通风、简单整理',
      detail: '留出一个清醒但不仓促的半小时，让身体和环境都先苏醒过来。',
      label: '清晨启动',
    },
    {
      time: '08:00 - 08:20',
      title: '早餐与出门准备',
      detail: '优先保证早餐和随身物品齐全，避免上课前被琐事打断节奏。',
      label: '基础补给',
    },
    {
      time: '20:30',
      title: '检查明晚运动安排',
      detail: '如果明天学习负荷偏大，就把运动强度调轻一点，保持节奏比追求强度更重要。',
      label: '节奏维护',
    },
  ],
}

export const lifeLongTermPlan: PlanDrawerData = {
  id: 'life-long-term',
  title: '长期生活计划',
  summary: '长期生活计划不是给自己增加更多任务，而是让运动、收纳和恢复都变成可持续的背景秩序。',
  hint: '长期习惯',
  tone: 'blend',
  items: [
    {
      time: '每周',
      title: '保持 3 次中等强度运动',
      detail: '核心目标是稳定频率，不因为一两天忙碌就完全中断生活节奏。',
      label: '运动基线',
    },
    {
      time: '每周日晚',
      title: '宿舍与书桌整理',
      detail: '留一段固定时间整理生活环境，让下一周开始时不需要从混乱里恢复秩序。',
      label: '空间维护',
    },
    {
      time: '本月',
      title: '建立更稳的休息边界',
      detail: '尽量把“学习结束”和“准备睡觉”分开，不让大脑一直停在高强度状态。',
      label: '恢复系统',
    },
  ],
}

export function LifePanel({
  onRefresh,
  refreshing = false,
  refreshMessage = '',
  refreshError = '',
}: PanelRefreshProps) {
  return (
    <div className="space-y-6">
      <section className="overflow-hidden rounded-[32px] border border-white/70 bg-[linear-gradient(135deg,rgba(255,255,255,0.96),rgba(236,253,245,0.9))] p-6 shadow-[0_18px_40px_rgba(15,23,42,0.06)]">
        <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
          <div className="max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-emerald-700">
              Life Rhythm
            </p>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight text-slate-900">
              生活区不堆太多事，只保留能稳定支持学习的节奏。
            </h2>
            <p className="mt-3 text-sm leading-7 text-slate-600">
              把今天、明天和长期习惯分开后，生活安排会更轻，不会和学习区挤在一起互相打架。
            </p>
          </div>

          <div className="rounded-[28px] border border-white/80 bg-white/80 p-4 shadow-[0_10px_24px_rgba(15,23,42,0.05)] xl:max-w-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
              当前焦点
            </p>
            <p className="mt-3 text-base font-semibold text-slate-900">
              今晚按时健身、放松和入睡，明天的生活节奏就会自然顺下来。
            </p>
            <div className="mt-4 flex items-center justify-between gap-3">
              <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-medium text-emerald-700 ring-1 ring-inset ring-emerald-200">
                以规律感为主
              </span>
              <button
                type="button"
                onClick={() => {
                  void onRefresh?.()
                }}
                disabled={refreshing}
                className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {refreshing ? '刷新中...' : '刷新'}
              </button>
            </div>
          </div>
        </div>

        {refreshError ? (
          <p className="mt-4 text-sm text-rose-600">{refreshError}</p>
        ) : null}
        {!refreshError && refreshMessage ? (
          <p className="mt-4 text-sm text-emerald-600">{refreshMessage}</p>
        ) : null}
      </section>

      <section>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          {lifeOverviewStats.map((stat) => (
            <StatCard key={stat.label} {...stat} />
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <PlanDrawer section={lifeTodayPlan} defaultOpen />
        <PlanDrawer section={lifeTomorrowPlan} />
        <PlanDrawer section={lifeLongTermPlan} />
      </section>
    </div>
  )
}
