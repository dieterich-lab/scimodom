import axios, {
  type AxiosRequestConfig,
  type AxiosResponse,
  type InternalAxiosRequestConfig
} from 'axios'
import { type AccessTokenStore, useAccessToken } from '@/stores/AccessToken.js'
import { DIALOG, type DialogStateStore, useDialogState } from '@/stores/DialogState.js'

const API_PREFIX = '/api/v0/'

// The response type is a compile-time assertion made at the call site;
// Axios does not validate it. Unlike Axios' own signatures, the type parameter
// defaults to `unknown` instead of `any`, so a forgotten annotation fails to compile
// as soon as the data is used, instead of silently disabling type checking.
interface ApiClient {
  get<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>>
  delete<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>>
  post<T = unknown>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>>
  put<T = unknown>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>>
  patch<T = unknown>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>>
}

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
  return typeof x === 'object' && x !== null && 'message' in x && x.message !== undefined
}

function getApiBaseUrl(): string {
  if (import.meta.env.PROD) {
    return API_PREFIX
  } else {
    return import.meta.env?.VITE_API_BASE_URL ? import.meta.env.VITE_API_BASE_URL : API_PREFIX
  }
}

const httpAuthInstance = axios.create({
  baseURL: getApiBaseUrl(),
  withCredentials: false,
  paramsSerializer: { indexes: null }
  // default xsrfCookieName: 'XSRF-TOKEN'
})

const httpInstance = axios.create({
  baseURL: getApiBaseUrl(),
  withCredentials: false,
  paramsSerializer: { indexes: null },
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json'
  }
})

const HTTPAuth: ApiClient = httpAuthInstance
const HTTP: ApiClient = httpInstance

let cachedAccessToken: string | null = null

function prepareAPI(isAuthRequired: boolean) {
  const accessToken = useAccessToken()
  const currentToken = accessToken.token
  if (currentToken !== cachedAccessToken) {
    // use appends an interceptor; it does not replace the previous one...
    httpAuthInstance.interceptors.request.clear()
    httpAuthInstance.interceptors.request.use(
      (config) => handleHTTPAuthRequest(config, accessToken),
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

function handleHTTPAuthRequest(
  config: InternalAxiosRequestConfig,
  accessToken: AccessTokenStore
): InternalAxiosRequestConfig {
  const token = accessToken.token
  config.headers.Authorization = token ? `Bearer ${token}` : ''
  return config
}

function getApiUrl(endpoint: string): string {
  const base = getApiBaseUrl().replace(/\/$/, '')
  return `${base}/${endpoint.replace(/^\//, '')}`
}

// The response type T is declared once, where the request is made
// and inferred here. T is not validated at runtime.
async function handleRequest<T>(
  request: Promise<AxiosResponse<T>>,
  error_context?: string
): Promise<T> {
  let messages: undefined | ErrorMessages
  try {
    const response = await request
    // axios' default validateStatus resolves this promise for 2xx
    if (response.status >= 200 && response.status < 300) {
      return response.data
    }
    messages = getErrorMessagesFromResponse(response, error_context)
  } catch (err) {
    messages = getErrorMessagesFromException(err, error_context)
  }
  throw new RequestError(messages)
}

function getErrorMessagesFromResponse(
  response: AxiosResponse<unknown>,
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

function getErrorMessagesFromException(err: unknown, error_context?: string): ErrorMessages {
  if (axios.isAxiosError(err) && err.response !== undefined) {
    return getErrorMessagesFromResponse(err.response, error_context)
  } else {
    const prefix = error_context ? `${error_context}: ` : ''
    const message = String(err)
    const technical_message = `${prefix}${message}`
    return {
      userMessage: technical_message,
      technicalMessage: technical_message
    }
  }
}

async function handleRequestWithErrorReporting<T>(
  request: Promise<AxiosResponse<T>>,
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
  HTTPAuth,
  getApiBaseUrl,
  getApiUrl,
  prepareAPI,
  handleRequest,
  handleRequestWithErrorReporting,
  RequestError,
  trashRequestErrors
}
