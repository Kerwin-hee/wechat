/**
 * 图片处理工具
 * - 压缩：>5MB 自动压缩至 <5MB
 * - 格式转换：BMP/TIFF/WebP → PNG
 * - 粘贴图片提取
 */

const MAX_IMAGE_SIZE = 5 * 1024 * 1024 // 5MB
const UNSUPPORTED_FORMATS = ['image/bmp', 'image/tiff', 'image/webp']

/**
 * 判断是否需要格式转换
 */
export function needsFormatConversion(file: File): boolean {
  return UNSUPPORTED_FORMATS.includes(file.type) || file.type === 'image/webp'
}

/**
 * 判断是否需要压缩
 */
export function needsCompression(file: File): boolean {
  return file.size > MAX_IMAGE_SIZE
}

/**
 * 图片文件转换为 PNG（通过 Canvas 重绘）
 */
export function convertToPng(file: File): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    const url = URL.createObjectURL(file)

    img.onload = () => {
      const canvas = document.createElement('canvas')
      canvas.width = img.naturalWidth
      canvas.height = img.naturalHeight
      const ctx = canvas.getContext('2d')!
      ctx.drawImage(img, 0, 0)
      canvas.toBlob(
        (blob) => {
          URL.revokeObjectURL(url)
          if (blob) resolve(blob)
          else reject(new Error('Canvas toBlob failed'))
        },
        'image/png',
        1
      )
    }

    img.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('Image load failed'))
    }

    img.src = url
  })
}

/**
 * 压缩图片到目标大小以内
 */
export async function compressImage(file: File, maxSize: number = MAX_IMAGE_SIZE): Promise<Blob> {
  let quality = 0.9
  let blob: Blob | null = null

  const img = new Image()
  const url = URL.createObjectURL(file)

  await new Promise<void>((resolve, reject) => {
    img.onload = () => resolve()
    img.onerror = () => reject(new Error('Image load failed'))
    img.src = url
  })

  // 尝试不同压缩质量
  for (let i = 0; i < 5; i++) {
    const canvas = document.createElement('canvas')
    let width = img.naturalWidth
    let height = img.naturalHeight

    // 如果质量压缩不够，则缩小尺寸
    if (i >= 3) {
      const ratio = 0.75
      width = Math.round(width * ratio)
      height = Math.round(height * ratio)
    }

    canvas.width = width
    canvas.height = height
    const ctx = canvas.getContext('2d')!
    ctx.drawImage(img, 0, 0, width, height)

    blob = await new Promise<Blob | null>((resolve) => {
      canvas.toBlob(
        (b) => resolve(b),
        'image/jpeg',
        quality
      )
    })

    if (blob && blob.size <= maxSize) break
    quality -= 0.15
  }

  URL.revokeObjectURL(url)
  return blob || file
}

/**
 * 处理上传的图片文件
 * - 自动格式转换
 * - 自动压缩
 * - 返回 base64 DataURL
 */
export async function processImageFile(file: File): Promise<string> {
  let processedFile: File | Blob = file

  // 格式转换
  if (needsFormatConversion(file)) {
    const pngBlob = await convertToPng(file)
    processedFile = new File([pngBlob], file.name.replace(/\.\w+$/, '.png'), {
      type: 'image/png',
    })
  }

  // 压缩
  if (processedFile.size > 10 * 1024 * 1024) {
    throw new Error('图片大小不能超过 10MB，请压缩后重新上传')
  }

  if (needsCompression(processedFile as File)) {
    const compressed = await compressImage(processedFile as File)
    processedFile = compressed
  }

  // 转 DataURL
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => resolve(e.target?.result as string)
    reader.onerror = () => reject(new Error('FileReader error'))
    reader.readAsDataURL(processedFile)
  })
}

/**
 * 从剪贴板事件中提取图片
 */
export function extractImageFromClipboard(
  event: ClipboardEvent
): File | null {
  const items = event.clipboardData?.items
  if (!items) return null

  for (let i = 0; i < items.length; i++) {
    if (items[i].type.startsWith('image/')) {
      return items[i].getAsFile()
    }
  }
  return null
}
