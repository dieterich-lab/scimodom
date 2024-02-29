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

export function toCascade(tree) {
  // replace children with child1 and child2
  // tree depth = 2
  return tree.map((item) => {
    let child1 = JSON.parse(JSON.stringify(item.children).replaceAll('children', 'child2'))
    return { key: item.key, label: item.label, child1: child1 }
  })
}

export function nestedSort(array, keys) {
  // sort max. 2 levels on "label"
  array.forEach((obj) => {
    if (keys.length == 2) {
      obj[keys[0]].forEach((nestedObj) => {
        nestedObj[keys[1]].sort((a, b) => a.label.localeCompare(b.label))
      })
    }
    obj[keys[0]].sort((a, b) => a.label.localeCompare(b.label))
  })
  array.sort((a, b) => a.label.localeCompare(b.label))
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
        .join('%2B')
    )
  }
  return []
}

export function fmtFilter(object) {
  return Object.entries(object)
    .map(([k, v]) => {
      if (!(Object.is(v.value, null) || v.value.length === 0)) {
        return [k, v.value, v.matchMode].join('%2B')
      }
    })
    .filter((item) => item)
}
