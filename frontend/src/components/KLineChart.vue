<template>
  <div ref="chartRef" class="kline-chart"></div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import dayjs from 'dayjs'

const props = defineProps({
  code: {
    type: String,
    required: true
  },
  type: {
    type: String,
    default: 'daily'
  },
  data: {
    type: Array,
    default: () => []
  },
  height: {
    type: String,
    default: '400px'
  }
})

const chartRef = ref(null)
let chartInstance = null

// 格式化K线数据
const formatKlineData = (data) => {
  return data.map(item => ({
    date: item.date || item.datetime,
    open: parseFloat(item.open) || 0,
    close: parseFloat(item.close) || 0,
    low: parseFloat(item.low) || 0,
    high: parseFloat(item.high) || 0,
    volume: parseInt(item.volume) || 0,
    ma20: item.ma20 ? parseFloat(item.ma20) : null,
    ma60: item.ma60 ? parseFloat(item.ma60) : null
  }))
}

// 初始化图表
const initChart = () => {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)
  updateChart()
}

// 更新图表
const updateChart = () => {
  if (!chartInstance || !props.data.length) return

  const formattedData = formatKlineData(props.data)
  const dates = formattedData.map(item => dayjs(item.date).format('MM-DD'))
  const klineData = formattedData.map(item => [item.open, item.close, item.low, item.high])
  const volumes = formattedData.map(item => item.volume)
  const ma20Data = formattedData.map(item => item.ma20)
  const ma60Data = formattedData.map(item => item.ma60)

  const option = {
    title: {
      text: `${props.code} - ${getChartTypeText()}`,
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: function (params) {
        const data = formattedData[params[0].dataIndex]
        return `
          <div style="padding: 10px;">
            <div>日期: ${dayjs(data.date).format('YYYY-MM-DD')}</div>
            <div>开盘: ${data.open.toFixed(2)}</div>
            <div>收盘: ${data.close.toFixed(2)}</div>
            <div>最低: ${data.low.toFixed(2)}</div>
            <div>最高: ${data.high.toFixed(2)}</div>
            <div>成交量: ${(data.volume / 10000).toFixed(2)}万</div>
          </div>
        `
      }
    },
    legend: {
      data: ['K线', 'MA20', 'MA60', '成交量'],
      top: 30
    },
    grid: [
      {
        left: '10%',
        right: '10%',
        top: '15%',
        height: '50%',
        containLabel: true
      },
      {
        left: '10%',
        right: '10%',
        top: '70%',
        height: '15%',
        containLabel: true
      }
    ],
    xAxis: [
      {
        type: 'category',
        data: dates,
        gridIndex: 0,
        scale: true,
        boundaryGap: false,
        axisLine: { onZero: false },
        splitLine: { show: false },
        splitNumber: 20,
        min: 'dataMin',
        max: 'dataMax'
      },
      {
        type: 'category',
        data: dates,
        gridIndex: 1,
        scale: true,
        boundaryGap: false,
        axisLine: { onZero: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        splitNumber: 20,
        min: 'dataMin',
        max: 'dataMax'
      }
    ],
    yAxis: [
      {
        type: 'value',
        gridIndex: 0,
        scale: true,
        splitArea: {
          show: true
        }
      },
      {
        type: 'value',
        gridIndex: 1,
        scale: true,
        splitNumber: 2,
        axisLabel: { show: false },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false }
      }
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1],
        start: Math.max(0, 100 - (formattedData.length / 60 * 100)),
        end: 100
      },
      {
        show: true,
        xAxisIndex: [0, 1],
        type: 'slider',
        top: '85%',
        start: Math.max(0, 100 - (formattedData.length / 60 * 100)),
        end: 100
      }
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: klineData,
        itemStyle: {
          color: '#ef232a',
          color0: '#14b143',
          borderColor: '#ef232a',
          borderColor0: '#14b143'
        }
      },
      {
        name: 'MA20',
        type: 'line',
        data: ma20Data,
        smooth: true,
        lineStyle: {
          opacity: 0.8
        }
      },
      {
        name: 'MA60',
        type: 'line',
        data: ma60Data,
        smooth: true,
        lineStyle: {
          opacity: 0.8
        }
      },
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumes
      }
    ]
  }

  chartInstance.setOption(option)
}

// 获取图表类型文本
const getChartTypeText = () => {
  const typeMap = {
    'daily': '日K线',
    'weekly': '周K线',
    '120min': '120分钟K线'
  }
  return typeMap[props.type] || 'K线'
}

// 监听数据变化
watch(
  () => props.data,
  () => {
    updateChart()
  },
  { deep: true }
)

// 监听类型变化
watch(
  () => props.type,
  () => {
    updateChart()
  }
)

// 窗口大小变化时重新渲染
const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

// 生命周期
onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style scoped>
.kline-chart {
  width: 100%;
  height: v-bind(height);
}
</style>