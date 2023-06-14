import axios from 'axios'

const HTTP = axios.create({
  baseURL: `http://localhost:3000`,
  withCredentials: false,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  },
})

export default {
  getMods() {
    return HTTP.get('/modification')
  },
}
