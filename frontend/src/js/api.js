/**
 * API Module
 * Handles all API calls to the backend
 */

// Configuration
const CONFIG = {
  API_ENDPOINT: "YOUR_API_GATEWAY_URL_HERE",
  USE_MOCK_DATA: true, // Set to false when API is deployed
  TIMEOUT: 30000, // 30 seconds
};

/**
 * Analyze customer feedback
 * @param {Object} data - Feedback data
 * @returns {Promise<Object>} Analysis results
 */
export async function analyzeFeedback(data) {
  if (CONFIG.USE_MOCK_DATA) {
    return generateMockAnalysis(data.feedback);
  }

  try {
    const response = await fetchWithTimeout(CONFIG.API_ENDPOINT, {
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
      throw new Error(`API request failed with status ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error analyzing feedback:", error);
    throw error;
  }
}

/**
 * Get analytics data
 * @param {number} limit - Maximum number of items to retrieve
 * @returns {Promise<Object>} Analytics data
 */
export async function getAnalytics(limit = 50) {
  if (CONFIG.USE_MOCK_DATA) {
    return generateMockAnalytics();
  }

  try {
    const response = await fetchWithTimeout(CONFIG.API_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        operation: "get_analytics",
        limit: limit,
      }),
    });

    if (!response.ok) {
      throw new Error(`API request failed with status ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error getting analytics:", error);
    throw error;
  }
}

/**
 * Fetch with timeout
 * @param {string} url - URL to fetch
 * @param {Object} options - Fetch options
 * @returns {Promise<Response>} Fetch response
 */
function fetchWithTimeout(url, options = {}) {
  return Promise.race([
    fetch(url, options),
    new Promise((_, reject) =>
      setTimeout(() => reject(new Error("Request timeout")), CONFIG.TIMEOUT)
    ),
  ]);
}

/**
 * Generate mock analysis for testing
 * @param {string} feedbackText - Feedback text
 * @returns {Object} Mock analysis results
 */
function generateMockAnalysis(feedbackText) {
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

  const words = feedbackText.split(/\s+/).filter((w) => w.length > 4);
  const keyPhrases = words.slice(0, 5).map((text) => ({
    text: text,
    score: 0.9,
  }));

  const result = {
    feedback_id: `feedback_${Date.now()}`,
    customer_id: "mock_customer",
    feedback_text: feedbackText,
    timestamp: new Date().toISOString(),
    sentiment: sentiment,
    sentiment_scores: scores,
    key_phrases: keyPhrases,
    entities: [],
    language: { language_code: "en", score: 1.0 },
  };

  // Store in localStorage
  storeFeedbackLocally(result);

  return result;
}

/**
 * Generate mock analytics
 * @returns {Object} Mock analytics data
 */
function generateMockAnalytics() {
  const feedbackHistory = JSON.parse(
    localStorage.getItem("feedbackHistory") || "[]"
  );

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
    timestamp: new Date().toISOString(),
  };
}

/**
 * Store feedback locally in localStorage
 * @param {Object} feedback - Feedback to store
 */
function storeFeedbackLocally(feedback) {
  let feedbackHistory = JSON.parse(
    localStorage.getItem("feedbackHistory") || "[]"
  );
  feedbackHistory.push(feedback);

  // Keep only last 100 items
  if (feedbackHistory.length > 100) {
    feedbackHistory = feedbackHistory.slice(-100);
  }

  localStorage.setItem("feedbackHistory", JSON.stringify(feedbackHistory));
}

/**
 * Update API endpoint configuration
 * @param {string} endpoint - New API endpoint URL
 */
export function updateApiEndpoint(endpoint) {
  CONFIG.API_ENDPOINT = endpoint;
  CONFIG.USE_MOCK_DATA = false;
}

/**
 * Get current configuration
 * @returns {Object} Current configuration
 */
export function getConfig() {
  return { ...CONFIG };
}
