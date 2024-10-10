import axios, { type InternalAxiosRequestConfig } from 'axios'
import { type AccessTokenStore, useAccessToken } from '@/stores/AccessToken.js'
import { DIALOG, useDialogState } from '@/stores/DialogState.js'

// TODO: refactor HTTP as HTTPPublic either export service, or
// rename exported functions

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

export { HTTP, HTTPSecure, getApiBaseUrl, getApiUrl, prepareAPI }
