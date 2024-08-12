<script>
import Plotly from 'plotly.js-dist'
import { HTTP } from '@/services/API.js'

export default {
  name: 'SunburstChart',
  props: ['chart'],
  setup(props) {
    const chart = props.chart
  },
  data() {
    return {
      data: null
    }
  },
  mounted() {
    this.fetchData()
  },
  methods: {
    async fetchData() {
      try {
        const response = await HTTP.get(`/sunburst/${this.chart}`)
        const data = await response.data
        this.calculateCumulativeSize(data[0])
        this.data = this.processData(data[0]) // Assuming data is an array and you need the first element
        this.createChart()
      } catch (error) {
        console.error('Error fetching data:', error)
      }
    },
    calculateCumulativeSize(node) {
      if (!node.children) {
        return node.size || 0
      }
      let totalSize = 0
      for (let child of node.children) {
        totalSize += this.calculateCumulativeSize(child)
      }
      node.cumulativeSize = totalSize
      return totalSize
    },
    getColors() {
      return [
        '#00b052',
        '#02aeed',
        '#6ac886',
        '#7acff4',
        '#c0e7ca',
        '#e0f4fd',
        '#00b052',
        '#02aeed',
        '#6ac886',
        '#7acff4',
        '#c0e7ca',
        '#e0f4fd',
        '#00b052',
        '#02aeed',
        '#6ac886',
        '#7acff4',
        '#c0e7ca',
        '#e0f4fd',
        '#00b052',
        '#02aeed',
        '#6ac886',
        '#7acff4',
        '#c0e7ca',
        '#e0f4fd'
      ]
    },
    // Function to lighten a color by a certain percentage.
    // This is used to create variations in color for child nodes.
    lightenColor(color, depth) {
      // Convert the hex color to an integer.
      const num = parseInt(color.slice(1), 16)

      // Adjust the amount based on the depth. The deeper the node, the less lightening is applied.
      const amt = Math.round(2.55 * (depth * 5)) // Adjust the multiplier for finer control.

      // Extract the red, green, and blue components and apply the adjustment.
      const R = (num >> 16) - amt
      const G = ((num >> 8) & 0x00ff) - amt
      const B = (num & 0x0000ff) - amt

      // Reassemble the color, ensuring each component is within valid range.
      return `#${(0x1000000 + (R > 0 ? R : 0) * 0x10000 + (G > 0 ? G : 0) * 0x100 + (B > 0 ? B : 0))
        .toString(16)
        .slice(1)}`
    },
    processData(data) {
      const ids = []
      const labels = []
      const parents = []
      const values = []
      const colors = []
      const textColors = [] // Array to hold the text colors for labels.
      const customdata = []

      const colorPalette = this.getColors()
      // Object to store the base color for each first-level node.
      const baseColors = {}
      function traverse(node, parent, depth, parentColor) {
        const id = parent ? `${parent}-${node.name}` : node.name
        ids.push(id)
        labels.push(node.name)
        parents.push(parent)
        values.push(node.size || 0)

        let color
        let textColor = 'white' // Default text color is white.

        if (depth === 0) {
          color = '#F4F1F5FF'
          textColor = 'black' // Keep root level label in black.
        } else if (depth === 1) {
          // Check if the node is a first-level node.
          // Assign a color from the palette to first-level nodes.
          color = colorPalette[ids.length % colorPalette.length]
          baseColors[node.name] = color // Store the base color for later use.
        } else {
          // For subsequent levels, lighten the parent's color.
          color = this.lightenColor(parentColor, depth) // Adjust lightness by depth level.
        }

        colors.push(color) // Add the calculated color to the colors array.
        textColors.push(textColor) // Assign the text color to the textColors array.

        // colors.push(colorPalette[depth % colorPalette.length]);
        customdata.push(node.cumulativeSize || node.size || 0)

        if (node.children) {
          node.children.forEach((child) => traverse.call(this, child, id, depth + 1, color))
        }
      }

      // Start the traversal from the root node, passing an empty string for the parent and depth 0.
      traverse.call(this, data, '', 0, '')

      return [
        {
          type: 'sunburst',
          ids: ids,
          labels: labels,
          parents: parents,
          values: values,
          marker: { colors: colors, line: { width: 1 } },
          textfont: { color: textColors }, // Set the text color for each label.
          customdata: customdata,
          hovertemplate: '<b>%{label}</b> : %{customdata}<extra></extra>',
          textinfo: 'label',
          insidetextorientation: 'horizontal'
        }
      ]
    },
    createChart() {
      const layout = {
        margin: { t: 0, l: 0, r: 0, b: 0 },
        sunburstcolorway: this.getColors(),
        extendsunburstcolorway: true
      }

      Plotly.newPlot(this.$refs.chart, this.data, layout)

      this.$refs.chart.on('plotly_click', (event) => {
        const point = event.points[0]
        if (point) {
          Plotly.restyle(this.$refs.chart, 'root', [point.id])
        }
      })
    }
  }
}
</script>

<template>
  <div ref="chart"></div>
</template>
