import { REC_BOOKS_COL_MAPPING } from "./config.js";

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

const fetchSuggestions = async (query) => {
  if (query.length < 4) return;

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
    console.error("Server error:", error);
    alert(`Error: ${error.detail || "Unknown error"}`);
    return;
  }
  const data = await response.json();
  console.log(data);
  //   const resultsList = document.getElementById("results");
  //   resultsList.innerHTML = "";

  const table = document.getElementById("results2");
  table.innerHTML = "";
  const thead = document.createElement("thead");
  table.appendChild(thead);

  const headerRow = document.createElement("tr");
  thead.appendChild(headerRow);
  //   data.recommended_books[0].keys()
  Object.keys(data.recommended_books[0]).forEach((k) => {
    const th = document.createElement("th");
    th.textContent = REC_BOOKS_COL_MAPPING[k];
    headerRow.appendChild(th);
  });

  const tbody = document.createElement("tbody");
  table.appendChild(tbody);

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

  //   data.recommended_books.forEach((book) => {
  //     const li = document.createElement("li");
  //     li.textContent = `${
  //       book.book_title
  //     } (corr: ${book.correlation_with_selected_book.toFixed(2)}, rating: ${
  //       book.average_rating
  //     })`;
  //     resultsList.appendChild(li);
  //   });
};

window.addEventListener("DOMContentLoaded", () => {
  document
    .getElementById("book-title-input")
    .addEventListener("input", (e) => fetchSuggestions(e.target.value));

  document
    .getElementById("recommend-button")
    .addEventListener("click", recommend);
});
