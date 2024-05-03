class AbstractStyle {
  baseColor() {
    return 'primary'
  }
  labelClasses() {
    const baseColor = this.baseColor()
    return `text-${baseColor}-500 font-semibold`
  }
  inputTextGroupClasses() {
    const baseColor = this.baseColor()
    return `bg-${baseColor}-50/25 dark:bg-surface-900/20`
  }
  inputTextDefaultClasses() {
    const baseColor = this.baseColor()
    return (
      this.inputTextGroupClasses() +
      ` ring-${baseColor}-500/20 dark:ring-${baseColor}-500/20 focus:ring-${baseColor}-800`
    )
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
    const baseColor = this.baseColor()
    return `
            border-radius: 12px;
            background-image: radial-gradient(
                circle at center,
                rgb(var(--${baseColor}-600)),
                rgb(var(--${baseColor}-500)),
                rgb(var(--${baseColor}-400))
            );
`
  }
  buttonClasses() {
    const baseColor = this.baseColor()
    return `p-4 w-full text-${baseColor}-50 border border-${baseColor}-300 ring-${baseColor}-800`
  }
  severity() {
    return null
  }
}

export default AbstractStyle
