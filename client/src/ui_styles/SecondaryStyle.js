import AbstractStyle from '@/ui_styles/AbstractStyle.js'

class SecondaryStyle extends AbstractStyle {
  baseColor() {
    return 'secondary'
  }
}

const style = new SecondaryStyle()

export default style
