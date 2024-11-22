import { defineStore } from 'pinia'
import { VueCookieNext } from 'vue-cookie-next'

enum DIALOG {
  NONE = 'NONE',
  LOGIN = 'LOGIN',
  ALERT = 'ALERT',
  ERROR_ALERT = 'ERROR_ALERT',
  REGISTER_ENTER_DATA = 'REGISTER_ENTER_DATA',
  RESET_PASSWORD_REQUEST = 'RESET_PASSWORD_REQUEST',
  CHANGE_PASSWORD = 'CHANGE_PASSWORD',
  CONFIRM = 'CONFIRM'
}

interface DialogState {
  state: DIALOG
  email: string | null
  token: string | null
  newPassword: string | null
  message: string | null
  confirmCallback: (() => void) | null
}

const useDialogState = defineStore('dialogState', {
  state: (): DialogState => {
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
      const workflow_status = VueCookieNext.getCookie('workflow_status')
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
          this.state = DIALOG.CHANGE_PASSWORD
        } else {
          console.log(`Got unexpected operation in workflow_status cookie: ${workflow_status}`)
        }
        VueCookieNext.removeCookie('workflow_status')
      }
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

type DialogStateStore = ReturnType<typeof useDialogState>

export { DIALOG, useDialogState, type DialogStateStore }
