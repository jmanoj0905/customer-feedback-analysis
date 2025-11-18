/**
 * Charts Module
 * Handles all chart initialization and updates using Chart.js
 */

let sentimentChart = null;
let scoresChart = null;

/**
 * Initialize all charts
 */
export function initializeCharts() {
  initSentimentChart();
  initScoresChart();
}

/**
 * Initialize sentiment distribution pie chart
 */
function initSentimentChart() {
  const ctx = document.getElementById("sentimentChart").getContext("2d");

  sentimentChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Positive", "Negative", "Neutral", "Mixed"],
      datasets: [
        {
          data: [0, 0, 0, 0],
          backgroundColor: ["#10b981", "#ef4444", "#6b7280", "#f59e0b"],
          borderWidth: 2,
          borderColor: "#ffffff",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            padding: 15,
            font: {
              size: 12,
            },
          },
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              const label = context.label || "";
              const value = context.parsed || 0;
              const total = context.dataset.data.reduce((a, b) => a + b, 0);
              const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
              return `${label}: ${value} (${percentage}%)`;
            },
          },
        },
      },
    },
  });
}

/**
 * Initialize average scores bar chart
 */
function initScoresChart() {
  const ctx = document.getElementById("scoresChart").getContext("2d");

  scoresChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["Positive", "Negative", "Neutral", "Mixed"],
      datasets: [
        {
          label: "Average Score",
          data: [0, 0, 0, 0],
          backgroundColor: ["#10b981", "#ef4444", "#6b7280", "#f59e0b"],
          borderWidth: 0,
          borderRadius: 8,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      scales: {
        y: {
          beginAtZero: true,
          max: 1,
          ticks: {
            callback: function (value) {
              return (value * 100).toFixed(0) + "%";
            },
          },
          grid: {
            color: "#e5e7eb",
          },
        },
        x: {
          grid: {
            display: false,
          },
        },
      },
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              return `Score: ${(context.parsed.y * 100).toFixed(1)}%`;
            },
          },
        },
      },
    },
  });
}

/**
 * Update sentiment distribution chart
 * @param {Object} distribution - Sentiment distribution data
 */
export function updateSentimentChart(distribution) {
  if (!sentimentChart) return;

  sentimentChart.data.datasets[0].data = [
    distribution.POSITIVE || 0,
    distribution.NEGATIVE || 0,
    distribution.NEUTRAL || 0,
    distribution.MIXED || 0,
  ];

  sentimentChart.update();
}

/**
 * Update average scores chart
 * @param {Object} scores - Average sentiment scores
 */
export function updateScoresChart(scores) {
  if (!scoresChart) return;

  scoresChart.data.datasets[0].data = [
    scores.positive || 0,
    scores.negative || 0,
    scores.neutral || 0,
    scores.mixed || 0,
  ];

  scoresChart.update();
}

/**
 * Destroy all charts (cleanup)
 */
export function destroyCharts() {
  if (sentimentChart) {
    sentimentChart.destroy();
    sentimentChart = null;
  }

  if (scoresChart) {
    scoresChart.destroy();
    scoresChart = null;
  }
}
