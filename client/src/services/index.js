import axios from 'axios'
import { API_BASE_URL } from '/config.js?url'

// refactor HTTP public service either export service, or
// rename exported functions

// const authService = axios.create({
//     baseURL:
//     withCredentials: true,
//     xsrfCookieName: 'csrf_access_token'
// })
// export { authService };

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
