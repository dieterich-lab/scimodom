import axios from 'axios'
import { API_BASE_URL } from '/config.js?url'

// TODO: refactor HTTP as HTTPPublic either export service, or
// rename exported functions

// const HTTPSecure = {
//     connection: null,
//     get: (url) => {
//         this.init()
//         this.connection.get(url)
//     },
//     init: () => {
//         if ( this.connection !== null ) {
//             return
//         }
//         this.connection =
//     }
// }

const HTTPSecure = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: false
  // default xsrfCookieName: 'XSRF-TOKEN'
})

// this dosn't work getActivePinia() was called but there was no active Pinia
// HTTPSecure.interceptors.request.use(
//     (config) => {
//         const token = accessToken.access_token
//         const auth = token ? `Bearer ${token}` : ''
//         config.headers.common['Authorization'] = auth
//         return config
//     },
//     (error) => Promise.reject(error),
// )

HTTPSecure.interceptors.response.use(
  (response) => {
    // 2xx
    return response
  },
  (error) => {
    // outside 2xx
    switch (error.response.status) {
      case 401:
        // jwt refresh needed - check COOKIE_EXPIRED_MSG = 'Token has expired'
        // HTTPSecure.defaults.xsrfCookieName = 'csrf_refresh_token'
        // here call api to refresh token
        // HTTPSecure.defaults.xsrfCookieName = 'csrf_access_token'
        // return HTTPSecure(error.config)
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

export default {
  getConcurrent(endpoints) {
    return Promise.all(endpoints.map((endpoint) => HTTP.get(endpoint)))
  },
  getEndpoint(endpoint) {
    return HTTP.get(endpoint)
  },
  get(endpoint, config) {
    return HTTP.get(endpoint, config)
  },
  getUri() {
    return HTTP.getUri(HTTP.config)
  }
}

export { HTTPSecure }
export { HTTP }
