class AbstractStyle {
  messageTextClasses() {
    return 'text-white font-bold'
  }
  labelClasses() {
    return 'text-primary-50 font-semibold'
  }
  inputTextGroupClasses() {
    return 'bg-primary-50/25 dark:bg-surface-900/20'
  }
  inputTextDefaultClasses() {
    return this.inputTextGroupClasses() + ' ring-primary-500/20 dark:ring-primary-500/20'
  }
  errorTextClasses() {
    return 'text-red-700'
  }
  errorIconClasses() {
    return 'pi pi-times-circle place-self-center text-red-700'
  }
  errorClasses() {
    return '!ring-red-700'
  }
  backgroundStyle() {
    return `
            border-radius: 12px;
            background-image: radial-gradient(
                circle at center,
                rgb(var(--primary-600)),
                rgb(var(--primary-500)),
                rgb(var(--primary-400))
            );
`
  }
  buttonClasses() {
    return (
      'p-4 w-full text-primary-50 border border-secondary-alpha-30' +
      ' bg-primary-600 hover:bg-primary-800'
    )
  }
}

export default AbstractStyle
