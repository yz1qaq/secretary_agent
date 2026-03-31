/* eslint-disable react-refresh/only-export-components */

import { PlanDrawer, StatCard } from '../ui'
import {
  PanelRefreshProps,
  PlanDrawerData,
  StatCardData,
  WorkspaceCopy,
} from '../types'

export const studyWorkspaceCopy: WorkspaceCopy = {
  eyebrow: 'Campus Study Board',
  title: '学习',
  subtitle: '把课程、自习和长期科研拆成三条清晰节奏，今天先处理最该落地的部分。',
}

export const studyOverviewStats: StatCardData[] = [
  { label: '今日课程', value: '2 节', hint: '下午完成课程收尾，晚上转入复盘与预习。' },
  { label: '明日准备', value: '3 项', hint: '英语写作、文献精读、课堂资料整理。' },
  { label: '可专注时间', value: '3.5h', hint: '晚间仍有一个完整深度学习窗口。' },
  { label: '长期推进', value: '2 条', hint: '论文写作与研究方法笔记继续稳步推进。' },
]

export const studyTodayPlan: PlanDrawerData = {
  id: 'study-today',
  title: '今日学习计划',
  summary: '今天的学习重点是把课堂内容收好尾，再用一段完整晚间时间把明天的课和科研线索接上。',
  hint: '今日节奏',
  tone: 'study',
  items: [
    {
      time: '19:10 - 20:00',
      title: '整理今天课堂笔记',
      detail: '把论文写作与社会网络课程内容拆成条目，顺手补上课堂里的关键词和老师提醒。',
      label: '课程收尾',
    },
    {
      time: '20:10 - 21:10',
      title: '阅读一篇相关文献并做摘录',
      detail: '优先精读和你本周研究主题最接近的那篇，记录 3 个可以复用的表达和结构。',
      label: '深度学习',
    },
    {
      time: '21:20 - 22:00',
      title: '预习明天英语写作内容',
      detail: '提前看课程提纲和例句，把明天可能会用到的表达先扫一遍。',
      label: '明日预热',
    },
    {
      time: '22:00 - 22:30',
      title: '更新科研推进记录',
      detail: '把今天的课程启发和文献摘录写进研究日志，方便后面串联成长期材料。',
      label: '研究整理',
    },
  ],
}

export const studyTomorrowPlan: PlanDrawerData = {
  id: 'study-tomorrow',
  title: '明日学习计划',
  summary: '明天的安排更偏向"轻课程 + 稳推进"，目标是让上午课堂和下午自习自然衔接，不出现断层。',
  hint: '明日预排',
  tone: 'study',
  items: [
    {
      time: '08:20 - 09:50',
      title: '英语写作课程',
      detail: '带着今天预习过的表达去上课，重点留意老师给的结构化写作建议。',
      label: '固定课程',
    },
    {
      time: '14:00 - 15:20',
      title: '文献精读与批注整理',
      detail: '把今天晚上的阅读继续展开，整理成可直接复用到综述里的摘录。',
      label: '延续推进',
    },
    {
      time: '20:00 - 21:00',
      title: '检查本周课程与作业节奏',
      detail: '确认周后半段课程教室、任务截止时间和本周最重要的输出目标。',
      label: '节奏校准',
    },
  ],
}

export const studyLongTermPlan: PlanDrawerData = {
  id: 'study-long-term',
  title: '长期学习计划',
  summary: '长期计划不追求一天做完，而是把论文写作、研究资料和方法训练拆成可持续推进的慢变量。',
  hint: '长期推进',
  tone: 'blend',
  items: [
    {
      time: '本周',
      title: '搭建论文写作素材池',
      detail: '把课程启发、文献句式、方法论段落分类归档，后续写作时能直接调用。',
      label: '写作储备',
    },
    {
      time: '本月',
      title: '建立研究方法笔记页',
      detail: '把社会网络与计算里的方法整理成自己的研究语言，避免只会听课不会迁移。',
      label: '方法训练',
    },
    {
      time: '学期内',
      title: '形成稳定的周复盘制度',
      detail: '每周固定留一段时间复盘课程、科研和输出情况，让学习节奏可持续而不是突击。',
      label: '学习系统',
    },
  ],
}

