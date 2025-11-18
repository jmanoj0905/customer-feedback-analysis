// Configuration - Update this with your API Gateway URL
const CONFIG = {
  API_ENDPOINT: "YOUR_API_GATEWAY_URL_HERE", // e.g., 'https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/analyze'
  USE_MOCK_DATA: true, // Set to false when API is ready
};

// Chart instances
let sentimentChart = null;
let scoresChart = null;

// Initialize app
document.addEventListener("DOMContentLoaded", () => {
  initializeCharts();
  loadAnalytics();
  setupEventListeners();
});

// Setup Event Listeners
function setupEventListeners() {
  // Feedback form submission
  const feedbackForm = document.getElementById("feedbackForm");
  feedbackForm.addEventListener("submit", handleFeedbackSubmit);

  // Character counter
  const feedbackText = document.getElementById("feedbackText");
  feedbackText.addEventListener("input", updateCharCount);

  // Refresh button
  const refreshBtn = document.getElementById("refreshBtn");
  refreshBtn.addEventListener("click", loadAnalytics);
}

// Handle feedback form submission
async function handleFeedbackSubmit(e) {
  e.preventDefault();

  const feedbackText = document.getElementById("feedbackText").value.trim();
  const customerId =
    document.getElementById("customerId").value.trim() || "anonymous";
  const category = document.getElementById("category").value;

  if (!feedbackText) {
    showToast("Please enter feedback text", "error");
    return;
  }

  // Disable submit button
  const submitBtn = document.getElementById("submitBtn");
  const btnText = submitBtn.querySelector(".btn-text");
  const btnLoader = submitBtn.querySelector(".btn-loader");

  submitBtn.disabled = true;
  btnText.style.display = "none";
  btnLoader.style.display = "inline-flex";

  try {
    const result = await analyzeFeedback({
      feedback: feedbackText,
      customer_id: customerId,
      metadata: {
        category: category,
        timestamp: new Date().toISOString(),
      },
    });

    displayAnalysisResult(result);
    showToast("Feedback analyzed successfully!", "success");

    // Refresh analytics
    setTimeout(() => loadAnalytics(), 500);

    // Reset form
    document.getElementById("feedbackForm").reset();
    updateCharCount();
  } catch (error) {
    console.error("Error:", error);
    showToast("Error analyzing feedback. Please try again.", "error");
  } finally {
    // Re-enable submit button
    submitBtn.disabled = false;
    btnText.style.display = "inline";
    btnLoader.style.display = "none";
  }
}

// Analyze feedback via API
async function analyzeFeedback(data) {
  if (CONFIG.USE_MOCK_DATA) {
    // Mock response for testing without AWS
    return generateMockAnalysis(data.feedback);
  }

  const response = await fetch(CONFIG.API_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      operation: "analyze_feedback",
      ...data,
    }),
  });

  if (!response.ok) {
    throw new Error("API request failed");
  }

  return await response.json();
}

// Get analytics from API
async function getAnalytics() {
  if (CONFIG.USE_MOCK_DATA) {
    // Mock analytics for testing
    return generateMockAnalytics();
  }

  const response = await fetch(CONFIG.API_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      operation: "get_analytics",
      limit: 50,
    }),
  });

  if (!response.ok) {
    throw new Error("API request failed");
  }

  return await response.json();
}

