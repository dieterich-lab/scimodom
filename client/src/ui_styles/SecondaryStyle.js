import AbstractStyle from '@/ui_styles/AbstractStyle.js'

class SecondaryStyle extends AbstractStyle {
  inputTextGroupClasses() {
    return 'bg-primary-50/25 dark:bg-surface-900/20'
  }
  backgroundStyle() {
    return `
            border-radius: 12px;
            background-image: radial-gradient(
                circle at center,
                rgb(var(--secondary-600)),
                rgb(var(--secondary-500)),
                rgb(var(--secondary-400))
            );
`
  }
  buttonClasses() {
    return (
      'p-4 w-full text-secondary-50 border border-secondary-300 ring-secondary-800 ' +
      'bg-secondary-600 hover:bg-secondary-800 hover:ring-secondary-800 focus:ring-secondary-800'
    )
  }
}

const style = new SecondaryStyle()

export default style
