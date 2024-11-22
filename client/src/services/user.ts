import { DIALOG, type DialogStateStore } from '@/stores/DialogState'
import {
  handleRequestWithErrorReporting,
  HTTP,
  HTTPSecure,
  prepareAPI,
  trashRequestErrors
} from '@/services/API'
import type { AccessTokenStore } from '@/stores/AccessToken'

interface MayChangeDatasetResponse {
  write_access: boolean
}

interface LoginResponse {
  access_token: string
}

async function login(
  email: string,
  password: string,
  accessToken: AccessTokenStore,
  dialogState: DialogStateStore
): Promise<void> {
  const request = HTTP.post('/user/login', { email, password })
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
  const request = HTTPSecure.post('/user/change_password', { password })
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
  const request = HTTP.post('/user/do_password_reset', {
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

async function mayChangeDataset(
  datasetId: string,
  dialogState: DialogStateStore
): Promise<boolean> {
  const data = await handleRequestWithErrorReporting<MayChangeDatasetResponse>(
    HTTPSecure.get(`/user/may_change_dataset/${datasetId}`),
    `Failed to determine if logged-in user may change dataset '${datasetId}'`,
    dialogState
  )
  return data.write_access
}

async function registerUser(
  email: string,
  password: string,
  dialogState: DialogStateStore
): Promise<void> {
  const request = HTTP.post('/user/register_user', { email, password })
  const errorState = { state: DIALOG.REGISTER_ENTER_DATA }
  await handleRequestWithErrorReporting(
    request,
    'Failed to register user',
    dialogState,
    errorState
  ).then(() => {
    dialogState.message =
      'We just sent you an email with a link to confirm your address. Please use the link to complete the registration.'
    dialogState.state = DIALOG.ALERT
  })
}

async function requestPasswordReset(email: string, dialogState: DialogStateStore): Promise<void> {
  const request = HTTP.post('/user/request_password_reset', { email })
  await handleRequestWithErrorReporting(request, 'Failed to request password reset', dialogState, {
    state: DIALOG.RESET_PASSWORD_REQUEST
  })
    .then(() => {
      dialogState.message =
        'We just sent you an email with a link. Please visit the link to set your new password.'
      dialogState.state = DIALOG.ALERT
    })
    .catch((e) => trashRequestErrors(e))
}

export {
  login,
  changePassword,
  resetPassword,
  mayChangeDataset,
  registerUser,
  requestPasswordReset
}
