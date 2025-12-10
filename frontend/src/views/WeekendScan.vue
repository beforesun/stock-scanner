<template>
  <div class="weekend-scan">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>周末扫描结果</span>
          <el-button
            type="primary"
            @click="triggerScan"
            :loading="triggering"
            :icon="Refresh"
          >
            手动扫描
          </el-button>
        </div>
      </template>

      <!-- 统计信息 -->
      <el-descriptions :column="4" border class="stats-info">
        <el-descriptions-item label="扫描日期">{{ formatDate(weekendScanResults.scanDate) }}</el-descriptions-item>
        <el-descriptions-item label="扫描总数">{{ weekendScanResults.totalCount }}</el-descriptions-item>
        <el-descriptions-item label="通过数量">{{ weekendScanResults.passedCount }}</el-descriptions-item>
        <el-descriptions-item label="通过率">{{ passRate }}%</el-descriptions-item>
      </el-descriptions>

      <!-- 股票列表 -->
      <el-table
        :data="weekendScanResults.results"
        style="margin-top: 20px"
        v-loading="loading"
        stripe
        border
      >
        <el-table-column prop="code" label="代码" width="100" fixed />
        <el-table-column prop="name" label="名称" width="120" fixed />
        <el-table-column prop="close_price" label="收盘价" width="100" />
        <el-table-column prop="ma233_weekly" label="233周均线" width="110" />
        <el-table-column prop="volume" label="周成交量" width="120" />
        <el-table-column prop="vol_ma20_weekly" label="周MA20" width="120" />
        <el-table-column label="条件满足" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="success">通过</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right" align="center">
          <template #default="{ row }">
            <el-button
              size="small"
              type="primary"
              @click="viewDetail(row.code)"
              :icon="View"
            >
              详情
            </el-button>
            <el-button
              size="small"
              @click="viewKLine(row.code)"
              :icon="TrendCharts"
            >
              K线
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[20, 50, 100, 200]"
          :total="weekendScanResults.results.length"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStockStore } from '@/stores/stock'
import { Refresh, View, TrendCharts } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { triggerWeekendScan } from '@/api/stock'

const router = useRouter()
const stockStore = useStockStore()

// 分页
const currentPage = ref(1)
const pageSize = ref(20)

// 触发扫描状态
const triggering = ref(false)

// 计算属性
const loading = computed(() => stockStore.loading)

const weekendScanResults = computed(() => stockStore.weekendScanResults)

const passRate = computed(() => {
  const { totalCount, passedCount } = weekendScanResults.value
  return totalCount > 0 ? ((passedCount / totalCount) * 100).toFixed(2) : 0
})

// 分页数据
const pagedResults = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return weekendScanResults.value.results.slice(start, end)
})

// 方法
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

const triggerScan = async () => {
  try {
    triggering.value = true
    ElMessage.info('正在执行周末扫描，请稍候...')

    await triggerWeekendScan()

    ElMessage.success('周末扫描完成')

    // 刷新数据
    await stockStore.fetchWeekendScan()
  } catch (error) {
    ElMessage.error('扫描失败：' + error.message)
  } finally {
    triggering.value = false
  }
}

const viewDetail = (code) => {
  router.push(`/stock/${code}`)
}

const viewKLine = (code) => {
  // TODO: 打开K线图表弹窗
  ElMessage.info('K线功能开发中...')
}

const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val) => {
  currentPage.value = val
}

// 生命周期
onMounted(async () => {
  if (!weekendScanResults.value.scanDate) {
    await stockStore.fetchWeekendScan()
  }
})
</script>

<style scoped>
.weekend-scan {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats-info {
  margin-top: 20px;
}

.pagination-container {
  margin-top: 20px;
  text-align: center;
}

:deep(.el-table) {
  .el-table__row:hover {
    cursor: pointer;
  }
}
</style>