import { defineStore } from 'pinia'
import { jwtDecode } from 'jwt-decode'
import { HTTPSecure } from '@/services'
// import { useLocalStorage } from '@vueuse/core'

const REFRESH_GRACE_PERIOD_SECONDS = 30 * 60
const REFRESH_RETRY_INTERVALL_SECONDS = 60

const useAccessToken = defineStore('access_token', {
  state: () => {
    return {
      _token_cache: null,
      refresh_requested_epoch: null,
      email: null,
      expire_epoch: null
    }
  },
  getters: {
    token() {
      if (this._token_cache !== null) {
        const now_epoch = Date.now() / 1000
        const seconds_to_expire = this.expire_epoch - now_epoch
        if (seconds_to_expire <= 0) {
          this._token_cache = null
        } else if (seconds_to_expire < REFRESH_GRACE_PERIOD_SECONDS) {
          this.try_to_refresh_access_token()
        }
      }
      return this._token_cache
    }
  },
  actions: {
    set(email, token) {
      const decoded_token = jwtDecode(token)
      this.email = email
      this._token_cache = token
      this.expire_epoch = decoded_token.exp
      this.refresh_requested_epoch = null
    },
    unset() {
      this.$reset()
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
