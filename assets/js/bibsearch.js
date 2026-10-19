document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("bibsearch-form");
  const input = document.getElementById("bibsearch");
  if (!form || !input) return;

  const normalize = (text) =>
    text
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase();
  const publications = Array.from(document.querySelectorAll("#publication-list [data-publication-key]")).map((entry) => ({
    item: entry.closest("li"),
    text: normalize([entry.dataset.publicationTitle, entry.dataset.publicationAuthors, entry.dataset.publicationYear].join(" ")),
  }));
  const status = document.getElementById("bibsearch-status");
  const empty = document.getElementById("bibsearch-empty");
  const clear = form.querySelector('[type="reset"]');
  let timeoutId;

  const filterItems = (updateUrl = true) => {
    const query = input.value.trim();
    const terms = normalize(query).split(/\s+/).filter(Boolean);
    let count = 0;
    publications.forEach(({ item, text }) => {
      const matches = terms.every((term) => text.includes(term));
      item.hidden = !matches;
      if (matches) count += 1;
    });
    status.textContent = query
      ? `${count} of ${publications.length} publications match your search.`
      : `Showing all ${publications.length} publications.`;
    empty.hidden = count !== 0;
    clear.disabled = input.value.length === 0;

    if (updateUrl) {
      const url = new URL(window.location.href);
      if (query) url.searchParams.set("q", query);
      else url.searchParams.delete("q");
      // Keep section and publication anchors independent of the search query.
      window.history.replaceState(window.history.state, "", url);
    }
  };

  input.addEventListener("input", () => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => filterItems(), 300);
  });
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    clearTimeout(timeoutId);
    filterItems();
  });
  form.addEventListener("reset", (event) => {
    event.preventDefault();
    clearTimeout(timeoutId);
    input.value = "";
    filterItems();
    input.focus();
  });
  const restoreQuery = () => {
    clearTimeout(timeoutId);
    input.value = new URL(window.location.href).searchParams.get("q") || "";
    filterItems(false);
  };
  window.addEventListener("popstate", restoreQuery);
  restoreQuery();
  form.hidden = false;
});
