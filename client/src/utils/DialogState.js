import { getCurrentInstance, reactive } from 'vue'
import { defineStore } from 'pinia'

const DIALOG = Object.freeze({
  NONE: Symbol('NONE'),
  LOGIN: Symbol('LOGIN'),
  LOGIN_FAILED: Symbol('LOGIN_FAILED'),
  REGISTER_ENTER_DATA: Symbol('REGISTER_ENTER_DATA'),
  REGISTER_CHECK_EMAIL: Symbol('REGISTER_CHECK_EMAIL'),
  REGISTER_SUCCESS: Symbol('REGISTER_SUCCESS'),
  RESET_PASSWORD_CHECK_EMAIL: Symbol('RESET_PASSWORD_CHECK_EMAIL'),
  RESET_PASSWORD_NEW_PASSWORD: Symbol('RESET_PASSWORD_NEW_PASSWORD'),
  GO_AWAY_HACKER: Symbol('GO_AWAY_HACKER')
})

const useDialogState = defineStore('dialogState', {
  state: () => {
    return {
      state: DIALOG.NONE,
      email: null,
      token: null,
      newPassword: null,
      error: null
    }
  },
  actions: {
    load_cookie_if_needed() {
      const cookie_jar = getCurrentInstance().appContext.app.$cookies
      const workflow_status_raw = cookie_jar.get('workflow_status')
      if (workflow_status_raw) {
        const workflow_status = JSON.parse(workflow_status_raw)

        if (workflow_status['operation'] == 'user_registration') {
          this.email = workflow_status['email']
          if (workflow_status['this'] == 'success') {
            this.state = DIALOG.REGISTER_SUCCESS
          } else {
            this.state = DIALOG.GO_AWAY_HACKER
          }
        } else if (workflow_status['operation'] == 'password_reset') {
          this.email = workflow_status['email']
          this.token = workflow_status['token']
          this.state = DIALOG.RESET_PASSWORD_NEW_PASSWORD
        } else {
          console.log(`Got unexpected operation in workflow_status cookie: ${workflow_status_raw}`)
        }
        cookie_jar.remove('workflow_status')
      }
    }
  }
})

export { DIALOG, useDialogState }
