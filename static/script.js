import { ERROR_MESSAGES, REC_BOOKS_COL_MAPPING } from "./config.js";

/**
 * Displays an error message in the error box.
 * @param {string} msg - The message to display. Hides the box if empty.
 */
const showError = (msg) => {
  const box = document.getElementById("error-box");

  box.textContent = msg;
  box.style.visibility = msg ? "visible" : "hidden";
};

/**
 * Handles error details returned from the backend and shows appropriate user message.
 * @param {{ code: string }} errorDetail - Object containing error code from backend.
 */
const handleError = (errorDetail) => {
  const errorMeta = ERROR_MESSAGES[errorDetail.code];

  showError(errorMeta.msg);
};

/**
 * Creates an HTML <img> element with optional dimensions.
 * @param {string} url - The image source URL.
 * @param {string} alt - The alt text for accessibility.
 * @param {number} [w=0] - Optional width in pixels.
 * @param {number} [h=0] - Optional height in pixels.
 * @returns {HTMLImageElement} - The constructed <img> element.
 */
const createHTMLImage = (url, alt, w = 0, h = 0) => {
  const img = document.createElement("img");
  img.src = url;
  img.alt = alt;

  if (w > 0 && h > 0) {
    img.width = w;
    img.height = h;
  }

  return img;
};

/**
 * Constructs and populates the table body with recommended books data.
 * @param {{ recommended_books: Object[] }} data - The backend response containing book data.
 */
const constructTable = (data) => {
  const tbody = document.getElementById("results");
  tbody.innerHTML = "";

  data.recommended_books.forEach((book) => {
    const tr = document.createElement("tr");
    tbody.appendChild(tr);

    Object.entries(book).forEach(([k, v]) => {
      const td = document.createElement("td");
      if (k.includes("image_url")) {
        td.appendChild(createHTMLImage(v, "Book Cover", 60, 90));
      } else {
        td.textContent = v;
      }

      tr.appendChild(td);
    });
  });
};

/**
 * Fetches autocomplete suggestions based on partial query and populates datalist.
 * @param {string} query - The partial book title input by the user.
 */
const fetchSuggestions = async (query) => {
  if (query.length === 0 || query.length % 3 !== 0) return;

  const dataList = document.getElementById("book-options");

  try {
    const response = await fetch(
      `http://localhost:8000/autocomplete?q=${encodeURIComponent(query)}`
    );
    const data = await response.json();

    dataList.innerHTML = "";
    data.suggestions.forEach((title) => {
      const option = document.createElement("option");
      option.value = title;
      dataList.appendChild(option);
    });
  } catch (error) {
    console.log("Fetch failed: ", error);
  }
};

/**
 * Sends recommendation request to the backend and displays results in the table.
 */
const recommend = async () => {
  const bookTitle = document.getElementById("book-title-input").value;
  const topN = document.getElementById("top-n").value;

  const response = await fetch("http://localhost:8000/recommend", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      book_title: bookTitle,
      top_n: parseInt(topN),
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    handleError(error.detail);
    return;
  }
  const data = await response.json();

  constructTable(data);
};

/**
 * Initializes event listeners after DOM is fully loaded.
 */
window.addEventListener("DOMContentLoaded", () => {
  document.getElementById("book-title-input").addEventListener("input", (e) => {
    showError("");
    fetchSuggestions(e.target.value);
  });

  document
    .getElementById("recommend-button")
    .addEventListener("click", recommend);
});
