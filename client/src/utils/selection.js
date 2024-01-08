import { toTree, toIds } from '@/utils/index.js'

// selection utilities for Search and Compare Views

// Search View
export const updModification = (selection) => {
  // update modification
  return toTree(selection, ['rna', 'modomics_sname'], 'modification_id')
}

export const updTechnologyFromMod = (selection, slctMod) => {
  // update technology from modification
  var idsMod = toIds(slctMod, [])
  var opts = selection.filter((item) => idsMod.includes(item.modification_id))
  return toTree(opts, ['cls', 'meth', 'tech'], 'technology_id')
}

export const updOrganismFromModAndTech = (selection, slctMod, slctTech) => {
  // update organism from modification and technology
  var idsMod = toIds(slctMod, [])
  var idsTech = toIds(slctTech, [])
  var opts = selection.filter(
    (item) => idsMod.includes(item.modification_id) && idsTech.includes(item.technology_id)
  )
  return toTree(opts, ['domain', 'kingdom', 'phylum', 'taxa_sname', 'cto'], 'organism_id')
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
