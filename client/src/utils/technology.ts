interface TechnologySelectionExtraProps {
  modificationIds?: number[]
  organismId?: number
  placeholder?: string
  disabled?: boolean
}

const TECHNOLOGY_SELECTION_DEFAULTS = {
  placeholder: 'Select technology',
  disabled: false
}

export { type TechnologySelectionExtraProps, TECHNOLOGY_SELECTION_DEFAULTS }
