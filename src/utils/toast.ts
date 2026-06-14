/**
 * Toast 提示工具
 */
import { ref } from 'vue'

interface ToastItem {
  id: number
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
  duration: number
}

const toasts = ref<ToastItem[]>([])
let nextId = 0

export function useToast() {
  function show(message: string, type: ToastItem['type'] = 'info', duration: number = 3000) {
    const id = nextId++
    const toast: ToastItem = { id, message, type, duration }
    toasts.value.push(toast)

    setTimeout(() => {
      toasts.value = toasts.value.filter((t) => t.id !== id)
    }, duration)
  }

  function info(msg: string) { show(msg, 'info') }
  function success(msg: string) { show(msg, 'success') }
  function warning(msg: string) { show(msg, 'warning') }
  function error(msg: string) { show(msg, 'error', 5000) }

  return { toasts, show, info, success, warning, error }
}
