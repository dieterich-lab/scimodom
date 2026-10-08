import { expect, test, vi } from 'vitest'
import { AxiosError, type AxiosResponse } from 'axios'
import { RequestError, handleRequest } from '@/services/API'

vi.mock('@/stores/AccessToken.js', () => ({ useAccessToken: vi.fn() }))
vi.mock('@/stores/DialogState.js', () => ({ DIALOG: {}, useDialogState: vi.fn() }))

interface A {
  a: number
}

function response(status: number, data: unknown): AxiosResponse {
  return { status, data } as AxiosResponse
}

test('handleRequest returns the response data for 2xx', async () => {
  const data = await handleRequest(Promise.resolve(response(200, { a: 1 }) as AxiosResponse<A>))
  expect(data).toStrictEqual({ a: 1 })
})

test('handleRequest uses the API error message for an HTTP error response', async () => {
  const err = new AxiosError(
    'failed',
    'ERR_BAD_REQUEST',
    undefined,
    undefined,
    response(404, {
      message: 'not found',
      user_message: 'Nothing here'
    })
  )
  const promise = handleRequest(Promise.reject(err), 'context')
  await expect(promise).rejects.toBeInstanceOf(RequestError)
  await expect(promise).rejects.toMatchObject({
    userMessage: 'Nothing here',
    message: 'context: HTTP status 404 - not found'
  })
})

test('handleRequest copes with an error response whose body is null', async () => {
  const err = new AxiosError(
    'failed',
    'ERR_BAD_RESPONSE',
    undefined,
    undefined,
    response(500, null)
  )
  await expect(handleRequest(Promise.reject(err))).rejects.toMatchObject({
    message: 'HTTP status 500 - please contact the system administrator.'
  })
})

test('handleRequest copes with an axios error without a response (network error)', async () => {
  const err = new AxiosError('Network Error', 'ERR_NETWORK')
  await expect(handleRequest(Promise.reject(err))).rejects.toMatchObject({
    message: 'AxiosError: Network Error'
  })
})

test('handleRequest copes with a thrown non-object', async () => {
  await expect(handleRequest(Promise.reject('boom'), 'ctx')).rejects.toMatchObject({
    message: 'ctx: boom'
  })
})
