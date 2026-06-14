# 公众号文章编辑器 (mp-editor)

> AI 驱动的 Web 端公众号文章编辑器 MVP

## 技术栈

| 类别 | 技术选型 |
|------|---------|
| 框架 | Vue 3 + TypeScript |
| 构建 | Vite |
| 编辑器 | Tiptap 2.x (ProseMirror) |
| 状态管理 | Pinia |
| 本地存储 | Dexie.js (IndexedDB) |
| 样式 | SCSS |

## 项目结构

```
src/
├── components/
│   ├── ai/              # AI 智能创作面板
│   │   └── AiPanel.vue
│   ├── editor/           # 编辑器核心
│   │   ├── MpEditor.vue      # 主编辑器
│   │   ├── EditorToolbar.vue # 工具栏
│   │   └── StatusBar.vue     # 状态栏
│   ├── preview/          # 微信预览
│   │   └── PreviewPanel.vue
│   ├── sidebar/          # 侧边栏
│   │   └── ArticlePanel.vue
│   ├── templates/        # 模板中心 (待开发)
│   ├── styles/           # 样式收藏 (待开发)
│   └── versions/         # 版本历史 (待开发)
├── composables/          # 组合式函数
│   └── useAutoSave.ts
├── db/                   # IndexedDB 封装
│   └── index.ts
├── stores/               # Pinia 状态
│   └── editor.ts
├── styles/
│   └── global.scss
├── types/
│   └── index.ts
├── views/
│   └── EditorView.vue
├── App.vue
└── main.ts
```

## 开发

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建
npm run build

# 类型检查
npx vue-tsc --noEmit
```

## 已完成功能 (Epic 0 + Epic 1 部分)

- [x] Vue3 + TypeScript + Vite 工程脚手架
- [x] Tiptap 编辑器核心集成
- [x] IndexedDB 存储封装 (Dexie.js)
- [x] 三栏布局（左侧边栏 280px / 中央编辑区 / 右侧预览 420px）
- [x] 工具栏（加粗/斜体/下划线/删除线/标题/列表/引用/分割线/链接/图片/撤销/重做/格式清除）
- [x] AI 创作面板 UI（全文生成/续写/改写/大纲/标题优化 5 个 Tab）
- [x] 文章管理面板（本地/草稿箱/已发布 + 搜索）
- [x] 微信手机预览面板（4 种机型切换 + 同步滚动开关）
- [x] 状态栏（字数/图片数/保存状态）
- [x] 自动保存（30s + Ctrl+S）
- [x] 离开页面未保存提醒
- [x] 面板折叠/展开动画
- [x] 响应式断点（1366px 以下适配）

## 待开发功能

参考 `研发任务拆解.md` 中 Epic 1~6 的详细任务列表。
