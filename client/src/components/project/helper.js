function convertToProjectTemplate(projectForm) {
  return {
    title: projectForm.title,
    summary: projectForm.summary,
    contact_name: `${projectForm.surname}, ${projectForm.forename}`,
    contact_institution: projectForm.contact_institution,
    contact_email: projectForm.contact_email,
    date_published: projectForm.date_published,
    external_sources: convertExternalSources(projectForm),
    metadata: convertMetaData(projectForm)
  }
}

function convertExternalSources(projectForm) {
  if (!('external_sources' in projectForm)) {
    return []
  }
  return projectForm.external_sources
    .filter((x) => x.doi || x.pmid)
    .map((x) => {
      return {
        doi: x.doi || null,
        pmid: x.pmid || null
      }
    })
}

function convertMetaData(projectForm) {
  return projectForm.metadata.map((x) => {
    return {
      rna: x.rna,
      modomics_id: x.modomics_id,
      tech: x.tech,
      method_id: x.method_id,
      note: x.note,
      organism: {
        taxa_id: x.taxa_id,
        cto: x.cto,
        assembly_name: x.assembly_name,
        assembly_id: x.assembly_id
      }
    }
  })
}

export { convertToProjectTemplate }
