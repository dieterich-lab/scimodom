import { useForm } from 'vee-validate'

function createFormManager(validationSchema) {
  const { defineField, handleSubmit, resetForm, errors } = useForm({
    validationSchema: validationSchema
  })
  return {
    defineField: defineField,
    handleSubmit: handleSubmit,
    resetForm: resetForm,
    errors: errors
  }
}

export { createFormManager }
