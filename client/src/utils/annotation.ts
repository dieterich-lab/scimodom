import { type Annotation } from '@/services/annotation'

/**
 * Describe the assemblies the data is in the coordinate system of,
 * e.g. "GRCh38 (Homo sapiens) and GRCm39 (Mus musculus)".
 */
function formatAssemblies(annotations: readonly Annotation[]): string {
  return formatList(unique(annotations.map((x) => `${x.assembly_name} (${x.taxa_name})`)))
}

/**
 * Describe what the data was annotated with, e.g. "Ensembl release
 * 110". More than one source, or an organism held at another
 * release, gives more than one entry.
 */
function formatReleases(annotations: readonly Annotation[]): string {
  return formatList(unique(annotations.map((x) => `${sourceLabel(x.source)} release ${x.release}`)))
}

// how a source is written, for the sources we know of. A source we
// do not know of is capitalised rather than left out: the label is
// cosmetic, nothing else here is per-source
const SOURCE_LABELS: Record<string, string> = {
  ensembl: 'Ensembl',
  gtrnadb: 'GtRNAdb'
}

function sourceLabel(source: string): string {
  return SOURCE_LABELS[source] ?? capitalise(source)
}

/** "a", "a and b", "a, b and c" */
function formatList(values: readonly string[]): string {
  if (values.length < 2) {
    return values.join('')
  }
  return `${values.slice(0, -1).join(', ')} and ${values[values.length - 1]}`
}

function unique(values: string[]): string[] {
  return [...new Set(values)].sort()
}

function capitalise(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1)
}

export { formatAssemblies, formatReleases }
