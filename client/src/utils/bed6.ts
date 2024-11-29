type Strand = '+' | '-' | '.'

interface Bed6Record {
  chrom: string
  start: number
  end: number
  name: string
  score: number
  strand: Strand
}

interface EufRecord extends Bed6Record {
  coverage: number
  frequency: number
  eufid: string
}

export { type Strand, type Bed6Record, type EufRecord }
