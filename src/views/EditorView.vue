<script setup lang="ts">
import { ref } from 'vue'
import { useEditorStore } from '../stores/editor'
import MpEditor from '../components/editor/MpEditor.vue'
import StatusBar from '../components/editor/StatusBar.vue'
import AiPanel from '../components/ai/AiPanel.vue'
import ArticlePanel from '../components/sidebar/ArticlePanel.vue'
import PreviewPanel from '../components/preview/PreviewPanel.vue'
import CompatPanel from '../components/preview/CompatPanel.vue'
import { useAutoSave } from '../composables/useAutoSave'

const store = useEditorStore()
useAutoSave()

const showCompatPanel = ref(false)
</script>

<template>
  <div class="main-layout">
    <!-- 左侧边栏 -->
    <transition name="slide-left">
      <aside v-show="store.leftPanelOpen" class="left-sidebar">
        <div class="sidebar-toggle-tabs">
          <button
            class="toggle-tab"
            :class="{ active: store.leftPanelTab === 'ai' }"
            @click="store.leftPanelTab = 'ai'"
            title="AI 创作"
          >
            🧠
          </button>
          <button
            class="toggle-tab"
            :class="{ active: store.leftPanelTab === 'articles' }"
            @click="store.leftPanelTab = 'articles'"
            title="文章管理"
          >
            📂
          </button>
        </div>
        <div class="sidebar-content">
          <AiPanel v-if="store.leftPanelTab === 'ai'" />
          <ArticlePanel v-else />
        </div>
      </aside>
    </transition>

    <!-- 中央编辑区 -->
    <main class="editor-area">
      <MpEditor />
      <StatusBar />
    </main>

    <!-- 右侧预览区 -->
    <transition name="slide-right">
      <aside v-show="store.rightPanelOpen" class="right-sidebar">
        <PreviewPanel @open-compat="showCompatPanel = true" />
      </aside>
    </transition>

    <!-- 面板切换按钮 -->
    <button
      class="toggle-left"
      :class="{ collapsed: !store.leftPanelOpen }"
      @click="store.leftPanelOpen = !store.leftPanelOpen"
      title="切换左面板"
    >
      {{ store.leftPanelOpen ? '◁' : '▷' }}
    </button>
    <button
      class="toggle-right"
      :class="{ collapsed: !store.rightPanelOpen }"
      @click="store.rightPanelOpen = !store.rightPanelOpen"
      title="切换右面板"
    >
      {{ store.rightPanelOpen ? '▷' : '◁' }}
    </button>

    <!-- 兼容检测面板 -->
    <CompatPanel
      v-if="showCompatPanel"
      @close="showCompatPanel = false"
    />
  </div>
</template>

<style lang="scss" scoped>
.main-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: #f5f5f5;
}

.left-sidebar {
  width: 280px;
  min-width: 280px;
  background: #fff;
  border-right: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 10;
}

.sidebar-toggle-tabs {
  display: flex;
  border-bottom: 1px solid #e8e8e8;
  background: #fafafa;
}

.toggle-tab {
  flex: 1;
  padding: 10px;
  border: none;
  background: transparent;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.15s;

  &.active {
    background: #e6f7ef;
  }

  &:hover:not(.active) {
    background: #f0f0f0;
  }
}

.sidebar-content {
  flex: 1;
  overflow: hidden;
}

.editor-area {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  position: relative;
}

.right-sidebar {
  width: 420px;
  min-width: 420px;
  background: #f0f0f0;
  border-left: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 10;
}

.toggle-left,
.toggle-right {
  position: fixed;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 40px;
  border: 1px solid #ddd;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  color: #aaa;
  transition: all 0.15s;

  &:hover {
    background: #f5f5f5;
    color: #555;
  }
}

.toggle-left {
  left: 280px;
  transition: left 0.3s ease;

  &.collapsed {
    left: 0;
  }
}

.toggle-right {
  right: 420px;
  transition: right 0.3s ease;

  &.collapsed {
    right: 0;
  }
}

// 折叠动画
.slide-left-enter-active,
.slide-left-leave-active {
  transition: all 0.3s ease;
}

.slide-left-enter-from,
.slide-left-leave-to {
  margin-left: -280px;
  opacity: 0;
}

.slide-right-enter-active,
.slide-right-leave-active {
  transition: all 0.3s ease;
}

.slide-right-enter-from,
.slide-right-leave-to {
  margin-right: -420px;
  opacity: 0;
}

// 响应式
@media (max-width: 1366px) {
  .right-sidebar {
    width: 360px;
    min-width: 360px;
  }

  .toggle-right {
    right: 360px;

    &.collapsed {
      right: 0;
    }
  }
}
</style>
