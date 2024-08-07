<template>
  <div ref="chart" class="chart"></div>
  <div
    ref="tooltip"
    class="tooltip"
    style="position: absolute; opacity: 0; pointer-events: none; transition: opacity 0.3s"
  ></div>
</template>

<script>
import * as d3 from 'd3'

export default {
  name: 'SunburstChart',
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
        const response = await fetch('http://localhost:5173/public/data.json')
        if (!response.ok) {
          throw new Error('Network response was not ok ' + response.statusText)
        }
        const data = await response.json()
        this.data = data[0]
        console.log('Fetched data:', this.data) // Log fetched data for verification
        this.createChart()
      } catch (error) {
        console.error('Error fetching data:', error)
      }
    },
    createChart() {
      const width = 700
      const radius = width / 2

      const svg = d3
        .select(this.$refs.chart)
        .append('svg')
        .attr('width', width)
        .attr('height', width)
        .append('g')
        .attr('transform', `translate(${radius},${radius})`)

      const tooltip = d3.select(this.$refs.tooltip) // Correctly define tooltip within D3 context

      const partition = d3.partition().size([2 * Math.PI, radius])

      const root = d3
        .hierarchy(this.data)
        .sum((d) => (d.size && !d.children ? d.size : 0))
        .sort((a, b) => b.value - a.value)

      partition(root)

      const arc = d3
        .arc()
        .startAngle((d) => d.x0)
        .endAngle((d) => d.x1)
        .innerRadius((d) => d.y0)
        .outerRadius((d) => d.y1)

      const path = svg
        .selectAll('path')
        .data(root.descendants())
        .enter()
        .append('path')
        .attr('d', arc)
        .style('fill', (d) => d.data.color || '#ccc')
        .on('mouseover', function (event, d) {
          const color = d3.select(this).style('fill')
          tooltip
            .style('opacity', 1)
            .html(`Name: ${d.data.name}<br>Size: ${d.value}`)
            .style('left', event.pageX + 10 + 'px')
            .style('top', event.pageY - 20 + 'px')
            .style('background-color', color)
        })
        .on('mouseout', function () {
          tooltip.style('opacity', 0)
        })
        .on('click', clicked)
        .append('title')
        .text((d) => `${d.data.name}\n${d.value}`)

      function clicked(event, p) {
        console.log('Clicked on:', p.data.name) // Log click event for verification
        root.each((d) => (d.current = d.target || d))

        const parent = p.parent
        const depth = p.depth

        // Rescale
        root.each((d) => {
          d.target = {
            x0: Math.max(0, Math.min(1, (d.x0 - p.x0) / (p.x1 - p.x0))) * 2 * Math.PI,
            x1: Math.max(0, Math.min(1, (d.x1 - p.x0) / (p.x1 - p.x0))) * 2 * Math.PI,
            y0: Math.max(0, d.y0 - p.y0),
            y1: Math.max(0, d.y1 - p.y0)
          }
        })

        const t = svg.transition().duration(750)

        path
          .transition(t)
          .tween('data', (d) => {
            const i = d3.interpolate(d.current, d.target)
            return (t) => (d.current = i(t))
          })
          .attrTween('d', (d) => () => arc(d.current))
      }

      // Add labels
      svg
        .selectAll('text')
        .data(root.descendants())
        .enter()
        .append('text')
        .attr('transform', function (d) {
          const x = (((d.x0 + d.x1) / 2) * 180) / Math.PI
          if (d.depth === 0) {
            return `translate(0, 0)`
          } else if (d.data.name === 'Y') {
            // Specific adjustment for 'Y'
            return `rotate(${x - 90}) translate(${(d.y0 + d.y1) / 2},0) rotate(${
              x < 270 && x > 90 ? 180 : 0
            })`
          } else {
            return `rotate(${x - 90}) translate(${(d.y0 + d.y1) / 2},0) rotate(${
              x < 180 ? 0 : 180
            })`
          }
        })
        .attr('dy', '0.35em')
        .attr('dx', '0.5em')
        .text((d) => d.data.name)
        .style('text-anchor', 'middle')
        .style('font-size', '10px')
    }
  }
}
</script>

<style scoped>
.chart {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
}

.tooltip {
  background-color: white;
  border: 1px solid #d3d3d3;
  border-radius: 5px;
  padding: 10px;
  color: black;
  font-size: 12px;
  max-width: 200px;
}
</style>
