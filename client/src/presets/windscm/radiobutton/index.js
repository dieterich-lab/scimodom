export default {
  root: {
    class: [
      'relative',

      // Flexbox & Alignment
      'inline-flex',
      'align-bottom',

      // Size
      'w-4 h-4',

      // Misc
      'cursor-default',
      'select-none'
    ]
  },
  box: ({ props }) => ({
    class: [
      // Flexbox
      'flex justify-center items-center',

      // Size
      'w-4 h-4',
      'text-sm',
      'font-medium',

      // Shape
      'border-2',
      'rounded-full',

      // Transition
      'transition duration-200 ease-in-out',

      // Colors
      {
        'text-surface-700 dark:text-white/80':
          props.value !== props.modelValue && props.value !== undefined,
        // 'bg-surface-0 dark:bg-surface-900':
        //   props.value !== props.modelValue && props.value !== undefined,
        'border-surface-300 dark:border-surface-700':
          props.value !== props.modelValue && props.value !== undefined,
        'bg-primary-500 border-primary-500 dark:bg-primary-400 dark:border-primary-400':
          props.value == props.modelValue && props.value !== undefined
      },
      // States
      {
        'peer-hover:border-surface-400 dark:peer-hover:border-surface-400':
          !props.disabled && !props.invalid && props.value !== props.modelValue,
        'peer-hover:border-primary-hover':
          !props.disabled && props.value == props.modelValue && props.value !== void 0,
        'peer-hover:[&>*:first-child]:bg-primary-600 dark:peer-hover:[&>*:first-child]:bg-primary-300':
          !props.disabled && props.value == props.modelValue && props.value !== void 0,
        'peer-focus-visible:ring-1 peer-focus-visible:ring-primary-500 dark:peer-focus-visible:ring-primary-400':
          !props.disabled,
        'bg-surface-200 [&>*:first-child]:bg-surface-600 dark:bg-surface-700 dark:[&>*:first-child]:bg-surface-400 border-surface-300 dark:border-surface-700 select-none pointer-events-none cursor-default':
          props.disabled
      }
      // {
      //   'outline-none outline-offset-0': !props.disabled,
      //   'peer-focus-visible:ring-2 peer-focus-visible:ring-offset-2 peer-focus-visible:ring-offset-surface-0 dark:focus-visible:ring-offset-surface-800 peer-focus-visible:ring-primary-500 dark:peer-focus-visible:ring-primary-400':
      //     !props.disabled,
      //   'opacity-60 cursor-default': props.disabled
      // }
    ]
  }),
  input: {
    class: [
      'peer',

      // Size
      'w-full ',
      'h-full',

      // Position
      'absolute',
      'top-0 left-0',
      'z-10',

      // Spacing
      'p-0',
      'm-0',

      // Shape
      'opacity-0',
      'rounded-md',
      'outline-none',
      'border-2 border-surface-300 dark:border-surface-700',

      // Misc
      'appareance-none',
      'cursor-default'
    ]
  },
  icon: {
    class: 'hidden'
  }
}
