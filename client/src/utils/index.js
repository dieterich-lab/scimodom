export function toTree(data, keys, id) {
  var len = keys.length - 1
  var tree = data.reduce((r, o) => {
    keys.reduce((t, k, idx) => {
      var jdx = idx === len ? id : k
      var tmp = (t.children = t.children || []).find((p) => p.key === o[jdx])
      if (!tmp) {
        t.children.push((tmp = { key: o[jdx], label: o[k] }))
      }
      return tmp
    }, r)
    return r
  }, {}).children
  return tree
}

export function toIds(array, defaultArray) {
  if (!(array === undefined || Object.keys(array).length === 0)) {
    return Object.keys(array)
      .map(Number)
      .filter((value) => !Number.isNaN(value))
  }
  return defaultArray
}

function setOrder(o) {
  if (!Number.isInteger(o)) {
    return o
  }
  return o === 1 ? 'asc' : 'desc'
}

export function fmtOrder(array) {
  if (!(array === undefined)) {
    return array.map((d) =>
      Object.entries(d)
        .map(([k, v]) => setOrder(v))
        .join('.')
    )
  }
  return []
}
