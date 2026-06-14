import { onMounted, onUnmounted } from 'vue'
import { useEditorStore } from '../stores/editor'

export function useAutoSave(intervalMs: number = 30000) {
  const store = useEditorStore()
  let timer: ReturnType<typeof setInterval> | null = null

  function startAutoSave() {
    stopAutoSave()
    timer = setInterval(async () => {
      if (store.isDirty && store.currentArticleId) {
        await store.saveArticle()
      }
    }, intervalMs)
  }

  function stopAutoSave() {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  // 手动保存 (Ctrl+S)
  function handleKeyDown(e: KeyboardEvent) {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault()
      if (store.isDirty && store.currentArticleId) {
        store.saveArticle()
      }
    }
  }

  // 离开页面提醒
  function handleBeforeUnload(e: BeforeUnloadEvent) {
    if (store.isDirty) {
      e.preventDefault()
    }
  }

  onMounted(() => {
    startAutoSave()
    window.addEventListener('keydown', handleKeyDown)
    window.addEventListener('beforeunload', handleBeforeUnload)
  })

  onUnmounted(() => {
    stopAutoSave()
    window.removeEventListener('keydown', handleKeyDown)
    window.removeEventListener('beforeunload', handleBeforeUnload)
  })

  return {
    startAutoSave,
    stopAutoSave,
  }
}
