import type { ChatConversation, WorkspacePage } from './types'

export const workspacePages: WorkspacePage[] = [
  {
    id: 'today',
    label: '今日任务',
    eyebrow: 'Morning Board',
    title: '把今天过成有节奏的一天',
    subtitle: '课程、社团、碰头会和个人小目标，先排顺，再出发。',
    note: '像翻开一页刚写好的计划本，先看最重要的三件事，再把零碎时间留给想悄悄进步的自己。',
    highlights: [
      {
        id: 'today-1',
        title: '课程展示准备',
        detail: '10:20 前再过一遍提纲，把结尾例子讲顺。',
        meta: '优先级 A',
      },
      {
        id: 'today-2',
        title: '社团例会提醒',
        detail: '中午前发一条集合提醒，顺手带上活动物资名单。',
        meta: '中午前',
      },
      {
        id: 'today-3',
        title: '晚间复盘',
        detail: '睡前花 15 分钟，把今天的完成情况记进计划簿。',
        meta: '晚间',
      },
    ],
    timeline: [
      {
        id: 'today-t1',
        time: '08:30',
        title: '晨读和早餐',
        note: '带上英语单词本和保温杯，先暖机。',
      },
      {
        id: 'today-t2',
        time: '13:40',
        title: '项目小组讨论',
        note: '重点确认分工和周末前要交的材料。',
      },
      {
        id: 'today-t3',
        time: '19:10',
        title: '操场慢跑',
        note: '给脑袋留一点放空时间，也给自己一点风。',
      },
    ],
    prompts: [
      '帮我把今天的事项按轻重缓急排一下，并告诉我先做哪三件。',
      '请根据我今天的课程和会议，生成一个更顺手的时间安排表。',
      '帮我把今天没做完的内容转成晚上的补救清单。',
    ],
  },
  {
    id: 'life',
    label: '生活',
    eyebrow: 'Soft Routine',
    title: '把生活过成轻盈又有秩序',
    subtitle: '采购、运动、约饭、休息，都可以被认真对待。',
    note: '生活不是任务堆，而是一些柔软的小安排。把它们排舒服了，整个人都会亮一点。',
    highlights: [
      {
        id: 'life-1',
        title: '宿舍补给',
        detail: '晚上回寝前买水果、洗衣液和创可贴。',
        meta: '放学后',
      },
      {
        id: 'life-2',
        title: '朋友生日准备',
        detail: '确认贺卡内容，再挑一份不太夸张的小礼物。',
        meta: '这周内',
      },
      {
        id: 'life-3',
        title: '睡前留白',
        detail: '关灯前不刷长视频，换成 10 分钟随手写。',
        meta: '睡前',
      },
    ],
    timeline: [
      {
        id: 'life-t1',
        time: '12:15',
        title: '食堂窗口避峰',
        note: '早点去，顺便带一杯热豆浆。',
      },
      {
        id: 'life-t2',
        time: '17:50',
        title: '超市快采买',
        note: '只买清单上的，不被零食区拐跑。',
      },
      {
        id: 'life-t3',
        time: '21:30',
        title: '洗漱后放松',
        note: '泡脚或者听歌二选一，别两件都忘了。',
      },
    ],
    prompts: [
      '请帮我把这周的生活安排整理成一个轻松一点的提醒清单。',
      '帮我规划一下今晚回宿舍后的节奏，别让我又拖到很晚。',
      '请把采购、运动和休息拆成一个简单的生活打卡计划。',
    ],
  },
  {
    id: 'study',
    label: '学习',
    eyebrow: 'Study Studio',
    title: '把注意力留给真正想学会的事',
    subtitle: '复习、预习、阅读和写作，都值得被安静地安排进一天。',
    note: '学习页不是为了塞满任务，而是提醒你：一点点往前走，也算很认真。',
    highlights: [
      {
        id: 'study-1',
        title: '高频错题回看',
        detail: '先挑最容易反复出错的两类题目，不贪多。',
        meta: '今晚主线',
      },
      {
        id: 'study-2',
        title: '论文资料摘录',
        detail: '读完两篇核心文献，顺手整理一句自己的理解。',
        meta: '图书馆',
      },
      {
        id: 'study-3',
        title: '英语输出练习',
        detail: '用 20 分钟写一段短文，不追求完美。',
        meta: '碎片时间',
      },
    ],
    timeline: [
      {
        id: 'study-t1',
        time: '09:50',
        title: '图书馆占位',
        note: '先坐到靠窗的位置，心会静一点。',
      },
      {
        id: 'study-t2',
        time: '15:30',
        title: '集中复习 45 分钟',
        note: '只做一门课，不多线程切换。',
      },
      {
        id: 'study-t3',
        time: '22:10',
        title: '睡前回顾',
        note: '把今天真正学会的一点写下来。',
      },
    ],
    prompts: [
      '请帮我把今晚的学习任务拆成 3 个能立刻开始的小步骤。',
      '根据我现在的复习内容，帮我安排一份 90 分钟的学习节奏。',
      '请整理一份适合宿舍晚间执行的安静学习计划。',
    ],
  },
]

export const initialConversations: ChatConversation[] = [
  {
    id: 'conversation-today',
    title: '今日安排',
    summary: '课程与社团事项一起整理',
    updatedAt: '刚刚',
    threadId: 'campus-today',
    messages: [
      {
        id: 'conversation-today-message-1',
        role: 'assistant',
        roleLabel: 'AI 秘书',
        content:
          '早安，今天的任务我可以帮你排优先级、理顺时间，也可以把零碎事项整理成可执行清单。',
        time: '08:12',
      },
    ],
  },
  {
    id: 'conversation-life',
    title: '生活清单',
    summary: '采购、休息和朋友安排',
    updatedAt: '12:40',
    threadId: 'campus-life',
    messages: [
      {
        id: 'conversation-life-message-1',
        role: 'assistant',
        roleLabel: 'AI 秘书',
        content:
          '生活页可以交给我处理那些容易忘的小事，比如采购提醒、作息安排和出门前检查。',
        time: '12:40',
      },
    ],
  },
  {
    id: 'conversation-study',
    title: '学习陪跑',
    summary: '复习节奏和晚间学习计划',
    updatedAt: '昨天',
    threadId: 'campus-study',
    messages: [
      {
        id: 'conversation-study-message-1',
        role: 'assistant',
        roleLabel: 'AI 秘书',
        content:
          '如果你愿意，我可以把今晚的学习任务拆得很轻，让你一眼看到下一步从哪里开始。',
        time: '昨天',
      },
    ],
  },
]
