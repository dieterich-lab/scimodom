import axios, { type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'
import { type AccessTokenStore, useAccessToken } from '@/stores/AccessToken.js'
import { DIALOG, type DialogStateStore, useDialogState } from '@/stores/DialogState.js'

// TODO: refactor HTTP as HTTPPublic either export service, or
// rename exported functions

interface ErrorResponse {
  message: string
  user_error?: string // For expected problems the backend may supply detailed instructions for the user
}

function isErrorResponse(x: unknown): x is ErrorResponse {
  return (x as ErrorResponse).message !== undefined
}

function getApiBaseUrl(): string {
  if (import.meta.env.PROD) {
    return '/api/v0/'
  } else {
    return import.meta.env?.VITE_API_BASE_URL ? import.meta.env.VITE_API_BASE_URL : '/api/v0/'
  }
}

const HTTPSecure = axios.create({
  baseURL: getApiBaseUrl(),
  withCredentials: false
  // default xsrfCookieName: 'XSRF-TOKEN'
})

HTTPSecure.interceptors.response.use(
  (response) => {
    // 2xx
    return response
  },
  (error) => {
    // outside 2xx
    switch (error.response.status) {
      case 401:
        break
      case 404:
        // router push to 404
        break
      default:
        break
    }
    return Promise.reject(error)
  }
)

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
  let user_message = ''
  try {
    const response = await request
    if (response.status === 200) {
      return response.data as T
    }
    user_message = getErrorMessageFromResponse(response, error_context)
  } catch (err) {
    user_message = getErrorMessageFromException(err as object, error_context)
  }
  console.log(user_message)
  throw new Error(user_message)
}

function getErrorMessageFromResponse(response: AxiosResponse, error_context?: string): string {
  const prefix = error_context ? `${error_context}: ` : ''
  if (isErrorResponse(response.data)) {
    const errorResponse = response.data
    if (errorResponse.user_error) {
      return errorResponse.user_error
    } else {
      return `${prefix}HTTP status ${response.status} - ${errorResponse.message}`
    }
  } else {
    return `${prefix}HTTP status ${response.status} - please contact the system administrator.`
  }
}

function getErrorMessageFromException(err: object, error_context?: string): string {
  if ('response' in err) {
    return getErrorMessageFromResponse(err.response as AxiosResponse, error_context)
  } else {
    const prefix = error_context ? `${error_context}: ` : ''
    const message = err.toString()
    return `${prefix}${message}`
  }
}

async function handleRequestWithErrorReporting<T>(
  request: Promise<AxiosResponse>,
  error_context: string,
  dialogState: DialogStateStore,
  dialogStateTemplate?: Partial<DialogStateStore>
): Promise<T> {
  try {
    return handleRequest(request, error_context)
  } catch (err) {
    dialogState.$patch({
      state: DIALOG.ERROR_ALERT,
      message: `${err}`,
      ...dialogStateTemplate
    })
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
  handleRequestWithErrorReporting
}
