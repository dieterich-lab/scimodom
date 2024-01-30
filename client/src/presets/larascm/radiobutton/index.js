export default {
  root: {
    class: [
      'relative',

      // Flexbox & Alignment
      'inline-flex',
      'align-bottom',

      // Size
      'w-6 h-6',

      // Misc
      'cursor-pointer',
      'select-none'
    ]
  },
  box: ({ props }) => ({
    class: [
      // Flexbox
      'flex justify-center items-center',

      // Size
      'w-6 h-6',

      // Shape
      'border-2',
      'rounded-full',

      // Transition
      'transition duration-200 ease-in-out',

      // Colors
      {
        'text-surface-700 dark:text-white/80':
          props.value !== props.modelValue && props.value !== undefined,
        'bg-surface-0 dark:bg-surface-900':
          props.value !== props.modelValue && props.value !== undefined,
        'border-surface-300 dark:border-surface-700':
          props.value !== props.modelValue && props.value !== undefined,
        'border-crmg/75 dark:border-crmg/50':
          props.value == props.modelValue && props.value !== undefined,
        'bg-crmg/75 dark:bg-crmg/50': props.value == props.modelValue && props.value !== undefined
      },

      // States
      {
        'peer-hover:border-crmg/75 dark:peer-hover:border-crmg/50': !props.disabled,
        'peer-hover:border-crmg dark:peer-hover:border-crmg peer-hover:bg-crmg dark:peer-hover:bg-crmg':
          !props.disabled && props.value == props.modelValue && props.value !== undefined,
        'peer-focus-visible:border-crmg/75 dark:peer-focus-visible:border-crmg/50 peer-focus-visible:ring-2 peer-focus-visible:ring-crmg/75 dark:peer-focus-visible:ring-crmg/50':
          !props.disabled,
        'opacity-60 cursor-default': props.disabled
      }
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
      'border-2 border-surface-200 dark:border-surface-700',

      // Misc
      'appareance-none',
      'cursor-pointer'
    ]
  },
  icon: ({ props }) => ({
    class: [
      'block',

      // Shape
      'rounded-full',

      // Size
      'w-3 h-3',

      // Colors
      'bg-surface-0 dark:bg-surface-900',

      // Conditions
      {
        'backface-hidden scale-10 invisible': props.value !== props.modelValue,
        'transform visible scale-[1.1]': props.value == props.modelValue
      },

      // Transition
      'transition duration-200'
    ]
  })
}
