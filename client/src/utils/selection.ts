import { toTree, toCascade, nestedSort, toIds } from '@/utils/index.js'

// selection utilities for Search

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
  const tree = toTree(opts, ['meth', 'tech'], 'technology_id')
  nestedSort(tree, ['children'])
  return tree
}
