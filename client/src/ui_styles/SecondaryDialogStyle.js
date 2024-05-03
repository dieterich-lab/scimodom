import AbstractStyle from '@/ui_styles/AbstractStyle.js'

class SecondaryStyle extends AbstractStyle {
  labelClasses() {
    const baseColor = this.baseColor()
    return `text-${baseColor}-50 font-semibold`
  }
  baseColor() {
    return 'secondary'
  }
  severity() {
    return 'secondary'
  }
}

const style = new SecondaryStyle()

export default style
