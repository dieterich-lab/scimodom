import { defineStore } from 'pinia'
import { jwtDecode } from 'jwt-decode'
import { HTTPSecure } from '@/services/API'

const REFRESH_GRACE_PERIOD_SECONDS = 30 * 60
const REFRESH_RETRY_INTERVALL_SECONDS = 60

const useAccessToken = defineStore('access_token', {
  state: () => {
    return {
      _tokenCache: null,
      refreshRequestedEpoch: null,
      email: null,
      expireEpoch: null
    }
  },
  getters: {
    token(state) {
      if (state._tokenCache !== null) {
        const now_epoch = Date.now() / 1000
        const seconds_to_expire = state.expireEpoch - now_epoch
        if (seconds_to_expire <= 0) {
          log.console('token getter: Access token expired - unsetting.')
          this.unset()
        }
      }
      return state._tokenCache
    }
  },
  actions: {
    set(email, token) {
      const decoded_token = jwtDecode(token)
      this.email = email
      this._tokenCache = token
      this.expireEpoch = decoded_token.exp
      this.refreshRequestedEpoch = null
      console.log(`Got new access token.`)
    },
    unset() {
      this.$reset()
    },
    considerToRefresh() {
      if (this.expireEpoch === null) {
        return
      }
      const now_epoch = Date.now() / 1000
      const seconds_to_expire = this.expireEpoch - now_epoch
      if (seconds_to_expire > REFRESH_GRACE_PERIOD_SECONDS) {
        return
      }
      if (seconds_to_expire < 1) {
        console.log('considerToRefresh: Access token expired - unsetting.')
        this.unset()
        return
      }

      if (this.refreshRequestedEpoch !== null) {
        const last_attempt_seconds = now_epoch - this.refreshRequestedEpoch
        if (last_attempt_seconds < REFRESH_RETRY_INTERVALL_SECONDS) {
          return
        }
      }
      this.refresh()
    },
    refresh() {
      const now_epoch = Date.now() / 1000
      console.log('Requesting access token refresh.')
      HTTPSecure.get('/user/refresh_access_token')
        .then((response) => {
          if (response.status == 200) {
            this.set(this.email, response.data.access_token)
          }
        })
        .catch((err) => {
          console.log(`Failed to refresh access token: ${err.text}`)
        })
      this.refreshRequestedEpoch = now_epoch
    }
  }
})

export { useAccessToken }
