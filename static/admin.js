async function fetchJSON(url) {
  const res = await fetch(url);
  return res.json();
}

function renderKpis(kpis) {
  const labels = {
    merchant_count: '商家总数',
    community_count: '社群总数',
    post_count: '帖子总数',
    avg_community_members: '社群平均人数',
  };
  const grid = document.getElementById('kpiGrid');
  grid.innerHTML = Object.entries(kpis)
    .map(([k, v]) => `<div class="kpi-card"><div>${labels[k]}</div><h3>${v}</h3></div>`)
    .join('');
}

function renderCategories(categories) {
  const list = document.getElementById('categoryStats');
  const entries = Object.entries(categories);
  list.innerHTML = entries.length
    ? entries.map(([name, count]) => `<li>${name}: ${count}</li>`).join('')
    : '<li>暂无商家数据</li>';
}

function renderTopCommunities(communities) {
  const list = document.getElementById('topCommunities');
  list.innerHTML = communities.length
    ? communities.map(c => `<li>#${c.community_id} ${c.community_name} - ${c.members} 人</li>`).join('')
    : '<li>暂无社群数据</li>';
}

async function loadAnalytics() {
  const data = await fetchJSON('/api/admin/analytics');
  renderKpis(data.kpis);
  renderCategories(data.merchant_categories);
  renderTopCommunities(data.top_communities);
}

loadAnalytics();
