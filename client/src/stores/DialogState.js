import { getCurrentInstance, reactive } from 'vue'
import { defineStore } from 'pinia'

const DIALOG = Object.freeze({
  NONE: Symbol('NONE'),
  LOGIN: Symbol('LOGIN'),
  ALERT: Symbol('ALERT'),
  REGISTER_ENTER_DATA: Symbol('REGISTER_ENTER_DATA'),
  RESET_PASSWORD_REQUEST: Symbol('RESET_PASSWORD_REQUEST'),
  CHANGE_PASSWORD: Symbol('CHANGE_PASSWORD'),
  CONFIRM: Symbol('CONFIRM')
})

const useDialogState = defineStore('dialogState', {
  state: () => {
    return {
      state: DIALOG.NONE,
      email: null,
      token: null,
      newPassword: null,
      message: null,
      confirmCallback: null
    }
  },
  actions: {
    load_cookie_if_needed() {
      const cookie_jar = getCurrentInstance().appContext.app.$cookies
      const workflow_status = cookie_jar.get('workflow_status')
      if (workflow_status) {
        if (workflow_status['operation'] == 'user_registration') {
          this.email = workflow_status['email']
          if (workflow_status['result'] == 'success') {
            this.message = 'Your registration was successful - please login.'
            this.state = DIALOG.LOGIN
          } else {
            this.message = 'Something went wrong. Please check the link you tried to use.'
            this.state = DIALOG.ALERT
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
    },
    handle_error(axios_error, context, new_state_template) {
      let error_message = `${axios_error}`
      try {
        const result = axios_error.response.data.result
        if (result) {
          error_message = result
        }
      } catch (e) {}

      const full_message = `${context}: ${error_message}`
      console.log(full_message)
      const new_state = { ...new_state_template, message: full_message }
      this.$patch(new_state)
    },
    confirm() {
      if (this.confirmCallback !== null) {
        const func = this.confirmCallback
        this.confirmCallback = null
        this.state = DIALOG.NONE
        func()
      }
    }
  }
})

export { DIALOG, useDialogState }
