import * as echarts from "echarts/core";
import { BarChart, LineChart } from "echarts/charts";
import { GridComponent, TooltipComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

echarts.use([BarChart, LineChart, GridComponent, TooltipComponent, CanvasRenderer]);

const CHART_TEXT_COLOR = "#94A3B8";
const CHART_ACCENT = "#F97316";
const CHART_ACCENT_LIGHT = "rgba(249, 115, 22, 0.25)";
const TOOLTIP_BG = "rgba(15, 23, 42, 0.92)";

function baseGrid() {
  return { top: 12, right: 20, bottom: 32, left: 48 };
}

function baseTooltip() {
  return {
    backgroundColor: TOOLTIP_BG,
    borderColor: "rgba(249, 115, 22, 0.3)",
    textStyle: { color: "#E2E8F0", fontSize: 12 },
  };
}

function initChart(domRef) {
  if (!domRef.value) return null;
  return echarts.init(domRef.value);
}

export function useCharts() {
  let charts = [];

  function buildRatingDistChart(domRef, movies) {
    const instance = initChart(domRef);
    if (!instance) return;
    charts.push(instance);

    const ratings = movies.map((m) => m.rating).filter((r) => r > 0);
    const bins = [0, 5, 6, 7, 8, 9, 10];
    const labels = ["0-5", "5-6", "6-7", "7-8", "8-9", "9-10"];
    const counts = new Array(labels.length).fill(0);
    ratings.forEach((r) => {
      for (let i = bins.length - 2; i >= 0; i--) {
        if (r >= bins[i]) { counts[i]++; break; }
      }
    });

    instance.setOption({
      grid: baseGrid(),
      tooltip: baseTooltip(),
      xAxis: {
        type: "category", data: labels,
        axisLine: { lineStyle: { color: CHART_TEXT_COLOR } },
        axisTick: { show: false },
        axisLabel: { color: CHART_TEXT_COLOR, fontSize: 10 },
      },
      yAxis: {
        type: "value",
        splitLine: { lineStyle: { color: "rgba(148, 163, 184, 0.1)" } },
        axisLabel: { color: CHART_TEXT_COLOR },
      },
      series: [{
        type: "bar", data: counts,
        itemStyle: {
          borderRadius: [6, 6, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: CHART_ACCENT },
            { offset: 1, color: CHART_ACCENT_LIGHT },
          ]),
        },
        barWidth: "55%",
        emphasis: { itemStyle: { color: "#FB923C" } },
      }],
    });
  }

  function buildYearlyCountChart(domRef, movies) {
    const instance = initChart(domRef);
    if (!instance) return;
    charts.push(instance);

    const yearMap = {};
    movies.forEach((m) => {
      const y = m.year;
      if (y && y > 1900 && y < 2030) yearMap[y] = (yearMap[y] || 0) + 1;
    });
    const sorted = Object.entries(yearMap).sort((a, b) => +a[0] - +b[0]);

    instance.setOption({
      grid: baseGrid(),
      tooltip: baseTooltip(),
      xAxis: {
        type: "category", data: sorted.map(([y]) => y),
        axisLabel: { color: CHART_TEXT_COLOR, fontSize: 9, rotate: 45 },
        axisTick: { show: false },
        axisLine: { lineStyle: { color: CHART_TEXT_COLOR } },
      },
      yAxis: {
        type: "value",
        splitLine: { lineStyle: { color: "rgba(148, 163, 184, 0.1)" } },
        axisLabel: { color: CHART_TEXT_COLOR },
      },
      series: [{
        type: "line", data: sorted.map(([, c]) => c),
        smooth: true,
        lineStyle: { color: CHART_ACCENT, width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(249, 115, 22, 0.3)" },
            { offset: 1, color: "rgba(249, 115, 22, 0.02)" },
          ]),
        },
        itemStyle: { color: CHART_ACCENT },
        symbol: "none",
      }],
    });
  }

  function buildAvgRatingChart(domRef, movies) {
    const instance = initChart(domRef);
    if (!instance) return;
    charts.push(instance);

    const yearMap = {};
    movies.forEach((m) => {
      const y = m.year;
      if (!y || y < 1900 || y > 2030) return;
      if (!yearMap[y]) yearMap[y] = { sum: 0, cnt: 0 };
      yearMap[y].sum += m.rating || 0;
      yearMap[y].cnt += 1;
    });
    const sorted = Object.entries(yearMap)
      .map(([y, v]) => [y, v.sum / v.cnt])
      .sort((a, b) => +a[0] - +b[0]);

    instance.setOption({
      grid: baseGrid(),
      tooltip: baseTooltip(),
      xAxis: {
        type: "category", data: sorted.map(([y]) => y),
        axisLabel: { color: CHART_TEXT_COLOR, fontSize: 9, rotate: 45 },
        axisTick: { show: false },
        axisLine: { lineStyle: { color: CHART_TEXT_COLOR } },
      },
      yAxis: {
        type: "value", min: 4, max: 10,
        splitLine: { lineStyle: { color: "rgba(148, 163, 184, 0.1)" } },
        axisLabel: { color: CHART_TEXT_COLOR },
      },
      series: [{
        type: "line", data: sorted.map(([, avg]) => +avg.toFixed(2)),
        smooth: true,
        lineStyle: { color: "#22C55E", width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(34, 197, 94, 0.2)" },
            { offset: 1, color: "rgba(34, 197, 94, 0.02)" },
          ]),
        },
        itemStyle: { color: "#22C55E" },
        symbol: "none",
      }],
    });
  }

  function buildGenresChart(domRef, movies) {
    const instance = initChart(domRef);
    if (!instance) return;
    charts.push(instance);

    const genreCount = {};
    movies.forEach((m) => {
      const gs = parseGenres(m.genres);
      gs.forEach((g) => { genreCount[g] = (genreCount[g] || 0) + 1; });
    });
    const top10 = Object.entries(genreCount)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .reverse();

    instance.setOption({
      grid: { top: 4, right: 30, bottom: 20, left: 56 },
      tooltip: baseTooltip(),
      xAxis: {
        type: "value",
        splitLine: { lineStyle: { color: "rgba(148, 163, 184, 0.1)" } },
        axisLabel: { color: CHART_TEXT_COLOR },
      },
      yAxis: {
        type: "category", data: top10.map(([g]) => g),
        axisLine: { lineStyle: { color: CHART_TEXT_COLOR } },
        axisTick: { show: false },
        axisLabel: { color: CHART_TEXT_COLOR, fontSize: 11 },
      },
      series: [{
        type: "bar", data: top10.map(([, c]) => c),
        itemStyle: {
          borderRadius: [0, 6, 6, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: CHART_ACCENT_LIGHT },
            { offset: 1, color: CHART_ACCENT },
          ]),
        },
        barWidth: "60%",
      }],
    });
  }

  function destroyCharts() {
    charts.forEach((c) => c.dispose());
    charts = [];
  }

  function resizeCharts() {
    charts.forEach((c) => c?.resize?.());
  }

  function parseGenres(g) {
    if (!g) return [];
    if (Array.isArray(g)) return g.map((x) => x.trim()).filter(Boolean);
    return String(g).split(/[,，]/).map((x) => x.trim()).filter(Boolean);
  }

  return {
    buildRatingDistChart, buildYearlyCountChart,
    buildAvgRatingChart, buildGenresChart,
    destroyCharts, resizeCharts, parseGenres,
  };
}
