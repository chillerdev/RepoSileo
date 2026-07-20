const baseUrl = new URL('./', location.href).href;
const clean = value => (value || '').replace(/<[^>]*>/g, '').trim();
const initial = value => clean(value).slice(0, 1).toUpperCase() || 'A';

document.querySelector('#repo-url').textContent = baseUrl;
document.querySelector('#add-sileo').href = `sileo://source/${baseUrl}`;
document.querySelector('#copy-url').addEventListener('click', async event => {
  await navigator.clipboard.writeText(baseUrl);
  event.currentTarget.textContent = 'Đã sao chép';
  setTimeout(() => event.currentTarget.textContent = 'Sao chép URL', 1500);
});

fetch(`packages.json?v=${Date.now()}`).then(response => {
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}).then(({repo, packages}) => {
  document.title = repo.name;
  document.querySelector('#repo-name').textContent = repo.name;
  document.querySelector('#repo-description').textContent = repo.description;
  document.querySelector('#count').textContent = `${packages.length} gói`;
  const grid = document.querySelector('#packages');
  if (!packages.length) {
    grid.innerHTML = '<p class="empty">Chưa có ứng dụng. Hãy thêm file .deb rồi chạy script cập nhật.</p>';
    return;
  }
  grid.replaceChildren(...packages.map(pkg => {
    const card = document.createElement(pkg.Depiction || pkg.Homepage ? 'a' : 'article');
    card.className = 'card';
    if (card.tagName === 'A') card.href = pkg.Depiction || pkg.Homepage;
    const name = pkg.Name || pkg.Package;
    card.innerHTML = `<div class="icon">${initial(name)}</div><div class="info"><h3></h3><code></code><p></p><div class="meta"><span></span><span></span></div></div>`;
    card.querySelector('h3').textContent = name;
    card.querySelector('code').textContent = pkg.Package;
    card.querySelector('p').textContent = (pkg.Description || 'Không có mô tả').split('\n')[0];
    const spans = card.querySelectorAll('.meta span');
    spans[0].textContent = `v${pkg.Version}`;
    spans[1].textContent = pkg.Architecture;
    return card;
  }));
}).catch(error => {
  document.querySelector('#packages').innerHTML = `<p class="empty">Không thể đọc packages.json: ${error.message}</p>`;
});
