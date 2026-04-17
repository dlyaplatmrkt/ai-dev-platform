const API = 'http://localhost:8000';
let currentProject = null;

// Tab navigation
document.querySelectorAll('.nav-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
    if (btn.dataset.tab === 'projects') loadProjects();
  });
});

// Generate
document.getElementById('generateBtn').addEventListener('click', async () => {
  const task = document.getElementById('taskInput').value.trim();
  const projectName = document.getElementById('projectName').value.trim();
  const template = document.getElementById('template').value;

  if (!task || !projectName) {
    alert('Please fill in Project Name and Task Description');
    return;
  }

  const btn = document.getElementById('generateBtn');
  btn.disabled = true;
  document.getElementById('generatingStatus').classList.remove('hidden');
  document.getElementById('resultSection').classList.add('hidden');

  try {
    const res = await fetch(`${API}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task, project_name: projectName, template })
    });
    const data = await res.json();

    currentProject = projectName;
    showResult(data);
  } catch (e) {
    alert('Error: ' + e.message);
  } finally {
    btn.disabled = false;
    document.getElementById('generatingStatus').classList.add('hidden');
  }
});

function showResult(data) {
  document.getElementById('resultSection').classList.remove('hidden');
  document.getElementById('planText').textContent = data.plan || '';

  const filesList = document.getElementById('filesList');
  filesList.innerHTML = '';

  (data.files || []).forEach(file => {
    const item = document.createElement('div');
    item.className = 'file-item';

    const header = document.createElement('div');
    header.className = 'file-header';
    header.innerHTML = `<span>${file.path}</span><span>+</span>`;

    const content = document.createElement('div');
    content.className = 'file-content';
    const pre = document.createElement('pre');
    pre.textContent = file.content;
    content.appendChild(pre);

    header.addEventListener('click', () => {
      content.classList.toggle('open');
      header.querySelector('span:last-child').textContent =
        content.classList.contains('open') ? '-' : '+';
    });

    item.appendChild(header);
    item.appendChild(content);
    filesList.appendChild(item);
  });
}

// Preview
document.getElementById('previewBtn').addEventListener('click', async () => {
  if (!currentProject) return;
  try {
    const res = await fetch(`${API}/api/projects/${currentProject}/preview`);
    const data = await res.json();
    const url = data.preview_url;

    document.getElementById('previewUrl').textContent = url;
    document.getElementById('previewIframe').src = url;
    document.getElementById('previewFrame').classList.remove('hidden');
    document.getElementById('previewBtn').style.display = 'none';
    document.getElementById('stopPreviewBtn').style.display = '';
  } catch (e) {
    alert('Preview error: ' + e.message);
  }
});

document.getElementById('stopPreviewBtn').addEventListener('click', async () => {
  if (!currentProject) return;
  await fetch(`${API}/api/projects/${currentProject}/stop`, { method: 'POST' });
  document.getElementById('previewFrame').classList.add('hidden');
  document.getElementById('previewBtn').style.display = '';
  document.getElementById('stopPreviewBtn').style.display = 'none';
});

document.getElementById('openPreviewBtn').addEventListener('click', () => {
  const url = document.getElementById('previewIframe').src;
  if (url) window.open(url, '_blank');
});

// Projects
async function loadProjects() {
  try {
    const res = await fetch(`${API}/api/projects`);
    const data = await res.json();
    const grid = document.getElementById('projectsList');
    grid.innerHTML = '';

    if (!data.projects || data.projects.length === 0) {
      grid.innerHTML = '<p style="color:#8b949e">No projects yet. Generate one!</p>';
      return;
    }

    data.projects.forEach(p => {
      const card = document.createElement('div');
      card.className = 'project-card';
      card.innerHTML = `
        <h3>${p.name}</h3>
        <p>${(p.files || []).length} files</p>
      `;
      card.addEventListener('click', () => {
        currentProject = p.name;
        document.getElementById('projectName').value = p.name;
        document.querySelector('[data-tab="generate"]').click();
      });
      grid.appendChild(card);
    });
  } catch (e) {
    console.error(e);
  }
}

document.getElementById('refreshProjectsBtn').addEventListener('click', loadProjects);

// GitHub Push
document.getElementById('pushBtn').addEventListener('click', async () => {
  const projectName = document.getElementById('ghProjectName').value.trim();
  const repoUrl = document.getElementById('ghRepoUrl').value.trim();
  const token = document.getElementById('ghToken').value.trim();
  const commitMsg = document.getElementById('ghCommitMsg').value.trim();

  if (!projectName || !repoUrl || !token) {
    alert('Please fill all fields');
    return;
  }

  const statusEl = document.getElementById('pushStatus');
  statusEl.className = 'status-msg';
  statusEl.textContent = 'Pushing...';
  statusEl.classList.remove('hidden');

  try {
    const res = await fetch(`${API}/api/github/push`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        project_name: projectName,
        repo_url: repoUrl,
        token,
        commit_message: commitMsg
      })
    });
    const data = await res.json();

    if (data.status === 'ok') {
      statusEl.classList.add('success');
      statusEl.textContent = 'Pushed successfully!';
    } else {
      statusEl.classList.add('error');
      statusEl.textContent = 'Error: ' + data.message;
    }
  } catch (e) {
    statusEl.classList.add('error');
    statusEl.textContent = 'Error: ' + e.message;
  }
});

// Index Repo
document.getElementById('indexBtn').addEventListener('click', async () => {
  const repoUrl = document.getElementById('indexRepoUrl').value.trim();
  const token = document.getElementById('indexToken').value.trim();

  if (!repoUrl) {
    alert('Please enter a Repo URL');
    return;
  }

  const statusEl = document.getElementById('indexStatus');
  statusEl.className = 'status-msg';
  statusEl.textContent = 'Indexing... This may take a few minutes.';
  statusEl.classList.remove('hidden');

  try {
    const res = await fetch(`${API}/api/index`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repo_url: repoUrl, token: token || null })
    });
    const data = await res.json();

    if (data.status === 'ok') {
      statusEl.classList.add('success');
      statusEl.textContent = `Indexed ${data.indexed} chunks successfully!`;
    } else {
      statusEl.classList.add('error');
      statusEl.textContent = 'Error: ' + data.message;
    }
  } catch (e) {
    statusEl.classList.add('error');
    statusEl.textContent = 'Error: ' + e.message;
  }
});
