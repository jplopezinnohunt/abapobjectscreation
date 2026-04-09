// Treasury Operations Companion — JavaScript
// Pure vanilla JS, no external dependencies

(function () {
  'use strict';

  // ── Tab Navigation ──────────────────────────────────────────────────
  function initTabs() {
    var links = document.querySelectorAll('.nav-link');
    links.forEach(function (link) {
      link.addEventListener('click', function (e) {
        e.preventDefault();
        var targetId = link.getAttribute('data-tab');
        if (!targetId) return;

        // Deactivate all links
        links.forEach(function (l) { l.classList.remove('active'); });
        // Deactivate all tab content panels
        document.querySelectorAll('.tab-content').forEach(function (tc) {
          tc.classList.remove('active');
          tc.style.display = 'none';
        });

        // Activate clicked link and its target panel
        link.classList.add('active');
        var panel = document.getElementById(targetId);
        if (panel) {
          panel.classList.add('active');
          panel.style.display = 'block';
        }
      });
    });
  }

  // ── Collapsible Sections ────────────────────────────────────────────
  function initCollapsibles() {
    document.querySelectorAll('.collapsible-header').forEach(function (header) {
      header.style.cursor = 'pointer';
      header.addEventListener('click', function () {
        header.classList.toggle('collapsed');
        var body = header.nextElementSibling;
        if (body) {
          body.classList.toggle('hidden');
        }
      });
    });
  }

  // ── Table Search / Filter ───────────────────────────────────────────
  function initSearchFilters() {
    document.querySelectorAll('.table-search').forEach(function (input) {
      var tableId = input.getAttribute('data-table');
      if (!tableId) return;

      input.addEventListener('input', function () {
        var term = input.value.toLowerCase().trim();
        var table = document.getElementById(tableId);
        if (!table) return;

        var rows = table.querySelectorAll('tbody tr');
        var visibleCount = 0;
        rows.forEach(function (row) {
          var text = row.textContent.toLowerCase();
          var match = !term || text.indexOf(term) !== -1;
          row.style.display = match ? '' : 'none';
          if (match) visibleCount++;
        });

        // Update result counter if one exists
        var counter = input.parentElement &&
          input.parentElement.querySelector('.search-count');
        if (counter) {
          counter.textContent = visibleCount + ' / ' + rows.length + ' rows';
        }
      });
    });
  }

  // ── Print Single Tab ────────────────────────────────────────────────
  function initPrint() {
    document.querySelectorAll('.btn-print').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var tabId = btn.getAttribute('data-print-tab');
        var panel = tabId ? document.getElementById(tabId) : null;

        // Fallback: print active tab
        if (!panel) {
          panel = document.querySelector('.tab-content.active');
        }
        if (!panel) {
          window.print();
          return;
        }

        // Build a print-friendly window with the same styles
        var printWin = window.open('', '_blank', 'width=900,height=700');
        if (!printWin) {
          // Popup blocked — fall back to full-page print
          window.print();
          return;
        }

        var styles = '';
        document.querySelectorAll('style').forEach(function (s) {
          styles += s.outerHTML;
        });
        document.querySelectorAll('link[rel="stylesheet"]').forEach(function (l) {
          styles += l.outerHTML;
        });

        var title = document.title || 'Treasury Operations Companion';
        var tabTitle = panel.querySelector('h2, h3');
        if (tabTitle) {
          title += ' — ' + tabTitle.textContent.trim();
        }

        printWin.document.write(
          '<!DOCTYPE html><html><head><meta charset="UTF-8">' +
          '<title>' + title + '</title>' +
          styles +
          '<style>body{padding:20px;font-size:12px}' +
          '.tab-content{display:block!important}' +
          '.nav-link,.btn-print,.table-search,.search-count{display:none!important}' +
          '@media print{body{padding:0}}</style>' +
          '</head><body>' +
          panel.innerHTML +
          '</body></html>'
        );
        printWin.document.close();

        // Give styles a moment to load before triggering print
        setTimeout(function () {
          printWin.focus();
          printWin.print();
        }, 400);
      });
    });
  }

  // ── Smooth Scroll for Anchor Links ──────────────────────────────────
  function initAnchorScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(function (a) {
      // Skip nav-links — they are handled by the tab system
      if (a.classList.contains('nav-link')) return;
      a.addEventListener('click', function (e) {
        var target = document.querySelector(a.getAttribute('href'));
        if (target) {
          e.preventDefault();
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      });
    });
  }

  // ── Tooltip / Hover Info ────────────────────────────────────────────
  function initTooltips() {
    document.querySelectorAll('[data-tooltip]').forEach(function (el) {
      el.style.position = 'relative';
      el.addEventListener('mouseenter', function () {
        var tip = document.createElement('span');
        tip.className = 'js-tooltip';
        tip.textContent = el.getAttribute('data-tooltip');
        tip.style.cssText =
          'position:absolute;bottom:110%;left:50%;transform:translateX(-50%);' +
          'background:#1a1a2e;color:#fff;padding:4px 10px;border-radius:4px;' +
          'font-size:12px;white-space:nowrap;z-index:9999;pointer-events:none;';
        el.appendChild(tip);
      });
      el.addEventListener('mouseleave', function () {
        var tip = el.querySelector('.js-tooltip');
        if (tip) tip.remove();
      });
    });
  }

  // ── Show First Tab on Load ──────────────────────────────────────────
  function showFirstTab() {
    var firstLink = document.querySelector('.nav-link');
    if (firstLink) {
      firstLink.click();
    } else {
      // No nav links — just show the first tab-content
      var first = document.querySelector('.tab-content');
      if (first) {
        first.classList.add('active');
        first.style.display = 'block';
      }
    }
  }

  // ── DOMContentLoaded Bootstrap ──────────────────────────────────────
  document.addEventListener('DOMContentLoaded', function () {
    initTabs();
    initCollapsibles();
    initSearchFilters();
    initPrint();
    initAnchorScroll();
    initTooltips();
    showFirstTab();
  });
})();
