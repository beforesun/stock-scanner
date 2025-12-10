<template>
  <div class="daily-pool">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>日筛选池</span>
          <el-button
            type="primary"
            @click="triggerScan"
            :loading="triggering"
            :icon="Refresh"
          >
            手动筛选
          </el-button>
        </div>
      </template>

      <!-- 筛选条件说明 -->
      <el-alert
        title="筛选条件"
        type="info"
        :closable="false"
        class="filter-info"
      >
        <ul>
          <li>均量线20日金叉60日</li>
          <li>120分钟MACD红柱连续放大</li>
        </ul>
      </el-alert>

      <!-- 统计信息 -->
      <el-descriptions :column="4" border class="stats-info">
        <el-descriptions-item label="筛选日期">{{ formatDate(dailyPoolResults.scanDate) }}</el-descriptions-item>
        <el-descriptions-item label="总数" >{{ dailyPoolResults.totalCount }}</el-descriptions-item>
        <el-descriptions-item label="入选数量"><span style="color: #409EFF; font-weight: bold;">{{ dailyPoolResults.poolCount }}</span></el-descriptions-item>
        <el-descriptions-item label="入选率">{{ selectionRate }}%</el-descriptions-item>
      </el-descriptions>

      <!-- 股票列表 -->
      <el-table
        :data="pagedResults"
        style="margin-top: 20px"
        v-loading="loading"
        stripe
        border
      >
        <el-table-column prop="code" label="代码" width="100" fixed />
        <el-table-column prop="name" label="名称" width="120" fixed />
        <el-table-column label="均量线金叉" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.golden_cross" type="success">金叉</el-tag>
            <el-tag v-else type="info">未金叉</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="vol_ma20" label="20日均量" width="120" />
        <el-table-column prop="vol_ma60" label="60日均量" width="120" />
        <el-table-column prop="macd_120min_status" label="MACD状态" min-width="180" />
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
              type="success"
              @click="viewSignals(row.code)"
              :icon="TrendCharts"
            >
              信号
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[20, 50, 100]"
          :total="dailyPoolResults.results.length"
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
import { triggerDailyScan } from '@/api/stock'

const router = useRouter()
const stockStore = useStockStore()

// 分页
const currentPage = ref(1)
const pageSize = ref(20)

// 触发扫描状态
const triggering = ref(false)

// 计算属性
const loading = computed(() => stockStore.loading)

const dailyPoolResults = computed(() => stockStore.dailyPoolResults)

const selectionRate = computed(() => {
  const { totalCount, poolCount } = dailyPoolResults.value
  return totalCount > 0 ? ((poolCount / totalCount) * 100).toFixed(2) : 0
})

// 分页数据
const pagedResults = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return dailyPoolResults.value.results.slice(start, end)
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
    ElMessage.info('正在执行日筛选，请稍候...')

    await triggerDailyScan()

    ElMessage.success('日筛选完成')

    // 刷新数据
    await stockStore.fetchDailyPool()
  } catch (error) {
    ElMessage.error('筛选失败：' + error.message)
  } finally {
    triggering.value = false
  }
}

const viewDetail = (code) => {
  router.push(`/stock/${code}`)
}

const viewSignals = (code) => {
  // 跳转到信号页面并过滤该股票
  router.push({
    path: '/signals',
    query: { code }
  })
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
  if (!dailyPoolResults.value.scanDate) {
    await stockStore.fetchDailyPool()
  }
})
</script>

<style scoped>
.daily-pool {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-info {
  margin-bottom: 20px;
}

.filter-info ul {
  margin: 10px 0;
  padding-left: 20px;
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