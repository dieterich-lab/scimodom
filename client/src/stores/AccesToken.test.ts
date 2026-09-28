import { test, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAccessToken } from '@/stores/AccessToken'
import { HTTPSecure } from '@/services/API'
import { jwtDecode } from 'jwt-decode'

vi.mock('@/services/API', () => ({
  HTTPSecure: { post: vi.fn() }
}))

vi.mock('jwt-decode', () => ({
  jwtDecode: vi.fn()
}))

const mockedPost = vi.mocked(HTTPSecure.post)
const mockedDecode = vi.mocked(jwtDecode)

const NOW_SECONDS = 1_700_000_000

beforeEach(() => {
  setActivePinia(createPinia())
  mockedPost.mockReset()
  mockedDecode.mockReset()
  vi.useFakeTimers()
  vi.setSystemTime(NOW_SECONDS * 1000)
})

afterEach(() => {
  vi.useRealTimers()
})

function decodeWithExp(exp: number | undefined): void {
  mockedDecode.mockReturnValueOnce({ exp } as never)
}

test('set stores the token, email, and expiry', () => {
  decodeWithExp(NOW_SECONDS + 3600)
  const store = useAccessToken()

  store.set('a@b.c', 'tok')

  expect(store.email).toBe('a@b.c')
  expect(store.token).toBe('tok')
  expect(store.expireEpoch).toBe(NOW_SECONDS + 3600)
  expect(store.refreshRequestedEpoch).toBeNull()
})

test('set throws when the token has no exp', () => {
  decodeWithExp(undefined)
  const store = useAccessToken()

  expect(() => store.set('a@b.c', 'tok')).toThrow('Got JWT token without expiry')
})

test('unset clears all state', () => {
  decodeWithExp(NOW_SECONDS + 3600)
  const store = useAccessToken()
  store.set('a@b.c', 'tok')

  store.unset()

  expect(store.email).toBeNull()
  expect(store.token).toBeNull()
  expect(store.expireEpoch).toBeNull()
  expect(store.refreshRequestedEpoch).toBeNull()
})

test('token getter returns the token when it is still valid', () => {
  decodeWithExp(NOW_SECONDS + 3600)
  const store = useAccessToken()
  store.set('a@b.c', 'token123')

  expect(store.token).toBe('token123')
})

test('token getter returns null when the token has expired', () => {
  decodeWithExp(NOW_SECONDS - 1)
  const store = useAccessToken()
  store.set('a@b.c', 'tok')

  // getter nulls the cache in place
  expect(store.token).toBeNull()
  expect(store.token).toBeNull()
})

test('token getter returns null when the token is corrupt', () => {
  decodeWithExp(undefined)
  const store = useAccessToken()

  // set() would throw, so we need to simulate a corrupt state...
  store._tokenCache = 'tok'
  store.expireEpoch = null

  expect(store.token).toBeNull()
})

test('considerToRefresh is a no-op when there is no expiry', () => {
  const store = useAccessToken()

  store.considerToRefresh()

  expect(mockedPost).not.toHaveBeenCalled()
  expect(store.refreshRequestedEpoch).toBeNull()
})

test('considerToRefresh is a no-op when there is more than the grace period left', () => {
  decodeWithExp(NOW_SECONDS + 3600)
  const store = useAccessToken()
  store.set('a@b.c', 'tok')

  store.considerToRefresh()

  expect(mockedPost).not.toHaveBeenCalled()
})

test('considerToRefresh unsets the store when the token has expired', () => {
  decodeWithExp(NOW_SECONDS - 1)
  const store = useAccessToken()
  store.email = 'a@b.c'
  store._tokenCache = 'tok'
  store.expireEpoch = NOW_SECONDS - 1

  store.considerToRefresh()

  expect(mockedPost).not.toHaveBeenCalled()
  expect(store.email).toBeNull()
  expect(store.token).toBeNull()
})

test('considerToRefresh refreshes when within the grace period', async () => {
  decodeWithExp(NOW_SECONDS + 60) // 60s left within the 30min grace period
  mockedPost.mockResolvedValueOnce({ status: 200, data: { access_token: 'new' } })
  decodeWithExp(NOW_SECONDS + 3600) // the new token's expiry

  const store = useAccessToken()
  store.set('a@b.c', 'tok')

  store.considerToRefresh()
  await Promise.resolve() // flush the .then chain

  expect(mockedPost).toHaveBeenCalledWith('/sessions/refresh')
})

test('considerToRefresh refreshes again after the retry interval', async () => {
  decodeWithExp(NOW_SECONDS + 60)
  mockedPost.mockResolvedValueOnce({ status: 200, data: { access_token: 'new' } })
  decodeWithExp(NOW_SECONDS + 3600)

  const store = useAccessToken()
  store.set('a@b.c', 'tok')
  store.refreshRequestedEpoch = NOW_SECONDS - 120 // 2 minutes ago, > 60s

  store.considerToRefresh()
  await Promise.resolve()

  expect(mockedPost).toHaveBeenCalled()
})

test('refresh GETs /sessions/refresh and updates the token', async () => {
  decodeWithExp(NOW_SECONDS + 3600)
  const store = useAccessToken()
  store.set('a@b.c', 'old')
  mockedPost.mockResolvedValueOnce({ status: 200, data: { access_token: 'new' } })
  decodeWithExp(NOW_SECONDS + 7200)

  store.refresh()
  await Promise.resolve()

  expect(mockedPost).toHaveBeenCalledWith('/sessions/refresh')
  expect(store.token).toBe('new')
  expect(store.email).toBe('a@b.c')
})

test('refresh logs and keeps the old token when the request fails', async () => {
  const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})

  // override the factory default...
  mockedPost.mockReset()
  mockedPost.mockRejectedValueOnce({ text: 'reject' })

  decodeWithExp(NOW_SECONDS + 3600)
  const store = useAccessToken()
  store.set('a@b.c', 'old')

  store.refresh()
  await vi.waitFor(() => {
    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining('Failed to refresh access token')
    )
  })

  expect(store.token).toBe('old')
  consoleSpy.mockRestore()
})
