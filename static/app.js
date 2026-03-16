async function fetchJSON(url, options = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.error || '请求失败');
  }
  return data;
}

async function loadMerchants() {
  const merchants = await fetchJSON('/api/merchants');
  const list = document.getElementById('merchantList');
  list.innerHTML = merchants
    .map(m => `<li>#${m.id} ${m.name} | ${m.category} | ${m.city} | 联系人：${m.contact}</li>`)
    .join('');
}

async function loadCommunities() {
  const communities = await fetchJSON('/api/communities');
  const posts = await fetchJSON('/api/posts');
  const list = document.getElementById('communityList');
  list.innerHTML = communities.map(c => {
    const cPosts = posts.filter(p => p.community_id === c.id).length;
    return `<li>#${c.id} ${c.name}（创建者：${c.owner}）<br/>成员数：${c.members.length}，帖子数：${cPosts}<br/>简介：${c.description}</li>`;
  }).join('');
}

document.getElementById('merchantForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const formData = new FormData(e.target);
  const body = Object.fromEntries(formData.entries());
  await fetchJSON('/api/merchants', { method: 'POST', body: JSON.stringify(body) });
  e.target.reset();
  await loadMerchants();
});

document.getElementById('communityForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const formData = new FormData(e.target);
  const body = Object.fromEntries(formData.entries());
  await fetchJSON('/api/communities', { method: 'POST', body: JSON.stringify(body) });
  e.target.reset();
  await loadCommunities();
});

document.getElementById('joinBtn').addEventListener('click', async () => {
  const communityId = document.getElementById('joinCommunityId').value;
  const username = document.getElementById('joinUsername').value;
  if (!communityId || !username) return;
  await fetchJSON(`/api/communities/${communityId}/join`, {
    method: 'POST',
    body: JSON.stringify({ username }),
  });
  await loadCommunities();
});

document.getElementById('postBtn').addEventListener('click', async () => {
  const community_id = document.getElementById('postCommunityId').value;
  const author = document.getElementById('postAuthor').value;
  const content = document.getElementById('postContent').value;
  if (!community_id || !author || !content) return;
  await fetchJSON('/api/posts', {
    method: 'POST',
    body: JSON.stringify({ community_id, author, content }),
  });
  await loadCommunities();
});

loadMerchants();
loadCommunities();
