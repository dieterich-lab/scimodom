import { defineStore } from 'pinia'
import { VueCookieNext } from 'vue-cookie-next'
import { string } from 'yup'

enum DIALOG {
  NONE = 'NONE',
  LOGIN = 'LOGIN',
  ALERT = 'ALERT',
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

interface AxiosErrorResponse {
  response: {
    data: {
      result: string
    }
  }
}

interface HTTPError {
  status: number
}

function isHTTPError(x: unknown): x is HTTPError {
  return x !== null && typeof x === 'object' && 'status' in x
}

function isAxiosErrorResponse(x: any): x is AxiosErrorResponse {
  return (
    typeof x === 'object' &&
    'response' in x &&
    typeof x.response === 'object' &&
    'data' in x.response &&
    typeof x.response.data === 'object' &&
    'result' in x.response.data &&
    x.response.data.result instanceof string
  )
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
    handle_error(
      axios_error: unknown,
      context: string,
      new_state_template: object,
      messages_by_http_status?: Map<number, string>
    ) {
      let error_message: string
      if (
        messages_by_http_status &&
        isHTTPError(axios_error) &&
        messages_by_http_status.has(axios_error.status)
      ) {
        error_message = messages_by_http_status.get(axios_error.status) || ''
      } else if (isAxiosErrorResponse(axios_error)) {
        error_message = axios_error.response.data.result
      } else {
        error_message = `${axios_error}`
      }
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

type DialogStateStore = ReturnType<typeof useDialogState>

export { DIALOG, useDialogState, type DialogStateStore }
