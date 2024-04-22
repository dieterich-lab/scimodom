import axios from 'axios'
import { API_BASE_URL } from '/config.js?url'
import { useAccessToken } from '@/stores/AccessToken.js'
import { DIALOG, useDialogState } from '@/stores/DialogState.js'

// TODO: refactor HTTP as HTTPPublic either export service, or
// rename exported functions

const HTTPSecure = axios.create({
  baseURL: API_BASE_URL,
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
  baseURL: API_BASE_URL,
  withCredentials: false,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json'
  }
})

let cachedAccessToken = null

function prepareAPI(isAuthRequired) {
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

function handleHTTPSecureRequest(config, accessToken) {
  const token = accessToken.token
  config.headers.Authorization = token ? `Bearer ${token}` : ''
  return config
}

function getApiUrl(endpoint) {
  return `${API_BASE_URL}${endpoint}`
}

export { HTTP, HTTPSecure, getApiUrl, prepareAPI }
