/* ============================================
   OFFSIDE — main.js
   Simple hash-based router + renderers.
   Routes:
     #/                -> home (badge wall)
     #/team/<slug>      -> team squad page
     #/icons            -> icons/legends gallery
   ============================================ */

const app = document.getElementById('app');

const POSITION_GROUPS = [
  { label: 'Goalkeepers', positions: ['GK'] },
  { label: 'Defenders', positions: ['RB', 'CB', 'LB'] },
  { label: 'Midfielders', positions: ['CDM', 'CM', 'CAM', 'RM', 'LM'] },
  { label: 'Forwards', positions: ['RW', 'LW', 'ST'] },
];

let teamsData = null;
let iconsData = null;

function slugify(name) {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');
}

async function loadTeams() {
  if (teamsData) return teamsData;
  const res = await fetch('data/teams.json');
  const json = await res.json();
  teamsData = json.teams || [];
  return teamsData;
}

async function loadIcons() {
  if (iconsData) return iconsData;
  try {
    const res = await fetch('data/icons.json');
    const json = await res.json();
    iconsData = json.icons || [];
  } catch (e) {
    iconsData = [];
  }
  return iconsData;
}

async function loadSponsors() {
  const row = document.getElementById('sponsor-row');
  try {
    const res = await fetch('data/sponsors.json');
    const json = await res.json();
    const sponsors = json.sponsors || [];
    if (sponsors.length === 0) return;
    row.innerHTML = sponsors
      .map(s => `<img src="assets/sponsors/${encodeURIComponent(s.image)}" alt="${escapeHtml(s.name)}">`)
      .join('');
  } catch (e) {
    // no sponsors.json yet — footer just stays empty, that's fine
  }
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str ?? '';
  return div.innerHTML;
}

/* ---------- Renderers ---------- */

async function renderHome() {
  const teams = await loadTeams();

  app.innerHTML = `
    <section class="hero">
      <span class="hero-eyebrow">Global Football League</span>
      <h1 class="hero-title">24 clubs. One league.</h1>
      <p class="hero-sub">Pick a club to view its squad, or step into the Icons gallery to see the legends of the game.</p>
    </section>
    <p class="section-label">Clubs</p>
    <div class="badge-wall">
      ${teams.map(t => `
        <a class="badge-tile" href="#/team/${slugify(t.name)}">
          <img src="assets/team_logos/${encodeURIComponent(t.logo)}" alt="${escapeHtml(t.name)} badge" loading="lazy">
          <span>${escapeHtml(t.name)}</span>
        </a>
      `).join('')}
    </div>
  `;
}

async function renderTeam(slug) {
  const teams = await loadTeams();
  const team = teams.find(t => slugify(t.name) === slug);

  if (!team) {
    app.innerHTML = `<div class="empty-state">No club found for this link. <a href="#/">Back to clubs</a>.</div>`;
    return;
  }

  const groupsHtml = POSITION_GROUPS.map(group => {
    const players = team.players.filter(p => group.positions.includes(p.position));
    if (players.length === 0) return '';
    return `
      <div class="position-group">
        <p class="section-label">${group.label}</p>
        <div class="player-grid">
          ${players.map(p => renderPlayerCard(team.name, p)).join('')}
        </div>
      </div>
    `;
  }).join('');

  app.innerHTML = `
    <div class="team-header">
      <img src="assets/team_logos/${encodeURIComponent(team.logo)}" alt="${escapeHtml(team.name)} badge">
      <div>
        <h1>${escapeHtml(team.name)}</h1>
        ${team.manager ? `<p class="manager">Manager: ${escapeHtml(team.manager)}</p>` : ''}
      </div>
    </div>
    ${groupsHtml}
    <a class="back-link" href="#/">&larr; All clubs</a>
  `;
}

function renderPlayerCard(teamName, player) {
  if (!player.image) {
    // Data exists but the image hasn't been prepared/validated yet.
    return `
      <div class="player-card">
        <div class="player-img-wrap"><span class="empty-state" style="border:none;padding:0;font-size:0.7rem;">No image yet</span></div>
        <div class="player-meta">
          <p class="player-name">${escapeHtml(player.name)}</p>
          <span class="player-position">${escapeHtml(player.position)}</span>
        </div>
      </div>
    `;
  }
  const src = `assets/player_cards/${encodeURIComponent(teamName)}/${encodeURIComponent(player.image)}`;
  return `
    <div class="player-card">
      <div class="player-img-wrap">
        <img src="${src}" alt="${escapeHtml(player.name)}" loading="lazy">
      </div>
      <div class="player-meta">
        <p class="player-name">${escapeHtml(player.name)}</p>
        <span class="player-position">${escapeHtml(player.position)}</span>
      </div>
    </div>
  `;
}

async function renderIcons() {
  const icons = await loadIcons();

  if (icons.length === 0) {
    app.innerHTML = `
      <section class="hero">
        <span class="hero-eyebrow">Legends</span>
        <h1 class="hero-title">Icons</h1>
      </section>
      <div class="empty-state">
        No icons added yet. Once icon images are in <code>assets/icons/</code> and listed in <code>data/icons.json</code>, they'll appear here.
      </div>
    `;
    return;
  }

  app.innerHTML = `
    <section class="hero">
      <span class="hero-eyebrow">Legends</span>
      <h1 class="hero-title">Icons</h1>
    </section>
    <div class="icons-grid">
      ${icons.map(i => `
        <div class="player-card">
          <div class="player-img-wrap">
            <img src="assets/icons/${encodeURIComponent(i.image)}" alt="${escapeHtml(i.name)}" loading="lazy">
          </div>
          <div class="player-meta">
            <p class="player-name">${escapeHtml(i.name)}</p>
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

async function loadVersion() {
  const tag = document.getElementById('version-tag');
  try {
    const res = await fetch('data/version.json');
    const json = await res.json();
    if (json.version) tag.textContent = `· v${json.version}`;
  } catch (e) {
    // no version.json yet — footer just omits the version, that's fine
  }
}

/* ---------- Router ---------- */

function setActiveNav(route) {
  document.querySelectorAll('.nav-link').forEach(link => {
    const isIcons = link.getAttribute('href') === '#/icons';
    link.classList.toggle('active', (isIcons && route.startsWith('#/icons')) || (!isIcons && (route === '#/' || route.startsWith('#/team'))));
  });
}

async function router() {
  const route = window.location.hash || '#/';
  setActiveNav(route);
  window.scrollTo(0, 0);

  if (route === '#/' || route === '') {
    await renderHome();
  } else if (route.startsWith('#/team/')) {
    const slug = route.replace('#/team/', '');
    await renderTeam(slug);
  } else if (route.startsWith('#/icons')) {
    await renderIcons();
  } else {
    app.innerHTML = `<div class="empty-state">Page not found. <a href="#/">Back to clubs</a>.</div>`;
  }
}

window.addEventListener('hashchange', router);
window.addEventListener('DOMContentLoaded', () => {
  router();
  loadSponsors();
  loadVersion();
});
