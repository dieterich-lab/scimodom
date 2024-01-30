export default {
  root: ({ props, state }) => ({
    class: [
      // Display and Position
      'inline-flex',
      'relative',

      // Shape
      'rounded-md',
      'shadow',

      // Color and Background
      'bg-surface-0 dark:bg-surface-900',
      'border border-surface-300 dark:border-surface-700',

      // Transitions
      'transition-all',
      'duration-200',

      // States
      'hover:border-crmg/75 dark:hover:border-crmg/50',
      { 'outline-none outline-offset-0 ring ring-crmg/75 dark:ring-crmg/50': state.focused },

      // Misc
      'cursor-pointer',
      'select-none',
      {
        'opacity-60': props.disabled,
        'pointer-events-none': props.disabled,
        'cursor-default': props.disabled
      }
    ]
  }),
  labelContainer: {
    class: ['overflow-hidden flex flex-auto cursor-pointer']
  },
  label: {
    class: [
      'block leading-5',

      // Space
      'p-3',

      // Color
      'text-surface-800 dark:text-white/80',

      // Transition
      'transition duration-200',

      // Misc
      'overflow-hidden whitespace-nowrap cursor-pointer overflow-ellipsis'
    ]
  },
  trigger: {
    class: [
      // Flexbox
      'flex items-center justify-center',
      'shrink-0',

      // Color and Background
      'bg-transparent',
      'text-surface-500',

      // Size
      'w-12',

      // Shape
      'rounded-tr-md',
      'rounded-br-md'
    ]
  },
  panel: {
    class: [
      // Position
      'absolute top-0 left-0',

      // Shape
      'border-0 dark:border',
      'rounded-md',
      'shadow-md',

      // Color
      'bg-surface-0 dark:bg-surface-800',
      'text-surface-800 dark:text-white/80',
      'dark:border-surface-700'
    ]
  },
  wrapper: {
    class: [
      // Sizing
      'max-h-[200px]',

      // Misc
      'overflow-auto'
    ]
  },
  tree: {
    root: {
      class: [
        // Space
        'p-5'
      ]
    },
    wrapper: {
      class: ['overflow-auto']
    },
    container: {
      class: [
        // Spacing
        'm-0 p-0',

        // Misc
        'list-none overflow-auto'
      ]
    },
    node: {
      class: ['p-1', 'outline-none']
    },
    content: ({ context, props }) => ({
      class: [
        // Flex and Alignment
        'flex items-center',

        // Shape
        'rounded-md',

        // Spacing
        'p-2',

        // Colors
        'text-surface-600 dark:text-white/70',
        // context.checked
        { 'bg-crmg/25 dark:bg-crmg/25 text-crmg dark:text-surface-0': context.selected },

        // States
        {
          'hover:bg-surface-50 dark:hover:bg-surface-700/40':
            (props.selectionMode == 'single' || props.selectionMode == 'multiple') &&
            !context.selected
        },

        // Transition
        'transition-shadow duration-200',

        {
          'cursor-pointer select-none':
            props.selectionMode == 'single' || props.selectionMode == 'multiple'
        }
      ]
    }),
    toggler: ({ context }) => ({
      class: [
        // Flex and Alignment
        'inline-flex items-center justify-center',

        // Shape
        'border-0 rounded-full',

        // Size
        'w-8 h-8',

        // Spacing
        'mr-2',

        // Colors
        'bg-transparent',
        {
          'text-surface-500 hover:text-crmg/75 dark:text-white dark:hover:text-crmg/50':
            !context.selected,
          'text-crmg dark:text-white': context.selected,
          invisible: context.leaf
        },

        // States
        'hover:bg-surface-200/20 dark:hover:bg-surface-500/20',
        'focus:outline-none focus:outline-offset-0 focus:ring focus:ring-crmg/75 dark:focus:ring-crmg/50',

        // Transition
        'transition duration-200',

        // Misc
        'cursor-pointer select-none'
      ]
    }),
    nodeCheckbox: {
      root: {
        class: [
          'relative',

          // Alignment
          'inline-flex',
          'align-bottom',

          // Size
          'w-6',
          'h-6',

          // Spacing
          'mr-2',

          // Misc
          'cursor-pointer',
          'select-none'
        ]
      },
      box: ({ props, context }) => ({
        class: [
          // Alignment
          'flex',
          'items-center',
          'justify-center',

          // Size
          'w-6',
          'h-6',

          // Shape
          'rounded-md',
          'border-2',

          // Colors
          {
            'border-surface-200 bg-surface-0 dark:border-surface-700 dark:bg-surface-900':
              !context.checked,
            'border-crmg/75 bg-crmg/75 dark:border-crmg/50 dark:bg-crmg/50': context.checked
          },

          // States
          {
            'peer-hover:border-crmg/75 dark:peer-hover:border-crmg/50':
              !props.disabled && !context.checked,
            'peer-hover:bg-crmg dark:peer-hover:bg-crmg peer-hover:border-crmg dark:peer-hover:border-crmg':
              !props.disabled && context.checked,
            'peer-focus-visible:border-crmg/75 dark:peer-focus-visible:border-crmg/50 peer-focus-visible:ring-2 peer-focus-visible:ring-crmg/75 dark:peer-focus-visible:ring-crmg/50':
              !props.disabled,
            'cursor-default opacity-60': props.disabled
          },

          // Transitions
          'transition-colors',
          'duration-200'
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
      icon: {
        class: [
          // Font
          'text-base leading-none',

          // Size
          'w-4',
          'h-4',

          // Colors
          'text-white dark:text-surface-900',

          // Transitions
          'transition-all',
          'duration-200'
        ]
      }
    },
    nodeicon: {
      class: [
        // Space
        'mr-2',

        // Color
        'text-surface-600 dark:text-white/70'
      ]
    },
    subgroup: {
      class: ['m-0 list-none p-0 pl-2 mt-1']
    },
    filtercontainer: {
      class: [
        'relative block',

        // Space
        'mb-2',

        // Size
        'w-full'
      ]
    },
    input: {
      class: [
        'relative',
        // Font
        'font-sans leading-none',

        // Spacing
        'm-0',
        'p-3 pr-10',

        // Size
        'w-full',

        // Shape
        'rounded-md',

        // Colors
        'text-surface-600 dark:text-surface-200',
        'placeholder:text-surface-400 dark:placeholder:text-surface-500',
        'bg-surface-0 dark:bg-surface-900',
        'border border-surface-300 dark:border-surface-600',

        // States
        'hover:border-crmg/75 dark:hover:border-crmg/50',
        'focus:outline-none focus:outline-offset-0 focus:ring focus:ring-crmg/75 dark:focus:ring-crmg/50',

        // Transition & Misc
        'appearance-none',
        'transition-colors duration-200'
      ]
    },
    loadingicon: {
      class: [
        'text-surface-500 dark:text-surface-0/70',
        'absolute top-[50%] right-[50%] -mt-2 -mr-2 animate-spin'
      ]
    },
    searchicon: {
      class: [
        // Position
        'absolute top-1/2 -mt-2 right-3',

        // Color
        'text-surface-600 dark:hover:text-white/70'
      ]
    }
  },
  transition: {
    enterFromClass: 'opacity-0 scale-y-[0.8]',
    enterActiveClass:
      'transition-[transform,opacity] duration-[120ms] ease-[cubic-bezier(0,0,0.2,1)]',
    leaveActiveClass: 'transition-opacity duration-100 ease-linear',
    leaveToClass: 'opacity-0'
  }
}
