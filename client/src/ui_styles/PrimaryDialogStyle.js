import AbstractStyle from '@/ui_styles/AbstractStyle.js'

class PrimaryDialogStyle extends AbstractStyle {
  labelClasses() {
    const baseColor = this.baseColor()
    return `text-${baseColor}-50 font-semibold`
  }
}

const style = new PrimaryDialogStyle()

export default style
