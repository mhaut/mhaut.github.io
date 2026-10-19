const assert = require("node:assert/strict");
const { existsSync, readFileSync } = require("node:fs");
const { join } = require("node:path");
const { test } = require("node:test");
const vm = require("node:vm");

const script = readFileSync(join(__dirname, "../assets/js/bibsearch.js"), "utf8");
const records = [
  { publicationTitle: "Hyperspectral image analysis", publicationAuthors: "Haut, Juan M. and García-Flores, María B.", publicationYear: "2026" },
  { publicationTitle: "Remote sensing retrieval", publicationAuthors: "Paoletti, Mercedes E. and Haut, Juan M.", publicationYear: "2025" },
  { publicationTitle: "Network intrusion detection", publicationAuthors: "Franco-Valiente, José M.", publicationYear: "2026" },
];

function harness(url = "https://example.org/publications/#journals", data = records, hasForm = true) {
  const callbacks = new Map();
  const timers = new Map();
  let timerId = 0;
  const element = (id) => ({
    hidden: false,
    value: "",
    textContent: "",
    addEventListener: (event, callback) => callbacks.set(`${id}:${event}`, callback),
  });
  const input = element("input");
  const clear = element("clear");
  const form = element("form");
  form.hidden = true;
  form.querySelector = () => clear;
  input.focus = () => (input.focused = true);
  const status = element("status");
  const empty = element("empty");
  const items = data.map((dataset) => {
    const item = { hidden: false };
    return { dataset, item, closest: () => item };
  });
  const elements = { "bibsearch-form": hasForm ? form : null, bibsearch: input, "bibsearch-status": status, "bibsearch-empty": empty };
  const document = {
    getElementById: (id) => elements[id],
    querySelectorAll: (selector) => {
      assert.equal(selector, "#publication-list [data-publication-key]");
      return items;
    },
    addEventListener: (event, callback) => callbacks.set(`document:${event}`, callback),
  };
  const window = {
    location: { href: url },
    history: {
      state: { preserved: true },
      replaceState(state, title, nextUrl) {
        assert.deepEqual(state, { preserved: true });
        window.location.href = nextUrl.toString();
      },
    },
    addEventListener: (event, callback) => callbacks.set(`window:${event}`, callback),
  };
  vm.runInNewContext(script, {
    document,
    window,
    URL,
    setTimeout(callback, delay) {
      assert.equal(typeof callback, "function");
      assert.equal(delay, 300);
      timers.set(++timerId, callback);
      return timerId;
    },
    clearTimeout: (id) => timers.delete(id),
  });
  callbacks.get("document:DOMContentLoaded")();
  const fire = (name) => callbacks.get(name)({ preventDefault() {} });
  return {
    input,
    form,
    status,
    empty,
    clear,
    window,
    timers,
    fire,
    visible: () => items.filter(({ item }) => !item.hidden).map(({ dataset }) => dataset.publicationTitle),
    search(value) {
      input.value = value;
      fire("input:input");
    },
    flush() {
      for (const [id, callback] of timers) {
        timers.delete(id);
        callback();
      }
    },
  };
}

test("section anchors do not become search terms", () => {
  for (const section of ["journals", "conferences", "national"]) {
    const page = harness(`https://example.org/publications/#${section}`);
    assert.equal(page.visible().length, 3);
    assert.equal(page.input.value, "");
    assert.equal(page.form.hidden, false);
    assert.equal(page.clear.disabled, true);
    assert.equal(page.status.textContent, "Showing all 3 publications.");
  }
});

test("shared query searches full metadata independently of publication anchors", () => {
  const page = harness("https://example.org/publications/?q=HYPERSPECTRAL+garcia+2026#paper-key");
  assert.deepEqual(page.visible(), [records[0].publicationTitle]);
  assert.equal(page.status.textContent, "1 of 3 publications match your search.");
  assert.equal(new URL(page.window.location.href).hash, "#paper-key");
});

test("debounce waits and cancels earlier input", () => {
  const page = harness();
  page.search("retrieval");
  page.search("network");
  assert.equal(page.visible().length, 3);
  assert.equal(page.timers.size, 1);
  page.flush();
  assert.deepEqual(page.visible(), [records[2].publicationTitle]);
  assert.equal(new URL(page.window.location.href).searchParams.get("q"), "network");
});

test("button labels and citation badges do not create false matches", () => {
  const page = harness();
  page.search("BibTeX DOI scholar");
  page.flush();
  assert.deepEqual(page.visible(), []);
  assert.equal(page.empty.hidden, false);
  assert.equal(page.status.textContent, "0 of 3 publications match your search.");
});

test("clear restores every publication, keeps unrelated URL parameters and anchor", () => {
  const page = harness("https://example.org/publications/?source=cv&q=network#conferences");
  page.fire("form:reset");
  assert.equal(page.visible().length, 3);
  assert.equal(page.empty.hidden, true);
  assert.equal(page.input.focused, true);
  assert.equal(page.window.location.href, "https://example.org/publications/?source=cv#conferences");
});

test("submitting applies immediately and cancels the pending debounce", () => {
  const page = harness();
  page.search("2025");
  page.fire("form:submit");
  assert.equal(page.timers.size, 0);
  assert.deepEqual(page.visible(), [records[1].publicationTitle]);
});

test("back/forward restores query and cancels pending input", () => {
  const page = harness();
  page.search("network");
  page.window.location.href = "https://example.org/publications/?q=2025#national";
  page.fire("window:popstate");
  assert.equal(page.timers.size, 0);
  assert.equal(page.input.value, "2025");
  assert.deepEqual(page.visible(), [records[1].publicationTitle]);
});

test("empty bibliography reports zero results without throwing", () => {
  const page = harness(undefined, []);
  assert.equal(page.empty.hidden, false);
  assert.equal(page.status.textContent, "Showing all 0 publications.");
});

test("pages without publication search can load the script safely", () => {
  assert.doesNotThrow(() => harness(undefined, [], false));
});

const generatedIndex = join(__dirname, "../_site/assets/js/search-data.js");
test("generated global search registers each scientific reference and opens its anchor", { skip: !existsSync(generatedIndex) }, () => {
  const ninja = {};
  const window = { location: { origin: "https://example.org", href: "https://example.org/" } };
  class DOMParser {
    parseFromString(html) {
      const entries = Array.from(html.matchAll(/<span\b([^>]+)>/g), ([, attributes]) => {
        const dataset = {};
        for (const [, key, value] of attributes.matchAll(/data-publication-(key|title|authors|year)="([^"]*)"/g)) {
          dataset[`publication${key[0].toUpperCase()}${key.slice(1)}`] = value;
        }
        return { dataset };
      });
      return { querySelectorAll: () => entries };
    }
  }
  vm.runInNewContext(readFileSync(generatedIndex, "utf8"), {
    document: { querySelector: () => ninja },
    DOMParser,
    URL,
    window,
  });
  const actions = ninja.data.filter((action) => action.section === "Publications");
  const bibtex = readFileSync(join(__dirname, "../_bibliography/papers.bib"), "utf8");
  const keys = Array.from(bibtex.matchAll(/^@(?:article|inproceedings)\{([^,]+),/gm), ([, key]) => `publication-${key}`).sort();
  assert.deepEqual(Array.from(actions, (action) => action.id).sort(), keys);
  assert(actions.every((action) => action.description.includes("Haut")));
  assert(!ninja.data.some((action) => action.title === "a post that can be cited"));
  const paper = actions.find((action) => action.id === "publication-calle2026fastattention");
  paper.handler();
  assert.equal(window.location.href, "https://example.org/publications/#calle2026fastattention");
});
