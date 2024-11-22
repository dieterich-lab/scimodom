const COLORS: Readonly<string[]> = [
  '#00b052',
  '#02aeed',
  '#6ac886',
  '#7acff4',
  '#c0e7ca',
  '#e0f4fd',
  '#00b052',
  '#02aeed',
  '#6ac886',
  '#7acff4',
  '#c0e7ca',
  '#e0f4fd',
  '#00b052',
  '#02aeed',
  '#6ac886',
  '#7acff4',
  '#c0e7ca',
  '#e0f4fd',
  '#00b052',
  '#02aeed',
  '#6ac886',
  '#7acff4',
  '#c0e7ca',
  '#e0f4fd'
]

function toRgb(color: string): number[] {
  return [1, 3, 5].map((offset) => parseInt(color.slice(offset, offset + 2), 16))
}

function rgbToString(rgb: number[]): string {
  return (
    '#' +
    rgb
      .map((x) => x.toString(16))
      .map((s) => (s.length === 1 ? `0${s}` : s))
      .join('')
  )
}

class ColorFactory {
  private nextIndex: number

  constructor() {
    this.nextIndex = 0
  }

  public getTextColor(depth: number): string {
    return depth === 0 ? 'black' : 'white'
  }

  public getColor(depth: number, parentColor: string): string {
    let result: string
    switch (depth) {
      case 0:
        result = '#F4F1F5FF'
        break
      case 1:
        result = COLORS[this.nextIndex]
        this.nextIndex = (this.nextIndex + 1) % COLORS.length
        break
      default:
        result = this.lightenColor(parentColor, depth)
    }
    return result
  }

  lightenColor(parentColor: string, depth: number): string {
    const parentRgb = toRgb(parentColor)
    const displacement = Math.round(12.75 * depth)
    const rgb = parentRgb.map((x) => Math.max(0, x - displacement))
    return rgbToString(rgb)
  }
}

export { COLORS, toRgb, rgbToString, ColorFactory }
