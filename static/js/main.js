/* InvoiceFlow — Main JS */

document.addEventListener('DOMContentLoaded', () => {

  // ── Sidebar Toggle ─────────────────────────────────────────
  const sidebar = document.getElementById('sidebar');
  const toggle = document.getElementById('sidebarToggle');
  const mainWrapper = document.getElementById('mainWrapper');

  if (toggle && sidebar) {
    // Create overlay
    const overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    document.body.appendChild(overlay);

    toggle.addEventListener('click', () => {
      sidebar.classList.toggle('open');
      overlay.classList.toggle('show');
    });

    overlay.addEventListener('click', () => {
      sidebar.classList.remove('open');
      overlay.classList.remove('show');
    });
  }

  // ── Auto-dismiss alerts after 5s ──────────────────────────
  document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      bsAlert?.close();
    }, 5000);
  });

  // ── Confirm delete forms ───────────────────────────────────
  // Already handled inline with onsubmit, but catch any missed ones
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', (e) => {
      if (!confirm(el.dataset.confirm)) e.preventDefault();
    });
  });

  // ── Table row click to navigate ────────────────────────────
  document.querySelectorAll('[data-href]').forEach(row => {
    row.style.cursor = 'pointer';
    row.addEventListener('click', () => {
      window.location.href = row.dataset.href;
    });
  });

  // ── Format currency inputs ─────────────────────────────────
  document.querySelectorAll('input[data-format="currency"]').forEach(input => {
    input.addEventListener('blur', () => {
      const val = parseFloat(input.value);
      if (!isNaN(val)) input.value = val.toFixed(2);
    });
  });

  // ── Tooltip init ───────────────────────────────────────────
  const tooltipEls = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltipEls.forEach(el => new bootstrap.Tooltip(el));

});
