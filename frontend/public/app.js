/**
 * Main Application Module
 * Orchestrates the customer feedback analysis application
 */

import { analyzeFeedback, getAnalytics, getConfig } from "./api.js";
import {
  initializeCharts,
  updateSentimentChart,
  updateScoresChart,
} from "./charts.js";

// Initialize app when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  console.log("Customer Feedback Analysis System - Initialized");
  console.log("Configuration:", getConfig());

  initializeCharts();
  loadAnalytics();
  setupEventListeners();
});

/**
 * Setup all event listeners
 */
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

/**
 * Handle feedback form submission
 * @param {Event} e - Form submit event
 */
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

  // Show loading state
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

    // Refresh analytics after a short delay
    setTimeout(() => loadAnalytics(), 500);

    // Reset form
    document.getElementById("feedbackForm").reset();
    updateCharCount();
  } catch (error) {
    console.error("Error analyzing feedback:", error);
    showToast(
      "Error analyzing feedback. Please try again.",
      "error"
    );
  } finally {
    // Restore button state
    submitBtn.disabled = false;
    btnText.style.display = "inline";
    btnLoader.style.display = "none";
  }
}

/**
 * Display analysis results
 * @param {Object} result - Analysis results
 */
function displayAnalysisResult(result) {
  const resultDiv = document.getElementById("analysisResult");
  resultDiv.style.display = "block";

  // Sentiment badge
  const sentimentBadge = document.getElementById("sentimentBadge");
  sentimentBadge.textContent = result.sentiment;
  sentimentBadge.className = `sentiment-badge ${result.sentiment}`;

  // Sentiment scores
  const scores = result.sentiment_scores;
  document.getElementById("positiveScore").textContent = `${(scores.positive * 100).toFixed(1)}%`;
  document.getElementById("negativeScore").textContent = `${(scores.negative * 100).toFixed(1)}%`;
  document.getElementById("neutralScore").textContent = `${(scores.neutral * 100).toFixed(1)}%`;
  document.getElementById("mixedScore").textContent = `${(scores.mixed * 100).toFixed(1)}%`;

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
            `<span class="entity-tag">${entity.text} (${entity.type})</span>`
        )
        .join("")}
    `;
  } else {
    entitiesDiv.innerHTML = "";
  }

  // Scroll to result
  resultDiv.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

/**
 * Load and display analytics
 */
async function loadAnalytics() {
  try {
    const analytics = await getAnalytics(50);

    // Update statistics
    document.getElementById("totalFeedback").textContent =
      analytics.total_feedback || 0;
    document.getElementById("positiveCount").textContent =
      analytics.sentiment_distribution?.POSITIVE || 0;
    document.getElementById("negativeCount").textContent =
      analytics.sentiment_distribution?.NEGATIVE || 0;
    document.getElementById("neutralCount").textContent =
      analytics.sentiment_distribution?.NEUTRAL || 0;

    // Update charts
    if (analytics.sentiment_distribution) {
      updateSentimentChart(analytics.sentiment_distribution);
    }

    if (analytics.average_sentiment_scores) {
      updateScoresChart(analytics.average_sentiment_scores);
    }

    // Display recent feedback
    if (analytics.recent_feedback) {
      displayRecentFeedback(analytics.recent_feedback);
    }
  } catch (error) {
    console.error("Error loading analytics:", error);
    showToast("Error loading analytics. Using cached data.", "error");
  }
}

/**
 * Display recent feedback list
 * @param {Array} feedbackList - List of recent feedback
 */
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
    `
    )
    .join("");
}

/**
 * Update character count display
 */
function updateCharCount() {
  const feedbackText = document.getElementById("feedbackText");
  const charCount = document.querySelector(".char-count");
  const count = feedbackText.value.length;

  charCount.textContent = `${count} characters`;

  // Warn if approaching limit
  if (count > 4500) {
    charCount.style.color = "#ef4444";
  } else {
    charCount.style.color = "#6b7280";
  }
}

/**
 * Show toast notification
 * @param {string} message - Message to display
 * @param {string} type - Type of toast (success, error, info)
 */
function showToast(message, type = "success") {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.className = `toast ${type} show`;

  setTimeout(() => {
    toast.classList.remove("show");
  }, 3000);
}

/**
 * Truncate text to specified length
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated text
 */
function truncateText(text, maxLength) {
  if (!text) return "";
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + "...";
}

/**
 * Format timestamp for display
 * @param {string} timestamp - ISO timestamp
 * @returns {string} Formatted timestamp
 */
function formatTimestamp(timestamp) {
  if (!timestamp) return "";

  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? "s" : ""} ago`;

  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? "s" : ""} ago`;

  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? "s" : ""} ago`;

  return date.toLocaleDateString();
}
