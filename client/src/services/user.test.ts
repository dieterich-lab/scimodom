import { test, expect, vi, beforeEach } from 'vitest'
import {
  login,
  changePassword,
  resetPassword,
  registerUser,
  requestPasswordReset
} from '@/services/user'
import {
  handleRequestWithErrorReporting,
  HTTP,
  HTTPSecure,
  prepareAPI,
  trashRequestErrors
} from '@/services/API'
import { DIALOG, type DialogStateStore } from '@/stores/DialogState'
import { type AccessTokenStore } from '@/stores/AccessToken'

vi.mock('@/services/API', () => ({
  HTTP: { post: vi.fn().mockResolvedValue({}) },
  HTTPSecure: { put: vi.fn().mockResolvedValue({}) },
  handleRequestWithErrorReporting: vi.fn(),
  prepareAPI: vi.fn(),
  trashRequestErrors: vi.fn()
}))

const mockedHttpPost = vi.mocked(HTTP.post)
const mockedSecurePut = vi.mocked(HTTPSecure.put)
const mockedHandle = vi.mocked(handleRequestWithErrorReporting)
const mockedPrepareAPI = vi.mocked(prepareAPI)
const mockedTrash = vi.mocked(trashRequestErrors)

beforeEach(() => {
  mockedHttpPost.mockClear()
  mockedSecurePut.mockClear()
  mockedHandle.mockReset()
  mockedPrepareAPI.mockClear()
  mockedTrash.mockClear()
})

function makeDialogState(): DialogStateStore {
  return { message: '', state: DIALOG.NONE } as DialogStateStore
}

function makeAccessToken(): AccessTokenStore & { set: ReturnType<typeof vi.fn> } {
  return { set: vi.fn() } as unknown as AccessTokenStore & {
    set: ReturnType<typeof vi.fn>
  }
}

test('login posts credentials to /sessions, sets store, dialog, and prepareAPI', async () => {
  mockedHandle.mockResolvedValueOnce({ access_token: 'tok123' })
  const accessToken = makeAccessToken()
  const dialogState = makeDialogState()

  await login('a@b.c', 'pw', accessToken, dialogState)

  expect(mockedHttpPost).toHaveBeenCalledWith('/sessions', {
    email: 'a@b.c',
    password: 'pw'
  })
  expect(mockedHandle).toHaveBeenCalledWith(expect.anything(), 'While logging in', dialogState, {
    state: DIALOG.LOGIN,
    email: 'a@b.c'
  })
  expect(accessToken.set).toHaveBeenCalledWith('a@b.c', 'tok123')
  expect(dialogState.state).toBe(DIALOG.NONE)
  expect(mockedPrepareAPI).toHaveBeenCalledWith(false)
})

test('login does not touch the store when the request fails', async () => {
  const error = new Error()
  mockedHandle.mockRejectedValueOnce(error)
  const accessToken = makeAccessToken()
  const dialogState = makeDialogState()
  dialogState.state = DIALOG.LOGIN

  await expect(login('a@b.c', 'pw', accessToken, dialogState)).rejects.toBe(error)

  expect(accessToken.set).not.toHaveBeenCalled()
  expect(mockedPrepareAPI).not.toHaveBeenCalled()
  expect(dialogState.state).toBe(DIALOG.LOGIN)
})

test('changePassword puts to /users/me/passwords and sets dialog', async () => {
  mockedHandle.mockResolvedValueOnce(undefined)
  const dialogState = makeDialogState()

  await changePassword('new-pw', dialogState)

  expect(mockedSecurePut).toHaveBeenCalledWith('/users/me/password', {
    password: 'new-pw'
  })
  expect(mockedHandle).toHaveBeenCalledWith(
    expect.anything(),
    'Failed to change password',
    dialogState
  )
  expect(dialogState.message).toBe('Password changed successfully.')
  expect(dialogState.state).toBe(DIALOG.ALERT)
})

test('changePassword does not set the success dialog on failure', async () => {
  const error = new Error()
  mockedHandle.mockRejectedValueOnce(error)
  const dialogState = makeDialogState()
  dialogState.message = 'unchanged'

  await expect(changePassword('new-pw', dialogState)).rejects.toBe(error)

  expect(dialogState.message).toBe('unchanged')
})

test('resetPassword posts to /users/password/reset', async () => {
  mockedHandle.mockResolvedValueOnce(undefined)
  const dialogState = makeDialogState()

  await resetPassword('a@b.c', 'new-pw', 'token456', dialogState)

  expect(mockedHttpPost).toHaveBeenCalledWith('/users/password/reset', {
    email: 'a@b.c',
    password: 'new-pw',
    token: 'token456'
  })
  expect(mockedHandle).toHaveBeenCalledWith(
    expect.anything(),
    'Failed to reset password',
    dialogState
  )
  expect(dialogState.message).toBe('Password set successfully.')
  expect(dialogState.state).toBe(DIALOG.ALERT)
})

test('registerUser posts to /users', async () => {
  mockedHandle.mockResolvedValueOnce(undefined)
  const dialogState = makeDialogState()

  await registerUser('a@b.c', 'pw', dialogState)

  expect(mockedHttpPost).toHaveBeenCalledWith('/users', {
    email: 'a@b.c',
    password: 'pw'
  })
  expect(mockedHandle).toHaveBeenCalledWith(
    expect.anything(),
    'Failed to register user',
    dialogState,
    { state: DIALOG.REGISTER_ENTER_DATA }
  )
  expect(dialogState.message).toMatch(/An email containing a link has been sent to your address/)
  expect(dialogState.state).toBe(DIALOG.ALERT)
})

test('requestPasswordReset posts to /users/password/request', async () => {
  mockedHandle.mockResolvedValueOnce(undefined)
  const dialogState = makeDialogState()

  await requestPasswordReset('a@b.c', dialogState)

  expect(mockedHttpPost).toHaveBeenCalledWith('/users/password/request', {
    email: 'a@b.c'
  })
  expect(mockedHandle).toHaveBeenCalledWith(
    expect.anything(),
    'Failed to request password reset',
    dialogState,
    { state: DIALOG.RESET_PASSWORD_REQUEST }
  )
  expect(dialogState.message).toMatch(/An email containing a link has been sent to your address/)
  expect(dialogState.state).toBe(DIALOG.ALERT)
})

test('requestPasswordReset swallows errors via trashRequestErrors', async () => {
  const error = new Error()
  mockedHandle.mockRejectedValueOnce(error)
  const dialogState = makeDialogState()

  await requestPasswordReset('a@b.c', dialogState)

  expect(mockedTrash).toHaveBeenCalledWith(error)
  // success dialog must not be set when the request fails
  expect(dialogState.state).toBe(DIALOG.NONE)
})
