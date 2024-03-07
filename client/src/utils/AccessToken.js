import { defineStore } from 'pinia'
import { jwtDecode } from 'jwt-decode'
import { HTTP } from '@/services'

const REFRESH_GRACE_PERIOD_SECONDS = 30 * 60
const REFRESH_RETRY_INTERVALL_SECONDS = 60

const useAccessToken = defineStore('access_token', {
  state: () => {
    return {
      access_token: null,
      refresh_requested_seconds: null
    }
  },
  actions: {
    get() {
      if (!this.access_token) {
        throw Error('No token')
      }
      const decoded_token = jwtDecode(this.access_token)
      const now_seconds = Date.now() / 1000
      const seconds_to_expire = decoded_token.exp - now_seconds

      if (seconds_to_expire <= 0) {
        throw Error('Token expired')
      } else if (seconds_to_expire < REFRESH_GRACE_PERIOD_SECONDS) {
        try_to_refresh_access_token(this)
      }
      return this.access_token
    }
  }
})

function try_to_refresh_access_token(store) {
  const now_seconds = Date.now() / 1000
  if (store.refresh_requested_seconds !== null) {
    const last_attempt_seconds = now_seconds - store.refresh_requested_seconds
    if (last_attempt_seconds < REFRESH_RETRY_INTERVALL_SECONDS) {
      return
    }
  }

  HTTP.get('/user/refresh_access_token')
    .then((response) => {
      if (response.status == 200) {
        store.access_token = response.data.access_token
      }
    })
    .catch((err) => {
      console.log(`Failed to refresh access token: ${err.text}`)
    })
  this.refresh_requested_seconds = now_seconds
}

export { useAccessToken }
