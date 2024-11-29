import axios, { type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'
import { type AccessTokenStore, useAccessToken } from '@/stores/AccessToken.js'
import { DIALOG, type DialogStateStore, useDialogState } from '@/stores/DialogState.js'

const API_PREFIX = '/api/v0/'

interface ErrorResponse {
  message: string
  user_message?: string // For expected problems the backend may supply detailed instructions for the user
}

interface ErrorMessages {
  userMessage: string
  technicalMessage: string
}

class RequestError extends Error {
  userMessage: string
  constructor(messages: ErrorMessages) {
    super(messages.technicalMessage)
    this.userMessage = messages.userMessage
  }
}

function isErrorResponse(x: unknown): x is ErrorResponse {
  return (x as ErrorResponse).message !== undefined
}

function getApiBaseUrl(): string {
  if (import.meta.env.PROD) {
    return API_PREFIX
  } else {
    return import.meta.env?.VITE_API_BASE_URL ? import.meta.env.VITE_API_BASE_URL : API_PREFIX
  }
}

const HTTPSecure = axios.create({
  baseURL: getApiBaseUrl(),
  withCredentials: false
  // default xsrfCookieName: 'XSRF-TOKEN'
})

const HTTP = axios.create({
  baseURL: getApiBaseUrl(),
  withCredentials: false,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json'
  }
})

let cachedAccessToken: string | null = null

function prepareAPI(isAuthRequired: boolean) {
  const accessToken = useAccessToken()
  const currentToken = accessToken.token
  if (currentToken !== cachedAccessToken) {
    HTTPSecure.interceptors.request.use(
      (config) => handleHTTPSecureRequest(config, accessToken),
      (error) => Promise.reject(error)
    )
    cachedAccessToken = currentToken
  }
  if (isAuthRequired && currentToken === null) {
    const dialogState = useDialogState()
    dialogState.message = 'You are not logged in - maybe your session expired.'
    dialogState.state = DIALOG.LOGIN
  }
  accessToken.considerToRefresh()
}

function handleHTTPSecureRequest(
  config: InternalAxiosRequestConfig,
  accessToken: AccessTokenStore
): InternalAxiosRequestConfig {
  const token = accessToken.token
  config.headers.Authorization = token ? `Bearer ${token}` : ''
  return config
}

function getApiUrl(endpoint: string): string {
  const base = getApiBaseUrl()
  return `${base}${endpoint}`
}

async function handleRequest<T>(
  request: Promise<AxiosResponse>,
  error_context?: string
): Promise<T> {
  let messages: undefined | ErrorMessages
  try {
    const response = await request
    if (response.status === 200) {
      return response.data as T
    }
    messages = getErrorMessagesFromResponse(response, error_context)
  } catch (err) {
    messages = getErrorMessagesFromException(err as object, error_context)
  }
  throw new RequestError(messages)
}

function getErrorMessagesFromResponse(
  response: AxiosResponse,
  error_context?: string
): ErrorMessages {
  const prefix = error_context ? `${error_context}: ` : ''
  if (isErrorResponse(response.data)) {
    const errorResponse = response.data
    const technical_message = `${prefix}HTTP status ${response.status} - ${errorResponse.message}`
    if (errorResponse.user_message) {
      return {
        userMessage: errorResponse.user_message,
        technicalMessage: technical_message
      }
    } else {
      return {
        userMessage: technical_message,
        technicalMessage: technical_message
      }
    }
  } else {
    const technical_message = `${prefix}HTTP status ${response.status} - please contact the system administrator.`
    return {
      userMessage: technical_message,
      technicalMessage: technical_message
    }
  }
}

function getErrorMessagesFromException(err: object, error_context?: string): ErrorMessages {
  if ('response' in err) {
    return getErrorMessagesFromResponse(err.response as AxiosResponse, error_context)
  } else {
    const prefix = error_context ? `${error_context}: ` : ''
    const message = err.toString()
    const technical_message = `${prefix}${message}`
    return {
      userMessage: technical_message,
      technicalMessage: technical_message
    }
  }
}

async function handleRequestWithErrorReporting<T>(
  request: Promise<AxiosResponse>,
  error_context: string,
  dialogState: DialogStateStore,
  dialogStateTemplate?: Partial<DialogStateStore>
): Promise<T> {
  try {
    return await handleRequest(request, error_context)
  } catch (err) {
    const technicalMessage = `${err}`
    console.log(technicalMessage)
    const userMessage = err instanceof RequestError ? err.userMessage : technicalMessage
    dialogState.$patch({
      state: DIALOG.ERROR_ALERT,
      message: userMessage,
      ...dialogStateTemplate
    })
    throw err
  }
}

function trashRequestErrors(err: unknown) {
  // This function is intended to be used like this:
  //
  // handleRequestWithErrorReporting(...)
  //     .catch((e) => trashRequestErrors(e))
  //
  // It will silently ignore all errors of type RequestError and
  // re-throws all others.
  //
  // Why?
  //
  // In general RequestErrors are already handled in the handleRequestWithErrorReporting()
  // function. Most of the time this is all which can and should be done. Sometimes the
  // calling function may need to do more to recover. In this case rashResponseErrors()
  // can be just used in the specific error handler.
  //
  // Also, we still want a full backtrace of an unhandled exception in the
  // case that initial exception is *not* a RequestError, e.g. a pure frontend
  // issue.
  //
  if (err instanceof RequestError) {
    return
  } else {
    throw err
  }
}

export {
  HTTP,
  HTTPSecure,
  getApiBaseUrl,
  getApiUrl,
  prepareAPI,
  handleRequest,
  handleRequestWithErrorReporting,
  trashRequestErrors
}
