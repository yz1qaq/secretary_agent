/* eslint-disable react-refresh/only-export-components */

import { StatCard, TaskItem, TimelineItem } from '../ui'
import { StatCardData, TaskData, TimelineEntry, WorkspaceCopy } from '../types'

export const studyWorkspaceCopy: WorkspaceCopy = {
  title: '学习',
  subtitle: '展示西华大学研究生 2025-2026 下期课程安排、学习任务与专注计划。',
}

export const studyStatCards: StatCardData[] = [
  { label: '本周课程', value: '8', hint: '周一至周五共 8 节课' },
  { label: '今日课程', value: '0', hint: '今天是星期日，无课程' },
  { label: '明日课程', value: '2', hint: '15:30 和 19:00 各有 1 节' },
  { label: '学习任务', value: '4', hint: '按优先级完成' },
]

// 周课表数据：根据西华大学研究生 2025-2026 下期课表
export const weeklySchedule = {
  '星期一': [
    { time: '15:30 - 16:55', course: '研究生英语写作与交流·22班', location: '3B-204 陈博', week: '1-4周' },
    { time: '19:00 - 21:10', course: '工程伦理·2班', location: '3C-101 丰慧芳', week: '1-6周' },
  ],
  '星期二': [
    { time: '08:30 - 09:55', course: '论文写作与学术规范·2班', location: '3B-101 刘冰', week: '1-8周' },
    { time: '14:00 - 15:25', course: '自然辩证法概论·9班', location: '3B-203 陈小满', week: '2-5周' },
    { time: '15:30 - 16:55', course: '社会网络与计算·1班', location: '3C-202 杜亚军', week: '2-5周' },
    { time: '15:30 - 16:55', course: '社会网络与计算·1班', location: '3C-202 李显勇', week: '6-9周' },
  ],
  '星期三': [
    { time: '10:15 - 11:40', course: '研究生英语写作与交流·22班', location: '3B-303 陈博', week: '1-12周' },
    { time: '14:00 - 15:25', course: '自然辩证法概论·9班', location: '3B-203 陈小满', week: '2-5周' },
    { time: '15:30 - 16:55', course: '社会网络与计算·1班', location: '3C-202 杜亚军', week: '2-5周' },
    { time: '15:30 - 16:55', course: '社会网络与计算·1班', location: '3C-202 李显勇', week: '6-9周' },
  ],
  '星期四': [],
  '星期五': [
    { time: '14:00 - 16:55', course: '深度学习原理及应用·1班', location: '3B-203 高海燕', week: '4-14周' },
  ],
  '星期六': [],
  '星期日': [],
}

// 明日（3月30日 星期一）真实时间安排
export const studyTimelineEntries: TimelineEntry[] = [
  {
    time: '08:30 - 11:30',
    title: '自习：预习论文写作与学术规范',
    type: '建议任务',
  },
  {
    time: '14:00 - 15:00',
    title: '自习：复习工程伦理课程资料',
    type: '建议任务',
  },
  {
    time: '15:30 - 16:55',
    title: '课程：研究生英语写作与交流·22班',
    type: '固定安排',
  },
  {
    time: '17:00 - 18:30',
    title: '晚餐 & 休息',
    type: '固定安排',
  },
  {
    time: '19:00 - 21:10',
    title: '课程：工程伦理·2班',
    type: '固定安排',
  },
  {
    time: '21:30 - 22:30',
    title: '复盘：整理今日课程笔记',
    type: '建议任务',
  },
]

// 明日（3月30日 星期一）真实学习任务
export const studyTasks: TaskData[] = [
  { title: '准备英语写作课程材料', deadline: '明天 15:00', priority: '高' },
  { title: '阅读工程伦理案例资料', deadline: '明天 18:30', priority: '高' },
  { title: '完成论文写作课程预习', deadline: '明天 12:00', priority: '中' },
  { title: '整理本周学习计划', deadline: '明天 22:30', priority: '中' },
]

// 星期名称数组
const weekDays = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']

export function StudyPanel() {
  return (
    <div className="space-y-8">
      <section>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          {studyStatCards.map((stat) => (
            <StatCard key={stat.label} {...stat} />
          ))}
        </div>
      </section>

      {/* 周课表区域 */}
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-slate-900">本周课程表</h2>
          <span className="text-sm text-slate-500">西华大学 2025-2026 下期</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {weekDays.map((day) => {
            const courses = weeklySchedule[day as keyof typeof weeklySchedule]
            const hasCourses = courses.length > 0
            return (
              <div
                key={day}
                className={`rounded-xl border p-4 ${
                  hasCourses
                    ? 'border-blue-200 bg-blue-50'
                    : 'border-slate-200 bg-slate-50'
                }`}
              >
                <h3 className={`font-semibold mb-3 ${hasCourses ? 'text-blue-700' : 'text-slate-500'}`}>
                  {day}
                </h3>
                {hasCourses ? (
                  <div className="space-y-2">
                    {courses.map((item, idx) => (
                      <div
                        key={idx}
                        className="text-sm bg-white rounded-lg p-2 border border-blue-100"
                      >
                        <div className="font-medium text-slate-700">{item.time}</div>
                        <div className="text-blue-600">{item.course}</div>
                        <div className="text-xs text-slate-400">{item.location}</div>
                        <div className="text-xs text-blue-400">{item.week}</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-sm text-slate-400 text-center py-4">
                    无课程安排
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </section>

      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">明日学习时间线</h2>
          <span className="text-sm text-slate-500">2026 年 3 月 30 日 星期一</span>
        </div>
        <div className="space-y-3">
          {studyTimelineEntries.map((item) => (
            <TimelineItem key={`${item.time}-${item.title}`} {...item} />
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">明日学习任务</h2>
          <span className="text-sm text-slate-500">按优先级推进</span>
        </div>
        <div className="mt-4">
          {studyTasks.map((task) => (
            <TaskItem key={task.title} {...task} />
          ))}
        </div>
      </section>
    </div>
  )
}