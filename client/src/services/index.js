import axios from 'axios'
import {API_BASE_URL} from "/config.js";

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
