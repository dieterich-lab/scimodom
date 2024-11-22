interface UiStyle {
  baseColor: string
  labelClasses: string
  inputTextGroupClasses: string
  inputTextDefaultClasses: string
  errorTextClasses: string
  errorIconClasses: string
  errorClasses: string
  backgroundStyle: string
  buttonClasses: string
  textClasses: string
  severity?: string
}

const DEFAULT_STYLE: UiStyle = {
  baseColor: 'primary',
  labelClasses: 'text-primary-500 font-semibold',
  inputTextGroupClasses: 'bg-primary-50/25 dark:bg-surface-900/20',
  inputTextDefaultClasses:
    'bg-primary-50/25 dark:bg-surface-900/20 ring-primary-500/20 dark:ring-primary-500/20 focus:ring-primary-500 dark:focus:ring-primary-500',
  errorTextClasses: 'text-red-700',
  errorIconClasses: 'pi pi-times-circle place-self-center text-red-700',
  errorClasses: '!ring-red-700',
  backgroundStyle: `
    border-radius: 12px;
    background-image: radial-gradient(
        circle at center,
        rgb(var(--primary-600)),
        rgb(var(--primary-500)),
        rgb(var(--primary-400))
  )`,
  buttonClasses: 'p-4 w-full text-primary-50 border border-primary-300 ring-primary-500',
  textClasses: 'text-gray-700 dark:text-gray-300'
}

const PRIMARY_DIALOG_STYLE: UiStyle = {
  ...DEFAULT_STYLE,
  labelClasses: 'text-primary-50 font-semibold',
  errorTextClasses: 'text-white font-bold'
}

const SECONDARY_STYLE: UiStyle = {
  ...DEFAULT_STYLE,
  baseColor: 'secondary',
  labelClasses: 'text-secondary-50 font-semibold',
  inputTextGroupClasses: 'bg-secondary-50/25 dark:bg-surface-900/20',
  inputTextDefaultClasses:
    'bg-secondary-50/25 dark:bg-surface-900/20 ring-secondary-500/20 dark:ring-secondary-500/20 focus:ring-secondary-500 dark:focus:ring-secondary-500',
  errorTextClasses: 'text-white font-bold',
  backgroundStyle: `
    border-radius: 12px;
    background-image: radial-gradient(
        circle at center,
        rgb(var(--secondary-600)),
        rgb(var(--secondary-500)),
        rgb(var(--secondary-400))
  )`,
  buttonClasses: 'p-4 w-full text-secondary-50 border border-secondary-300 ring-secondary-500',
  severity: 'secondary'
}

const ERROR_ALERT_STYLE: UiStyle = {
  ...DEFAULT_STYLE,
  baseColor: 'error',
  labelClasses: 'text-red-700 font-semibold',
  inputTextGroupClasses: 'bg-surface-50/25 dark:bg-surface-900/20',
  inputTextDefaultClasses:
    'bg-surface-50/25 dark:bg-surface-900/20 ring-surface-500/20 dark:ring-surface-500/20 focus:ring-surface-500 dark:focus:ring-surface-500',
  errorTextClasses: 'text-red-700 font-bold',
  backgroundStyle: `
    border-radius: 12px;
    background-image: radial-gradient(
        circle at center,
        rgb(var(--surface-200)),
        rgb(var(--surface-100)),
        rgb(var(--surface-50))
  )`,
  buttonClasses: 'p-4 w-full',
  textClasses: 'text-red-700 dark:text-red-300',
  severity: 'danger'
}

interface FormFieldProps {
  uiStyle?: UiStyle
  error?: string
}

const FORM_FIELD_DEFAULTS = {
  uiStyle: () => DEFAULT_STYLE
}

interface GenericFieldProps {
  id?: string
  markAsError?: boolean
  uiStyle?: UiStyle
}

const GENERIC_FIELD_DEFAULTS = {
  markAsError: false,
  uiStyle: () => DEFAULT_STYLE
}

interface FormFieldWrapperProps extends FormFieldProps {
  fieldId: string
}

export {
  type UiStyle,
  type FormFieldProps,
  type FormFieldWrapperProps,
  type GenericFieldProps,
  DEFAULT_STYLE,
  PRIMARY_DIALOG_STYLE,
  SECONDARY_STYLE,
  ERROR_ALERT_STYLE,
  FORM_FIELD_DEFAULTS,
  GENERIC_FIELD_DEFAULTS
}
