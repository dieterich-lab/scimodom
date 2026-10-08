// The API sends frequency (at most two decimals) as a JSON number
// Display and export it with a fixed number of decimals, as the database stores it
function formatFrequency(frequency: number): string {
  return frequency.toFixed(2)
}

export { formatFrequency }
