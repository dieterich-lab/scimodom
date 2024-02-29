import { toTree, toCascade, nestedSort, toIds } from '@/utils/index.js'

// selection utilities for Search and Compare Views

// Search View
export const updModification = (selection) => {
  // update modification
  // grouped Dropdown works with one child tree
  let tree = toTree(selection, ['rna', 'modomics_sname'], 'modification_id')
  nestedSort(tree, ['children'])
  return tree
}

export const updOrganismFromMod = (selection, slctMod) => {
  // update organism from modification
  let opts = selection.map((item) => {
    const kingdom = Object.is(item.kingdom, null) ? item.domain : item.kingdom
    return { ...item, kingdom }
  })
  opts = selection.filter((item) => item.modification_id == slctMod.key)
  let tree = toTree(opts, ['kingdom', 'taxa_sname', 'cto'], 'organism_id')
  tree = toCascade(tree)
  nestedSort(tree, ['child1', 'child2'])
  return tree
}

export const updTechnologyFromModAndOrg = (selection, slctMod, slctOrg) => {
  // update technology from modification and organism
  let opts = selection.filter(
    (item) => item.modification_id == slctMod.key && item.organism_id == slctOrg.key
  )
  let tree = toTree(opts, ['meth', 'tech'], 'technology_id')
  nestedSort(tree, ['children'])
  return tree
}

export const updSelectionFromAll = (selection, slctMod, slctOrg, slctTech) => {
  let idsTech = toIds(slctTech, [])
  let opts = selection.filter(
    (item) =>
      item.modification_id == slctMod.key &&
      item.organism_id == slctOrg.key &&
      idsTech.includes(item.technology_id)
  )
  let selection_id = opts.map((item) => item.selection_id)
  let taxid = [...new Set(opts.map((item) => item.taxa_id))]
  return { selection: selection_id, taxid: taxid }
}

// Compare View
export const updSpecies = (selection) => {
  // update species
  return toTree(selection, ['domain', 'taxa_sname'], 'taxa_sname')
}

export const updOrganismFromSpec = (selection, slctSpec) => {
  // update organism from selected species
  var opts = selection.filter((item) => item.taxa_sname === slctSpec)
  return toTree(opts, ['cto'], 'organism_id')
}

export const updModificationFromOrg = (selection, slctOrg) => {
  // update modification from selected organism
  var ids = slctOrg.map((item) => item.key)
  var opts = selection.filter((item) => ids.includes(item.organism_id))
  return toTree(opts, ['rna', 'modomics_sname'], 'modification_id')
}

export const updTechnologyFromOrgAndMod = (selection, slctOrg, slctMod) => {
  // update technology from selected organism and modification
  var idsOrg = slctOrg.map((item) => item.key)
  var idsMod = toIds(slctMod, Array.from(new Set(selection.map((item) => item.modification_id))))
  var opts = selection.filter(
    (item) => idsOrg.includes(item.organism_id) && idsMod.includes(item.modification_id)
  )
  return toTree(opts, ['cls', 'meth', 'tech'], 'technology_id')
}

export function updDataset(selection, organism, slctOrg, slctMod, slctTech, dataset, options = {}) {
  // update dataset selection from organism, modification, technology, and,
  // optionally, from pre-selected dataset
  const { isFilter = false, slctDS } = options
  var idsOrg =
    Object.is(slctOrg, undefined) || slctOrg.length === 0
      ? organism.map((item) => item.key)
      : slctOrg.map((item) => item.key)
  var idsMod = toIds(slctMod, Array.from(new Set(selection.map((item) => item.modification_id))))
  var idsTech = toIds(slctTech, Array.from(new Set(selection.map((item) => item.technology_id))))
  var opts = dataset.filter(
    (item) =>
      idsOrg.includes(item.organism_id) &&
      idsMod.includes(item.modification_id) &&
      idsTech.includes(item.technology_id)
  )
  if (isFilter) {
    var idsDS =
      Object.is(slctDS, undefined) || slctDS.length === 0
        ? dataset.map((item) => item.dataset_id)
        : slctDS
    opts = dataset.filter(
      (item) =>
        idsOrg.includes(item.organism_id) &&
        idsMod.includes(item.modification_id) &&
        idsTech.includes(item.technology_id) &&
        !idsDS.includes(item.dataset_id)
    )
  }
  return [...new Map(opts.map((item) => [item['dataset_id'], item])).values()].map((item) => {
    return {
      dataset_id: item.dataset_id,
      dataset_title: item.dataset_title,
      dataset_display: item.dataset_title + '    [' + item.dataset_id + ']'
    }
  })
}
