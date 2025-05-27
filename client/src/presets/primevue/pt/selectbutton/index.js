export default {
  root: ({ props }) => ({
    class: [
      'shadow-sm',
      { 'opacity-60 select-none pointer-events-none cursor-default': props.disabled }
    ]
  }),
  button: ({ context }) => ({
    class: [
      'relative',
      // Font
      'text-sm',
      'leading-none',

      // Flex Alignment
      'inline-flex items-center align-bottom text-center',

      // Spacing
      'px-2.5 py-1.5',

      // Shape
      'ring-1 ring-secondary-500 dark:ring-secondary-400',
      'first:rounded-l-md first:rounded-tr-none first:rounded-br-none',
      'last:rounded-tl-none last:rounded-bl-none last:rounded-r-md ',

      // Color
      {
        'bg-surface-0 dark:bg-surface-800': !context.active,
        'border-secondary-500 dark:border-secondary-400': !context.active,
        'text-secondary-500 dark:text-secondary-400': !context.active,
        'bg-secondary-500 dark:bg-secondary-400': context.active,
        'text-white dark:text-surface-900': context.active
      },

      // States
      'focus:outline-none focus:outline-offset-0 focus:ring-secondary-500 dark:focus:ring-secondary-400 focus:z-10',
      { 'opacity-60 select-none pointer-events-none cursor-default': context.disabled },

      // Transition
      'transition duration-200',

      // Misc
      'cursor-pointer select-none overflow-hidden'
    ]
  }),
  label: {
    class: 'font-semibold'
  }
}

// export default {
//     root: ({ props }) => ({
//         class: [
//           'inline-flex select-none align-bottom outline-transparent',
//           'border rounded-md [&>button]:rounded-none [&>button]:border-none',
//           '[&>button:first-child]:border-r-none [&>button:first-child]:rounded-r-none [&>button:first-child]:rounded-tl-md [&>button:first-child]:rounded-bl-md',
//           '[&>button:last-child]:border-l-none [&>button:first-child]:rounded-l-none [&>button:last-child]:rounded-tr-md [&>button:last-child]:rounded-br-md',
//           // Invalid State
//           {
//             'border-red-500 dark:border-red-400': props.invalid,
//             'border-transparent': !props.invalid
//           }
//         ]
//     })
// }
