// Private - only exported for testing
import type { DataTableSortMeta } from 'primevue/datatable'

interface CascadeItem<T> {
  label: string
  cChildren: (T | CascadeItem<T>)[]
}

// Unfortunately primvue does not export there TreeNode.
// So we have to define a subset of it.
interface TreeNode {
  label: string
  key: string
  children?: TreeNode[]
}

function getOptionsForPrimvueCascadeSelect<T, K extends keyof T>(
  data: T[],
  keys: K[]
): CascadeItem<T>[] {
  const root: CascadeItem<T> = { label: 'root', cChildren: [] }
  for (const item of data) {
    addItemToCascadeOptions(root, item, keys)
  }
  sortCascadeOptions(root, keys)
  return root.cChildren as CascadeItem<T>[]
}

function addItemToCascadeOptions<T, K extends keyof T>(parent: CascadeItem<T>, item: T, keys: K[]) {
  for (const k of keys.slice(0, -1)) {
    const label = `${item[k]}`
    const matchingNodes = parent.cChildren.filter((x) => (x as CascadeItem<T>).label === label)
    if (matchingNodes.length > 0) {
      parent = matchingNodes[0] as CascadeItem<T>
    } else {
      const newNode: CascadeItem<T> = { label: label, cChildren: [] as CascadeItem<T>[] }
      parent.cChildren.push(newNode)
      parent = newNode
    }
  }
  parent.cChildren.push(item)
}

function sortCascadeOptions<T, K extends keyof T>(parent: CascadeItem<T>, keys: K[]) {
  if (keys.length === 1) {
    const label = keys[0]
    ;(parent.cChildren as T[]).sort((a, b) => `${a[label]}`.localeCompare(`${b[label]}`))
  } else {
    ;(parent.cChildren as CascadeItem<T>[]).sort((a, b) => `${a.label}`.localeCompare(`${b.label}`))
    for (const c of parent.cChildren as CascadeItem<T>[]) {
      sortCascadeOptions(c, keys.slice(1))
    }
  }
}

function getOptionsForPrimvueTreeSelect<T, K extends keyof T>(
  data: T[],
  keys: [K, ...K[]],
  idKey: K
): TreeNode[] {
  const nodes: TreeNode[] = []
  for (const item of data) {
    addItemToTreeNodes(nodes, item, keys, idKey)
  }
  return sortTreeNodes(nodes)
}

function addItemToTreeNodes<T, K extends keyof T>(
  nodes: TreeNode[],
  item: T,
  keys: [K, ...K[]],
  idKey: K
) {
  let presentNodes = nodes
  let keyPrefix = ''
  for (const key of keys.slice(0, -1)) {
    const label = `${item[key]}`
    const keyString = `${keyPrefix}${label}`
    const foundNodes = presentNodes.filter((x) => x.key === keyString)
    let nodeToChange: TreeNode
    if (foundNodes.length > 0) {
      nodeToChange = foundNodes[0]
    } else {
      nodeToChange = { key: keyString, label: label }
      presentNodes.push(nodeToChange)
    }
    if (!nodeToChange.children) {
      nodeToChange.children = []
    }
    presentNodes = nodeToChange.children
    keyPrefix = `${keyString}/`
  }
  const lastLabelKey = keys[keys.length - 1]
  presentNodes.push({
    key: `${item[idKey]}`,
    label: `${item[lastLabelKey]}`
  })
}

function sortTreeNodes(nodes: TreeNode[]): TreeNode[] {
  for (const node of nodes) {
    if (node.children) {
      sortTreeNodes(node.children)
    }
  }
  return nodes.sort((a, b) => {
    const aLabel = a.label ? a.label : ''
    const bLabel = b.label ? b.label : ''
    return aLabel.localeCompare(bLabel)
  })
}

function formatPrimvueSortMetas(sortMetas?: DataTableSortMeta[]): string[] {
  const results: string[] = []
  if (sortMetas) {
    sortMetas.forEach((x) => {
      if (x.field === undefined) {
        return
      }
      if (typeof x.field === 'function') {
        throw new Error('Not implemented! Please fix me!')
      }
      switch (x.order) {
        case 1:
          results.push(`${x.field}%2Basc`)
          break
        case -1:
          results.push(`${x.field}%2Bdesc`)
          break
        default:
          results.push(x.field)
      }
    })
  }
  return results
}

export {
  type CascadeItem,
  type TreeNode,
  getOptionsForPrimvueCascadeSelect,
  getOptionsForPrimvueTreeSelect,
  formatPrimvueSortMetas
}
