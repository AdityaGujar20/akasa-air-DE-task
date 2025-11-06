// Smooth scroll helper
function scrollToEl(id) {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  
  // Simple status text helper
  function setStatus(id, msg, ok = true) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = msg || "";
    el.className = `text-center text-sm mt-3 ${ok ? "text-emerald-600" : "text-rose-600"}`;
  }
  
  // Current charts (so we can destroy before re-render)
  let charts = {
    repeat: null,
    monthly: null,
    regional: null,
    top: null
  };
  
  // Build endpoint prefix based on mode selector
  function baseKpi() {
    const mode = document.getElementById("sourceMode").value;
    return mode === "db" ? "/kpi/db" : "/kpi/memory";
  }
  
  // Render charts from datasets
  function renderCharts({ repeat, monthly, regional, top }) {
    // Destroy old charts if exist
    Object.keys(charts).forEach(k => {
      if (charts[k]) {
        charts[k].destroy();
        charts[k] = null;
      }
    });
  
    // Repeat Customers (bar)
    charts.repeat = new Chart(document.getElementById("chartRepeat"), {
      type: "bar",
      data: {
        labels: repeat.map(r => r.customer_id),
        datasets: [{
          label: "Orders",
          data: repeat.map(r => r.order_count),
        }]
      },
      options: { responsive: true, maintainAspectRatio: false }
    });
  
    // Monthly Trends (line)
    charts.monthly = new Chart(document.getElementById("chartMonthly"), {
      type: "line",
      data: {
        labels: monthly.map(m => m.month),
        datasets: [{
          label: "Orders",
          data: monthly.map(m => m.orders_count || m.orders || 0),
          tension: 0.3
        }]
      },
      options: { responsive: true, maintainAspectRatio: false }
    });
  
    // Regional Revenue (doughnut)
    charts.regional = new Chart(document.getElementById("chartRegional"), {
      type: "doughnut",
      data: {
        labels: regional.map(r => r.region || "Unknown"),
        datasets: [{
          data: regional.map(r => r.revenue || 0),
        }]
      },
      options: { responsive: true, maintainAspectRatio: false }
    });
  
    // Top Customers (horizontal bar)
    charts.top = new Chart(document.getElementById("chartTop"), {
      type: "bar",
      data: {
        labels: top.map(t => t.customer_id),
        datasets: [{
          label: "Total Spend",
          data: top.map(t => t.total_spend || t.total_amount || 0),
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: "y"
      }
    });
  }
  
  // Fetch KPI data and render
  async function refreshKpis() {
    const base = baseKpi();
    try {
      const [repeat, monthly, regional, top] = await Promise.all([
        fetch(`${base}/repeat-customers`).then(r => r.json()),
        fetch(`${base}/monthly-order-trends`).then(r => r.json()),
        fetch(`${base}/regional-revenue`).then(r => r.json()),
        fetch(`${base}/top-customers?limit=10`).then(r => r.json())
      ]);
  
      renderCharts({ repeat, monthly, regional, top });
      setStatus("statusKpi", "KPI dashboard refreshed.", true);
    } catch (err) {
      console.error(err);
      setStatus("statusKpi", "Failed to load KPIs.", false);
    }
  }
  
  // Upload both files (if provided)
  async function uploadFiles() {
    const cust = document.getElementById("customersFile").files[0];
    const orders = document.getElementById("ordersFile").files[0];
  
    if (!cust && !orders) {
      setStatus("statusUpload", "Please choose at least one file to upload.", false);
      return;
    }
  
    setStatus("statusUpload", "Uploading...", true);
  
    try {
      if (cust) {
        const fd = new FormData();
        fd.append("file", cust);
        await fetch("/upload/customers", { method: "POST", body: fd }).then(r => r.json());
      }
      if (orders) {
        const fd = new FormData();
        fd.append("file", orders);
        await fetch("/upload/orders", { method: "POST", body: fd }).then(r => r.json());
      }
  
      setStatus("statusUpload", "Upload successful.");
      scrollToEl("section-clean");
    } catch (err) {
      console.error(err);
      setStatus("statusUpload", "Upload failed.", false);
    }
  }
  
  // Run cleaning pipeline, then auto-scroll
  async function runClean() {
    setStatus("statusClean", "Cleaning in progress...");
    try {
      const res = await fetch("/clean", { method: "POST" }).then(r => r.json());
      setStatus("statusClean", res.message || "Cleaning completed.");
      scrollToEl("section-load");
      await refreshKpis(); // refresh KPIs from cleaned CSVs
    } catch (err) {
      console.error(err);
      setStatus("statusClean", "Cleaning failed.", false);
    }
  }
  
  // Load into DB, then auto-scroll and refresh KPIs (DB mode)
  async function runLoad() {
    setStatus("statusLoad", "Loading into DB...");
    try {
      const res = await fetch("/db/load", { method: "POST" }).then(r => r.json());
      setStatus("statusLoad", res.message || "DB load completed.");
      scrollToEl("section-kpi");
      await refreshKpis(); // refresh charts (source depends on selector)
    } catch (err) {
      console.error(err);
      setStatus("statusLoad", "DB load failed.", false);
    }
  }
  
  // Wire up events
  document.getElementById("btnUpload").addEventListener("click", uploadFiles);
  document.getElementById("btnClean").addEventListener("click", runClean);
  document.getElementById("btnLoad").addEventListener("click", runLoad);
  document.getElementById("sourceMode").addEventListener("change", refreshKpis);
  
  // Initial load (in-memory by default)
  refreshKpis();
  