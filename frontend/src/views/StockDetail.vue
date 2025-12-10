<template>
  <div class="stock-detail">
    <!-- 返回按钮 -->
    <el-page-header @back="goBack" content="个股详情" />

    <!-- 基本信息 -->
    <el-card v-if="stockInfo" class="info-card">
      <template #header>
        <div class="card-header">
          <span>{{ stockInfo.code }} {{ stockInfo.name }}</span>
          <el-button-group class="header-actions">
            <el-button @click="refreshData" :icon="Refresh">刷新</el-button>
            <el-button @click="addToWatchlist" :icon="Star">关注</el-button>
          </el-button-group>
        </div>
      </template>

      <el-descriptions :column="3" border>
        <el-descriptions-item label="市场">{{ stockInfo.market }}</el-descriptions-item>
        <el-descriptions-item label="最新价">
          <span :class="{ 'price-up': stockInfo.latestPrice > stockInfo.prevClose, 'price-down': stockInfo.latestPrice < stockInfo.prevClose }">
            ¥{{ stockInfo.latestPrice }}
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag v-if="stockInfo.inWeekendPool" type="success">周末筛选通过</el-tag>
          <el-tag v-if="stockInfo.inDailyPool" type="primary">日筛选通过</el-tag>
          <el-tag v-if="stockInfo.hasSignal" type="warning">有交易信号</el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- K线图表 -->
    <el-card class="chart-card">
      <template #header>
        <div class="chart-header">
          <span>K线图</span>
          <el-radio-group v-model="chartType" size="small">
            <el-radio-button label="daily">日线</el-radio-button>
            <el-radio-button label="weekly">周线</el-radio-button>
            <el-radio-button label="120min">120分钟</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <div v-loading="chartLoading" class="chart-container">
        <KLineChart
          :code="stockCode"
          :type="chartType"
          :data="chartData"
          height="400px"
        />
      </div>
    </el-card>

    <!-- 相关信号 -->
    <el-card v-if="relatedSignals.length > 0" class="signals-card">
      <template #header>
        <span>相关交易信号</span>
      </template>

      <el-table :data="relatedSignals" stripe>
        <el-table-column prop="signal_date" label="信号日期" width="120">
          <template #default="{ row }">{{ formatDate(row.signal_date) }}</template>
        </el-table-column>
        <el-table-column prop="signal_type" label="类型" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.signal_type === 'BUY' ? 'success' : 'danger'" size="small">{{ row.signal_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="signal_price" label="信号价格" width="100" />
        <el-table-column prop="reason" label="理由" min-width="200" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Refresh, Star } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getStockDetail, getStockKlines } from '@/api/stock'
import KLineChart from '@/components/KLineChart.vue'

const route = useRoute()
const router = useRouter()

// 股票代码
const stockCode = ref(route.params.code)

// 数据
const stockInfo = ref(null)
const chartData = ref([])
const relatedSignals = ref([])

// 加载状态
const loading = ref(false)
const chartLoading = ref(false)

// 图表类型
const chartType = ref('daily')

// 方法
const goBack = () => {
  router.back()
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

const getStatusType = (status) => {
  const typeMap = {
    'PENDING': 'warning',
    'CONFIRMED': 'success',
    'INVALID': 'danger'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    'PENDING': '待处理',
    'CONFIRMED': '已确认',
    'INVALID': '已作废'
  }
  return textMap[status] || status
}

const loadStockDetail = async () => {
  loading.value = true
  try {
    const data = await getStockDetail(stockCode.value)
    stockInfo.value = data
  } catch (error) {
    ElMessage.error('加载股票详情失败')
  } finally {
    loading.value = false
  }
}

const loadChartData = async () => {
  chartLoading.value = true
  try {
    const data = await getStockKlines(
      stockCode.value,
      chartType.value,
      chartType.value === 'weekly' ? 52 : 60
    )
    chartData.value = data.data
  } catch (error) {
    ElMessage.error('加载K线数据失败')
  } finally {
    chartLoading.value = false
  }
}

const refreshData = async () => {
  await loadStockDetail()
  await loadChartData()
  ElMessage.success('数据已刷新')
}

const addToWatchlist = () => {
  // TODO: 实现关注功能
  ElMessage.info('关注功能开发中...')
}

// 监听图表类型变化
watch(chartType, () => {
  loadChartData()
})

// 生命周期
onMounted(async () => {
  await loadStockDetail()
  await loadChartData()
})
</script>

<style scoped>
.stock-detail {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.info-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.price-up {
  color: #F56C6C;
  font-weight: bold;
}

.price-down {
  color: #67C23A;
  font-weight: bold;
}

.chart-card {
  margin-bottom: 20px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  width: 100%;
  height: 400px;
}

.signals-card {
  margin-bottom: 20px;
}

.mt-20 {
  margin-top: 20px;
}

@media (max-width: 768px) {
  .stock-detail {
    padding: 10px;
  }

  .chart-container {
    height: 300px;
  }
}
</style>