import { ref, readonly } from 'vue'
import { toTree, toIds } from '@/utils/index.js'

export function useSelection(options) {
  const organism = ref()
  const modification = ref()
  const technology = ref()

  const updateOrganism = (slctSpec) => {
    // update organism from selected species
    var opts = options.filter((item) => item.taxa_sname === slctSpec)
    organism.value = toTree(opts, ['cto'], 'organism_id')
  }

  const updateModification = (slctOrg) => {
    // update modification from selected organism
    var ids = slctOrg.map((item) => item.key)
    var opts = options.filter((item) => ids.includes(item.organism_id))
    modification.value = toTree(opts, ['rna', 'modomics_sname'], 'modification_id')
  }

  const updateTechnology = (slctOrg, slctMod) => {
    // update technology from selected organism and modification
    var idsOrg = slctOrg.map((item) => item.key)
    var idsMod = toIds(slctMod, Array.from(new Set(options.map((item) => item.modification_id))))
    var opts = options.filter(
      (item) => idsOrg.includes(item.organism_id) && idsMod.includes(item.modification_id)
    )
    technology.value = toTree(opts, ['cls', 'meth', 'tech'], 'technology_id')
  }

  return {
    organism: readonly(organism),
    modification: readonly(modification),
    technology: readonly(technology),
    // organism: organism,
    // modification: modification,
    updateOrganism,
    updateModification,
    updateTechnology
  }
}
