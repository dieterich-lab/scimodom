import { defineStore } from 'pinia'
import { jwtDecode } from 'jwt-decode'
import { HTTPSecure } from '@/services'

const REFRESH_GRACE_PERIOD_SECONDS = 30 * 60
const REFRESH_RETRY_INTERVALL_SECONDS = 60

const useAccessToken = defineStore('access_token', {
  state: () => {
    return {
      token: null,
      refresh_requested_epoch: null,
      email: null,
      expire_epoch: null
    }
  },
  actions: {
    get() {
      if (this.token !== null) {
        const now_epoch = Date.now() / 1000
        const seconds_to_expire = this.expire_epoch - now_epoch
        if (seconds_to_expire <= 0) {
          this.token = null
        } else if (seconds_to_expire < REFRESH_GRACE_PERIOD_SECONDS) {
          try_to_refresh_access_token(this)
        }
      }
      return this.token
    },
    set(email, token) {
      const decoded_token = jwtDecode(token)
      this.email = email
      this.token = token
      this.expire_epoch = decoded_token.exp
      this.refresh_requested_epoch = null
    },
    try_to_refresh_access_token() {
      const now_epoch = Date.now() / 1000
      if (this.refresh_requested_epoch !== null) {
        const last_attempt_seconds = now_epoch - this.refresh_requested_epoch
        if (last_attempt_seconds < REFRESH_RETRY_INTERVALL_SECONDS) {
          return
        }
      }
      HTTPSecure.get('/user/refresh_access_token')
        .then((response) => {
          if (response.status == 200) {
            this.set(this.email, response.data.access_token)
          }
        })
        .catch((err) => {
          console.log(`Failed to refresh access token: ${err.text}`)
        })
      this.refresh_requested_epoch = now_epoch
    }
  }
})

export { useAccessToken }