// Display analysis result
function displayAnalysisResult(result) {
  const resultDiv = document.getElementById("analysisResult");
  resultDiv.style.display = "block";

  // Sentiment badge
  const sentimentBadge = document.getElementById("sentimentBadge");
  sentimentBadge.textContent = result.sentiment;
  sentimentBadge.className = `sentiment-badge ${result.sentiment}`;

  // Scores
  const scores = result.sentiment_scores;
  document.getElementById("positiveScore").textContent =
    `${(scores.positive * 100).toFixed(1)}%`;
  document.getElementById("negativeScore").textContent =
    `${(scores.negative * 100).toFixed(1)}%`;
  document.getElementById("neutralScore").textContent =
    `${(scores.neutral * 100).toFixed(1)}%`;
  document.getElementById("mixedScore").textContent =
    `${(scores.mixed * 100).toFixed(1)}%`;

  // Key phrases
  const keyPhrasesDiv = document.getElementById("keyPhrases");
  if (result.key_phrases && result.key_phrases.length > 0) {
    keyPhrasesDiv.innerHTML = `
            <h4>Key Phrases</h4>
            ${result.key_phrases
              .map((phrase) => `<span class="phrase-tag">${phrase.text}</span>`)
              .join("")}
        `;
  } else {
    keyPhrasesDiv.innerHTML = "";
  }

  // Entities
  const entitiesDiv = document.getElementById("entities");
  if (result.entities && result.entities.length > 0) {
    entitiesDiv.innerHTML = `
            <h4>Detected Entities</h4>
            ${result.entities
              .map(
                (entity) =>
                  `<span class="entity-tag">${entity.text} (${entity.type})</span>`,
              )
              .join("")}
        `;
  } else {
    entitiesDiv.innerHTML = "";
  }

  // Scroll to result
  resultDiv.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// Load and display analytics
async function loadAnalytics() {
  try {
    const analytics = await getAnalytics();

    // Update stats
    document.getElementById("totalFeedback").textContent =
      analytics.total_feedback;
    document.getElementById("positiveCount").textContent =
      analytics.sentiment_distribution.POSITIVE;
    document.getElementById("negativeCount").textContent =
      analytics.sentiment_distribution.NEGATIVE;
    document.getElementById("neutralCount").textContent =
      analytics.sentiment_distribution.NEUTRAL;

    // Update charts
    updateSentimentChart(analytics.sentiment_distribution);
    updateScoresChart(analytics.average_sentiment_scores);

    // Update recent feedback list
    displayRecentFeedback(analytics.recent_feedback);
  } catch (error) {
    console.error("Error loading analytics:", error);
    showToast("Error loading analytics", "error");
  }
}

// Initialize charts
function initializeCharts() {
  // Sentiment Distribution Pie Chart
  const sentimentCtx = document
    .getElementById("sentimentChart")
    .getContext("2d");
  sentimentChart = new Chart(sentimentCtx, {
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
        },
      },
    },
  });

  // Average Scores Bar Chart
  const scoresCtx = document.getElementById("scoresChart").getContext("2d");
  scoresChart = new Chart(scoresCtx, {
    type: "bar",
    data: {
      labels: ["Positive", "Negative", "Neutral", "Mixed"],
      datasets: [
        {
          label: "Average Score",
          data: [0, 0, 0, 0],
          backgroundColor: ["#10b981", "#ef4444", "#6b7280", "#f59e0b"],
          borderWidth: 0,
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
        },
      },
      plugins: {
        legend: {
          display: false,
        },
      },
    },
  });
}

// Update sentiment chart
function updateSentimentChart(distribution) {
  sentimentChart.data.datasets[0].data = [
    distribution.POSITIVE,
    distribution.NEGATIVE,
    distribution.NEUTRAL,
    distribution.MIXED,
  ];
  sentimentChart.update();
}

// Update scores chart
function updateScoresChart(scores) {
  scoresChart.data.datasets[0].data = [
    scores.positive,
    scores.negative,
    scores.neutral,
    scores.mixed,
  ];
  scoresChart.update();
}

// Display recent feedback
function displayRecentFeedback(feedbackList) {
  const listDiv = document.getElementById("recentFeedbackList");

  if (!feedbackList || feedbackList.length === 0) {
    listDiv.innerHTML =
      '<p class="empty-state">No feedback analyzed yet. Submit your first feedback!</p>';
    return;
  }

  listDiv.innerHTML = feedbackList
    .map(
      (item) => `
        <div class="feedback-item">
            <div class="feedback-header">
                <span class="feedback-id">${item.customer_id}</span>
                <span class="feedback-sentiment ${item.sentiment}">${item.sentiment}</span>
            </div>
            <div class="feedback-text">${truncateText(item.feedback_text, 150)}</div>
            <div class="feedback-timestamp">${formatTimestamp(item.timestamp)}</div>
        </div>
    `,
    )
    .join("");
}

// Update character count
function updateCharCount() {
  const feedbackText = document.getElementById("feedbackText");
  const charCount = document.querySelector(".char-count");
  charCount.textContent = `${feedbackText.value.length} characters`;
}

