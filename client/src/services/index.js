import axios from 'axios'

const HTTP = axios.create({
  baseURL: `http://127.0.0.1:5000/api/v0`,
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
  }
}
