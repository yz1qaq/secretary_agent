import type { ChatApiResponse } from './types'

const FALLBACK_API_URL = 'http://127.0.0.1:9826/'
const configuredApiUrl = import.meta.env.VITE_SECRETARY_API_URL?.trim()

export const secretaryApiUrl = configuredApiUrl || FALLBACK_API_URL

export async function sendMessageToSecretary(
  message: string,
  threadId: string,
): Promise<ChatApiResponse> {
  const response = await fetch(secretaryApiUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      thread_id: threadId,
    }),
  })

  if (!response.ok) {
    let errorMessage = '请求失败，请稍后重试。'

    try {
      const errorData = (await response.json()) as { detail?: string }
      if (errorData.detail) {
        errorMessage = errorData.detail
      }
    } catch {
      errorMessage = `请求失败，状态码 ${response.status}`
    }

    throw new Error(errorMessage)
  }

  return (await response.json()) as ChatApiResponse
}
