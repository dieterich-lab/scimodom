import { toTree, toCascade, nestedSort, toIds } from '@/utils/index.js'

// selection utilities for Search

export const updModification = (selection) => {
  // update modification
  // grouped Dropdown works with one child tree
  let tree = toTree(selection, ['rna_name', 'modomics_sname'], 'modification_id')
  nestedSort(tree, ['children'])
  return tree
}

export const updOrganismFromMod = (selection, slctMod) => {
  // update organism from modification
  let opts = selection.map((item) => {
    const kingdom = Object.is(item.kingdom, null) ? item.domain : item.kingdom
    return { ...item, kingdom }
  })
  // if array of modification ids
  if (Array.isArray(slctMod)) {
    opts = selection.filter((item) => slctMod.includes(item.modification_id))
  } else {
    // single object
    opts = selection.filter((item) => item.modification_id == slctMod.key)
  }
  let tree = toTree(opts, ['kingdom', 'taxa_sname', 'cto'], 'organism_id')
  tree = toCascade(tree)
  nestedSort(tree, ['child1', 'child2'])
  return tree
}

export const updTechnologyFromModAndOrg = (selection, slctMod, slctOrg) => {
  // update technology from modification and organism
  let opts = selection
  // if array of modification ids
  if (Array.isArray(slctMod)) {
    opts = selection.filter(
      (item) => slctMod.includes(item.modification_id) && item.organism_id == slctOrg.key
    )
  } else {
    // single object
    opts = selection.filter(
      (item) => item.modification_id == slctMod.key && item.organism_id == slctOrg.key
    )
  }
  let tree = toTree(opts, ['meth', 'tech'], 'technology_id')
  nestedSort(tree, ['children'])
  return tree
}

export const updSelectionFromAll = (all_selections, slctMod, slctOrg, slctTech) => {
  let idsTech = toIds(slctTech, [])
  let opts = all_selections.filter(
    (item) =>
      item.modification_id == slctMod.key &&
      item.organism_id == slctOrg.key &&
      idsTech.includes(item.technology_id)
  )
  let selection_id = opts.map((item) => item.selection_id)
  let taxaId = [...new Set(opts.map((item) => item.taxa_id))]
  let taxaName = [...new Set(opts.map((item) => item.taxa_name))]
  // there should be only one, but we don't check...
  let rna = [...new Set(opts.map((item) => item.rna))]
  return {
    selection: selection_id,
    technology: idsTech,
    taxaId: taxaId[0],
    taxaName: taxaName[0],
    rna: rna[0]
  }
}