// Show toast notification
function showToast(message, type = "success") {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.className = `toast ${type} show`;

  setTimeout(() => {
    toast.classList.remove("show");
  }, 3000);
}

// Utility: Truncate text
function truncateText(text, maxLength) {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + "...";
}

// Utility: Format timestamp
function formatTimestamp(timestamp) {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins} minutes ago`;

  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours} hours ago`;

  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays} days ago`;

  return date.toLocaleDateString();
}

// Mock data generators for testing without AWS
function generateMockAnalysis(feedbackText) {
  // Simple sentiment detection based on keywords
  const positiveWords = [
    "good",
    "great",
    "excellent",
    "amazing",
    "love",
    "best",
    "wonderful",
    "fantastic",
  ];
  const negativeWords = [
    "bad",
    "poor",
    "terrible",
    "worst",
    "hate",
    "awful",
    "horrible",
    "disappointing",
  ];

  const text = feedbackText.toLowerCase();
  const hasPositive = positiveWords.some((word) => text.includes(word));
  const hasNegative = negativeWords.some((word) => text.includes(word));

  let sentiment = "NEUTRAL";
  let scores = { positive: 0.25, negative: 0.25, neutral: 0.4, mixed: 0.1 };

  if (hasPositive && hasNegative) {
    sentiment = "MIXED";
    scores = { positive: 0.35, negative: 0.35, neutral: 0.2, mixed: 0.1 };
  } else if (hasPositive) {
    sentiment = "POSITIVE";
    scores = { positive: 0.85, negative: 0.05, neutral: 0.08, mixed: 0.02 };
  } else if (hasNegative) {
    sentiment = "NEGATIVE";
    scores = { positive: 0.05, negative: 0.85, neutral: 0.08, mixed: 0.02 };
  }

  // Extract simple key phrases (words)
  const words = feedbackText.split(/\s+/).filter((w) => w.length > 4);
  const keyPhrases = words.slice(0, 5).map((text) => ({
    text: text,
    score: 0.9,
  }));

  return {
    feedback_id: `feedback_${Date.now()}`,
    customer_id: document.getElementById("customerId").value || "anonymous",
    feedback_text: feedbackText,
    timestamp: new Date().toISOString(),
    sentiment: sentiment,
    sentiment_scores: scores,
    key_phrases: keyPhrases,
    entities: [],
  };
}

function generateMockAnalytics() {
  // Get existing feedback from localStorage
  let feedbackHistory = JSON.parse(
    localStorage.getItem("feedbackHistory") || "[]",
  );

  // Count sentiments
  const distribution = {
    POSITIVE: 0,
    NEGATIVE: 0,
    NEUTRAL: 0,
    MIXED: 0,
  };

  const avgScores = { positive: 0, negative: 0, neutral: 0, mixed: 0 };

  feedbackHistory.forEach((item) => {
    distribution[item.sentiment]++;
    avgScores.positive += item.sentiment_scores.positive;
    avgScores.negative += item.sentiment_scores.negative;
    avgScores.neutral += item.sentiment_scores.neutral;
    avgScores.mixed += item.sentiment_scores.mixed;
  });

  const total = feedbackHistory.length;
  if (total > 0) {
    Object.keys(avgScores).forEach((key) => {
      avgScores[key] = avgScores[key] / total;
    });
  }

  return {
    total_feedback: total,
    sentiment_distribution: distribution,
    average_sentiment_scores: avgScores,
    recent_feedback: feedbackHistory.slice(-10).reverse(),
  };
}

// Store feedback in localStorage for mock mode
const originalAnalyzeFeedback = analyzeFeedback;
analyzeFeedback = async function (data) {
  const result = await originalAnalyzeFeedback(data);

  if (CONFIG.USE_MOCK_DATA) {
    let feedbackHistory = JSON.parse(
      localStorage.getItem("feedbackHistory") || "[]",
    );
    feedbackHistory.push(result);
    // Keep only last 100 items
    if (feedbackHistory.length > 100) {
      feedbackHistory = feedbackHistory.slice(-100);
    }
    localStorage.setItem("feedbackHistory", JSON.stringify(feedbackHistory));
  }

  return result;
};
