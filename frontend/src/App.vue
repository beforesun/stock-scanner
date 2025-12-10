<template>
  <div id="app">
    <el-container>
      <el-header class="app-header">
        <div class="header-content">
          <h1 class="app-title">
            <el-icon class="title-icon"><TrendCharts /></el-icon>
            A股量化交易筛选系统
          </h1>
          <el-menu
            :default-active="activeIndex"
            class="nav-menu"
            mode="horizontal"
            background-color="#545c64"
            text-color="#fff"
            active-text-color="#ffd04b"
            router
          >
            <el-menu-item index="/"><el-icon><DataAnalysis /></el-icon>周末扫描</el-menu-item>
            <el-menu-item index="/daily-pool"><el-icon><Filter /></el-icon>日筛选池</el-menu-item>
            <el-menu-item index="/signals"><el-icon><TrendCharts /></el-icon>交易信号</el-menu-item>
          </el-menu>
        </div>
      </el-header>

      <el-main class="app-main">
        <router-view />
      </el-main>

      <el-footer class="app-footer">
        <p>© 2024 A股量化交易筛选系统 - Powered by FastAPI + Vue3</p>
      </el-footer>
    </el-container>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { TrendCharts, DataAnalysis, Filter } from '@element-plus/icons-vue'

const route = useRoute()
const activeIndex = ref('/')

watch(
  () => route.path,
  (newPath) => {
    activeIndex.value = newPath
  },
  { immediate: true }
)
</script>

<style scoped>
.app-header {
  background-color: #545c64;
  color: white;
  padding: 0;
  height: 60px;
  line-height: 60px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.app-title {
  font-size: 24px;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  font-size: 28px;
}

.nav-menu {
  border-bottom: none;
}

.app-main {
  background-color: #f5f5f5;
  min-height: calc(100vh - 120px);
  padding: 20px;
}

.app-footer {
  background-color: #545c64;
  color: white;
  text-align: center;
  height: 40px;
  line-height: 40px;
}

.app-footer p {
  margin: 0;
}
</style>