// 课程表数据转换为抽屉格式
export const studyWeeklySchedule: PlanDrawerData = {
  id: 'study-weekly-schedule',
  title: '本周课程表',
  summary: '当前是星期二（2026年3月31日），本周共 12 节课，今日有 3 节课程。按星期分组展示所有课程安排，包含时间、教室和教师信息。',
  hint: '周视图',
  tone: 'study',
  items: [
    {
      time: '星期一 08:30 - 09:55',
      title: '论文写作与学术规范·2班',
      detail: '📍 3B-101 | 👨‍🏫 张教授',
      label: '星期一',
    },
    {
      time: '星期一 14:00 - 15:25',
      title: '自然辩证法概论·9班',
      detail: '📍 3B-203 | 👨‍🏫 李教授',
      label: '星期一',
    },
    {
      time: '星期二 08:30 - 09:55',
      title: '论文写作与学术规范·2班',
      detail: '📍 3B-101 | 👨‍🏫 张教授',
      label: '星期二 · 今天',
    },
    {
      time: '星期二 14:00 - 15:25',
      title: '自然辩证法概论·9班',
      detail: '📍 3B-203 | 👨‍🏫 李教授',
      label: '星期二 · 今天',
    },
    {
      time: '星期二 15:30 - 16:55',
      title: '社会网络与计算·1班',
      detail: '📍 3C-202 | 👨‍🏫 王教授',
      label: '星期二 · 今天',
    },
    {
      time: '星期三 08:20 - 09:50',
      title: '英语写作·3班',
      detail: '📍 3A-205 | 👨‍🏫 Smith',
      label: '星期三',
    },
    {
      time: '星期三 14:00 - 15:25',
      title: '自然辩证法概论·9班',
      detail: '📍 3B-203 | 👨‍🏫 李教授',
      label: '星期三',
    },
    {
      time: '星期三 15:30 - 16:55',
      title: '社会网络与计算·1班',
      detail: '📍 3C-202 | 👨‍🏫 王教授',
      label: '星期三',
    },
    {
      time: '星期四 08:30 - 09:55',
      title: '论文写作与学术规范·2班',
      detail: '📍 3B-101 | 👨‍🏫 张教授',
      label: '星期四',
    },
    {
      time: '星期四 14:00 - 15:25',
      title: '自然辩证法概论·9班',
      detail: '📍 3B-203 | 👨‍🏫 李教授',
      label: '星期四',
    },
    {
      time: '星期五 08:20 - 09:50',
      title: '英语写作·3班',
      detail: '📍 3A-205 | 👨‍🏫 Smith',
      label: '星期五',
    },
    {
      time: '星期五 14:00 - 15:25',
      title: '社会网络与计算·1班',
      detail: '📍 3C-202 | 👨‍🏫 王教授',
      label: '星期五',
    },
  ],
}

export function StudyPanel({
  onRefresh,
  refreshing = false,
  refreshMessage = '',
  refreshError = '',
}: PanelRefreshProps) {
  return (
    <div className="space-y-6">
      <section className="overflow-hidden rounded-[32px] border border-white/70 bg-[linear-gradient(135deg,rgba(255,255,255,0.96),rgba(239,246,255,0.92))] p-6 shadow-[0_18px_40px_rgba(15,23,42,0.06)]">
        <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
          <div className="max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-sky-700">
              Study Rhythm
            </p>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight text-slate-900">
              今天先把课程收好尾，再给明天留出轻盈的起点。
            </h2>
            <p className="mt-3 text-sm leading-7 text-slate-600">
              学习区现在按照今日、明日和长期三层节奏组织。先把今天真正要做的事情落地，再让明天和长期目标自然接上。
            </p>
          </div>

          <div className="rounded-[28px] border border-white/80 bg-white/80 p-4 shadow-[0_10px_24px_rgba(15,23,42,0.05)] xl:max-w-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
              当前焦点
            </p>
            <p className="mt-3 text-base font-semibold text-slate-900">
              晚间学习窗口优先留给课程复盘与明日预热。
            </p>
            <div className="mt-4 flex items-center justify-between gap-3">
              <span className="rounded-full bg-sky-100 px-3 py-1 text-xs font-medium text-sky-700 ring-1 ring-inset ring-sky-200">
                适合静心推进
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
          {studyOverviewStats.map((stat) => (
            <StatCard key={stat.label} {...stat} />
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <PlanDrawer section={studyTodayPlan} defaultOpen />
        <PlanDrawer section={studyTomorrowPlan} />
        <PlanDrawer section={studyWeeklySchedule} />
        <PlanDrawer section={studyLongTermPlan} />
      </section>
    </div>
  )
}