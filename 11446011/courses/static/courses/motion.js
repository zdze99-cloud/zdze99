/* 互動動畫:依序浮現的序號、數字跳動、按鈕漣漪與載入狀態、Toast 自動消失。
   全部是漸進增強;JavaScript 關掉時頁面一樣能正常使用。 */
(function () {
  "use strict";

  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var root = document.documentElement;

  // 開場動畫播完後記住,同一個分頁不再播
  if (root.classList.contains("intro")) {
    try { sessionStorage.setItem("introSeen", "1"); } catch (e) {}
    setTimeout(function () { root.classList.remove("intro"); }, reduce ? 0 : 3300);
  }

  // 1. 依序浮現:替同一層的兄弟元素標上 --i(最多 14,避免太慢)
  var groups = [
    ".page > *", ".grid > *", ".tbl tr", ".phasebar button", ".filters > *",
    ".sched > .blk", ".sched > .cell", ".bars i", ".center-page > div > *",
  ];
  groups.forEach(function (sel) {
    var seen = new Map();
    document.querySelectorAll(sel).forEach(function (el) {
      var parent = el.parentElement;
      var n = seen.get(parent) || 0;
      seen.set(parent, n + 1);
      var cap = sel === ".bars i" || sel === ".sched > .cell" ? 999 : 14;
      if (!el.style.getPropertyValue("--i")) el.style.setProperty("--i", Math.min(n, cap));
    });
  });
  // 進度條沒有自己的 --i,會繼承所在列或卡片的序號(CSS 變數會往下繼承)

  // 2. 統計數字從 0 跳到目標值(保留 %、小數)
  function countUp(el) {
    var m = el.textContent.trim().match(/^(\d+(?:\.\d+)?)(.*)$/);
    if (!m || reduce) return;
    var target = parseFloat(m[1]), suffix = m[2], decimals = (m[1].split(".")[1] || "").length;
    var start = null, dur = 1100;
    el.textContent = (0).toFixed(decimals) + suffix;
    function step(t) {
      if (start === null) start = t;
      var p = Math.min(1, (t - start) / dur), eased = 1 - Math.pow(1 - p, 4);
      el.textContent = (target * eased).toFixed(decimals) + suffix;
      if (p < 1) requestAnimationFrame(step);
    }
    setTimeout(function () { requestAnimationFrame(step); }, root.classList.contains("intro") ? 2500 : 250);
  }
  document.querySelectorAll(".stat b").forEach(countUp);

  // 3. 按鈕漣漪
  document.addEventListener("pointerdown", function (e) {
    var btn = e.target.closest(".btn");
    if (!btn || reduce) return;
    var r = btn.getBoundingClientRect(), dot = document.createElement("span");
    dot.className = "ripple";
    dot.style.left = e.clientX - r.left + "px";
    dot.style.top = e.clientY - r.top + "px";
    btn.appendChild(dot);
    setTimeout(function () { dot.remove(); }, 650);
  });

  // 4. 送出表單:按鈕顯示載入中;收藏星號先彈跳再送出
  document.addEventListener("submit", function (e) {
    var form = e.target, btn = e.submitter;
    if (btn && btn.classList.contains("star") && !reduce && !form.dataset.popped) {
      e.preventDefault();
      form.dataset.popped = "1";
      btn.textContent = btn.textContent.trim() === "★" ? "☆" : "★";
      btn.classList.add("pop");
      setTimeout(function () { form.requestSubmit ? form.requestSubmit(btn) : form.submit(); }, 380);
      return;
    }
    if (btn && btn.classList.contains("btn") && form.method.toLowerCase() === "post") {
      // 等瀏覽器把按鈕的 name/value 放進表單後再改樣式
      setTimeout(function () { btn.classList.add("is-loading"); }, 0);
    }
  });
  // 從上一頁返回時(bfcache)清掉載入狀態
  window.addEventListener("pageshow", function () {
    document.querySelectorAll(".is-loading").forEach(function (b) { b.classList.remove("is-loading"); });
    document.querySelectorAll("form[data-popped]").forEach(function (f) { delete f.dataset.popped; });
  });

  // 篩選表單:勾選框或下拉選單一改變就直接查詢(關鍵字仍需按 Enter 或「查詢」)
  document.querySelectorAll("form.filters").forEach(function (form) {
    form.addEventListener("change", function (e) {
      var t = e.target;
      if (t.type === "checkbox" || t.tagName === "SELECT") {
        form.requestSubmit ? form.requestSubmit() : form.submit();
      }
    });
  });

  // 5. Toast:4 秒後滑出,點一下立即關閉,滑鼠停留時暫停計時
  document.querySelectorAll(".toast").forEach(function (t) {
    var timer = t.querySelector(".toast-timer"), left = 4000, started = Date.now(), handle;
    function leave() {
      t.classList.add("leaving");
      t.addEventListener("animationend", function () { t.remove(); }, { once: true });
      if (reduce) t.remove();
    }
    function arm() { started = Date.now(); handle = setTimeout(leave, left); }
    t.addEventListener("click", leave);
    t.addEventListener("mouseenter", function () {
      clearTimeout(handle); left -= Date.now() - started;
      if (timer) timer.style.animationPlayState = "paused";
    });
    t.addEventListener("mouseleave", function () {
      if (timer) timer.style.animationPlayState = "running";
      arm();
    });
    arm();
  });
})();

/* 深色模式:記住選擇;沒選過就跟系統設定。切換時新主題從下方升起覆蓋畫面。 */
(function () {
  "use strict";
  var root = document.documentElement;
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var DARK_BG = "#151413", LIGHT_BG = "#f3f2f2";

  function apply(theme) {
    root.setAttribute("data-theme", theme);
    try { localStorage.setItem("theme", theme); } catch (e) {}
    document.querySelectorAll(".theme-toggle").forEach(function (b) {
      b.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
      b.setAttribute("aria-label", theme === "dark" ? "切換為淺色模式" : "切換為深色模式");
      b.title = b.getAttribute("aria-label");
    });
  }
  apply(root.getAttribute("data-theme") || "light");

  var busy = false;
  function toggle() {
    if (busy) return;
    var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    if (reduce) return apply(next);
    busy = true;
    if (document.startViewTransition) {
      var t = document.startViewTransition(function () { apply(next); });
      t.finished.then(function () { busy = false; }, function () { busy = false; });
      return;
    }
    var curtain = document.createElement("div");
    curtain.className = "theme-curtain";
    curtain.style.background = next === "dark" ? DARK_BG : LIGHT_BG;
    document.body.appendChild(curtain);
    curtain.getBoundingClientRect();
    curtain.classList.add("up");
    curtain.addEventListener("transitionend", function () {
      apply(next);
      curtain.classList.add("fade");
      setTimeout(function () { curtain.remove(); busy = false; }, 320);
    }, { once: true });
  }
  document.addEventListener("click", function (e) {
    if (e.target.closest(".theme-toggle")) toggle();
  });
})();
