export default {
  root: {
    class: [
      'relative overflow-auto will-change-scroll outline-none',
      'object-contain'
      // 'contain: strict',
      // 'transform: translateZ(0)',
    ]
  },
  content: { class: ['absolute min-h-full min-w-full will-change-transform left-0 top-0'] },
  spacer: { class: ['absolute h-px w-px origin-[0_0] pointer-events-none left-0 top-0'] },
  loader: { class: ['sticky w-full h-full left-0 top-0', 'flex items-center justify-center'] },
  loadingIcon: {
    class: [
      'text-[2rem]'
      // 'w-8 h-8'
    ]
  }
}
