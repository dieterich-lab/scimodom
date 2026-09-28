import { DIALOG, type DialogStateStore } from '@/stores/DialogState'
import {
  handleRequestWithErrorReporting,
  HTTP,
  HTTPSecure,
  prepareAPI,
  trashRequestErrors
} from '@/services/API'
import type { AccessTokenStore } from '@/stores/AccessToken'

interface LoginResponse {
  access_token: string
}

async function login(
  email: string,
  password: string,
  accessToken: AccessTokenStore,
  dialogState: DialogStateStore
): Promise<void> {
  const request = HTTP.post('/sessions', { email, password })
  const result = await handleRequestWithErrorReporting<LoginResponse>(
    request,
    'While logging in',
    dialogState,
    { state: DIALOG.LOGIN, email }
  )
  accessToken.set(email, result.access_token)
  dialogState.state = DIALOG.NONE
  prepareAPI(false)
}

async function changePassword(password: string, dialogState: DialogStateStore): Promise<void> {
  const request = HTTPSecure.put('/users/me/password', { password })
  await handleRequestWithErrorReporting(request, 'Failed to change password', dialogState).then(
    () => {
      dialogState.message = 'Password changed successfully.'
      dialogState.state = DIALOG.ALERT
    }
  )
}

async function resetPassword(
  email: string,
  password: string,
  token: string,
  dialogState: DialogStateStore
): Promise<void> {
  const request = HTTP.post('/users/password/reset', {
    email,
    password,
    token
  })
  await handleRequestWithErrorReporting(request, 'Failed to reset password', dialogState).then(
    () => {
      dialogState.message = 'Password set successfully.'
      dialogState.state = DIALOG.ALERT
    }
  )
}

async function registerUser(
  email: string,
  password: string,
  dialogState: DialogStateStore
): Promise<void> {
  const request = HTTP.post('/users', { email, password })
  const errorState = { state: DIALOG.REGISTER_ENTER_DATA }
  await handleRequestWithErrorReporting(
    request,
    'Failed to register user',
    dialogState,
    errorState
  ).then(() => {
    dialogState.message =
      'An email containing a link has been sent to your address. Please click the link to complete your registration.'
    dialogState.state = DIALOG.ALERT
  })
}

async function requestPasswordReset(email: string, dialogState: DialogStateStore): Promise<void> {
  const request = HTTP.post('/users/password/request', { email })
  await handleRequestWithErrorReporting(request, 'Failed to request password reset', dialogState, {
    state: DIALOG.RESET_PASSWORD_REQUEST
  })
    .then(() => {
      dialogState.message =
        'An email containing a link has been sent to your address. Please click the link to reset your password.'
      dialogState.state = DIALOG.ALERT
    })
    .catch((e) => trashRequestErrors(e))
}

export { login, changePassword, resetPassword, registerUser, requestPasswordReset }
