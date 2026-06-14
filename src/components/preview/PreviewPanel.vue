<script setup lang="ts">
import { computed, ref } from 'vue'
import { useEditorStore } from '../../stores/editor'

const store = useEditorStore()

const emit = defineEmits<{
  openCompat: []
}>()

const showFullscreen = ref(false)

const devices = {
  'iphone-se': { name: 'iPhone SE', width: 375, height: 667 },
  'iphone-14': { name: 'iPhone 14 Pro', width: 393, height: 852 },
  'iphone-14-max': { name: 'iPhone 14 Pro Max', width: 430, height: 932 },
  'android': { name: 'Android 主流', width: 412, height: 915 },
}

const currentDevice = computed(() => devices[store.previewDevice])

const deviceLabels = Object.entries(devices).map(([key, val]) => ({
  key: key as keyof typeof devices,
  label: val.name,
}))

function openCompat() {
  emit('openCompat')
}
</script>

<template>
  <div class="preview-panel">
    <div class="preview-header">
      <span class="preview-title">预览</span>
      <div class="device-switcher">
        <button
          v-for="d in deviceLabels"
          :key="d.key"
          class="device-btn"
          :class="{ active: store.previewDevice === d.key }"
          @click="store.previewDevice = d.key"
          :title="d.label"
        >
          {{ d.label.split(' ')[0] }}
        </button>
      </div>
      <button class="fullscreen-btn" @click="showFullscreen = true" title="全屏预览">⛶</button>
      <button class="compat-btn" @click="openCompat" title="兼容检测">🔍</button>
      <label class="sync-toggle" title="同步滚动">
        <input type="checkbox" v-model="store.syncScroll" />
        <span>同步</span>
      </label>
    </div>

    <div class="preview-body">
      <div
        class="phone-frame"
        :style="{
          width: currentDevice.width + 'px',
          height: Math.min(currentDevice.height, 700) + 'px',
        }"
      >
        <div class="phone-notch" />
        <div class="phone-screen">
          <div class="wechat-header">
            <span class="wechat-back">‹</span>
            <span class="wechat-title">{{ store.currentArticle?.title || '文章预览' }}</span>
            <span class="wechat-more">···</span>
          </div>
          <div class="wechat-body">
            <div
              v-if="store.editorContent && store.editorContent.replace(/<[^>]*>/g, '').trim()"
              v-html="store.editorContent"
            />
            <div v-else class="empty-preview">
              <div class="empty-icon">📝</div>
              <p>编辑内容将在此实时预览</p>
              <p class="empty-hint">尝试输入文字或使用 AI 生成文章</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 全屏预览 -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showFullscreen" class="fullscreen-overlay" @click="showFullscreen = false">
          <div class="fullscreen-container" @click.stop>
            <div class="fullscreen-header">
              <span>全屏预览</span>
              <button @click="showFullscreen = false">✕</button>
            </div>
            <div class="fullscreen-body">
              <div
                class="fullscreen-phone"
                :style="{
                  width: (currentDevice.width * 1.2) + 'px',
                  height: (currentDevice.height * 1.2) + 'px',
                }"
              >
                <div class="phone-screen">
                  <div class="wechat-header">
                    <span class="wechat-back">‹</span>
                    <span class="wechat-title">{{ store.currentArticle?.title || '文章预览' }}</span>
                    <span class="wechat-more">···</span>
                  </div>
                  <div class="wechat-body" v-html="store.editorContent || '<p style=color:#ccc;text-align:center;padding-top:60px>暂无内容</p>'" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style lang="scss" scoped>
.preview-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f0f0f0;
}

.preview-header {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid #e0e0e0;
  background: #fafafa;
  gap: 8px;

  .preview-title { font-size: 13px; font-weight: 600; color: #333; }
}

.device-switcher {
  display: flex;
  gap: 2px;
  margin-left: auto;
}

.device-btn {
  padding: 3px 8px;
  border: 1px solid #ddd;
  background: #fff;
  border-radius: 4px;
  font-size: 11px;
  color: #888;
  cursor: pointer;

  &.active {
    background: #07c160;
    border-color: #07c160;
    color: #fff;
  }
}

.fullscreen-btn, .compat-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #ddd;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  color: #888;

  &:hover { background: #f0f0f0; }
}

.sync-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #888;

  input { margin: 0; }
}

.preview-body {
  flex: 1;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 16px;
  overflow-y: auto;
}

.phone-frame {
  background: #1a1a1a;
  border-radius: 36px;
  padding: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  flex-shrink: 0;
  position: relative;
}

.phone-notch {
  width: 120px;
  height: 28px;
  background: #1a1a1a;
  border-radius: 0 0 16px 16px;
  position: absolute;
  top: 12px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
}

.phone-screen {
  width: 100%;
  height: 100%;
  background: #fff;
  border-radius: 24px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.wechat-header {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  background: #ededed;
  font-size: 16px;
  color: #333;
  flex-shrink: 0;

  .wechat-back { font-size: 22px; margin-right: 8px; color: #07c160; }
  .wechat-title {
    flex: 1; text-align: center; font-weight: 500;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    font-size: 15px;
  }
  .wechat-more { font-size: 18px; color: #07c160; letter-spacing: 2px; }
}

.wechat-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  font-size: 15px;
  line-height: 1.8;
  color: #333;

  :deep(h1) { font-size: 22px; font-weight: 700; margin-bottom: 12px; color: #1a1a1a; }
  :deep(h2) { font-size: 19px; font-weight: 700; margin: 16px 0 8px; color: #1a1a1a; }
  :deep(h3) { font-size: 17px; font-weight: 600; margin: 12px 0 6px; color: #1a1a1a; }
  :deep(p) { margin: 0 0 8px; }
  :deep(img) { max-width: 100%; border-radius: 4px; }
  :deep(blockquote) {
    border-left: 4px solid #07c160;
    padding: 8px 12px; background: #f8f9fa;
    margin: 8px 0; color: #666;
    border-radius: 0 4px 4px 0;
  }
}

.empty-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding-top: 60px;
  color: #ccc;

  .empty-icon { font-size: 36px; margin-bottom: 12px; }
  p { font-size: 13px; margin: 0 0 4px; }
  .empty-hint { font-size: 11px; color: #ddd; }
}

// Fullscreen
.fullscreen-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.fullscreen-container {
  background: #f0f0f0;
  border-radius: 12px;
  overflow: hidden;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.fullscreen-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: #fff;
  font-size: 15px;
  font-weight: 600;

  button {
    width: 32px; height: 32px;
    display: flex; align-items: center; justify-content: center;
    border: none; background: #f0f0f0; border-radius: 6px;
    cursor: pointer; font-size: 16px;
    &:hover { background: #e0e0e0; }
  }
}

.fullscreen-body {
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow-y: auto;
}

.fullscreen-phone {
  background: #1a1a1a;
  border-radius: 36px;
  padding: 12px;

  .phone-screen {
    width: 100%;
    height: 100%;
    background: #fff;
    border-radius: 24px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  .wechat-header { flex-shrink: 0; }
  .wechat-body { flex: 1; overflow-y: auto; }
}

// Modal transition
.modal-enter-active { transition: all 0.3s ease; }
.modal-leave-active { transition: all 0.2s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-from .fullscreen-container { transform: scale(0.9); }
</style>
