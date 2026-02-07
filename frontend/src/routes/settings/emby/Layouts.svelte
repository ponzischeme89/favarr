<script>
  import { api } from '../../../api';

  export let serverId;

  let activeTab = 'users';
  let users = [];
  let usersLoading = false;
  let usersError = '';

  let templates = [];
  let templatesLoading = false;
  let templatesError = '';

  let activeUser = null;
  let layouts = {};
  let layoutDraft = {};
  let layoutUnsupported = [];
  let layoutLoading = false;
  let layoutError = '';
  let expandedPrefs = new Set();
  let pushing = false;

  let toast = '';
  let toastType = 'success';
  let toastTimer = null;

  let showTemplateModal = false;
  let templateFormMode = 'create';
  let templateForm = { name: '', description: '', jsonText: '' };
  let templateFormError = '';

  let showApplyModal = false;
  let applyTemplateId = '';
  let applyUserIds = new Set();
  let applyProgress = null;
  let applyStatus = {};

  let showPreviewModal = false;
  let previewTitle = '';
  let previewJson = '';

  let layoutClient = 'Emby Web';
  let layoutDeviceId = 'faveswitch';

  const layoutOrder = ['home', 'landingcategories', 'resume', 'suggestions', 'latest'];

  let lastServerId = null;
  $: if (serverId && serverId !== lastServerId) {
    lastServerId = serverId;
    resetState();
    loadUsers();
    loadTemplates();
  }

  $: orderedLayoutKeys = Object.keys(layoutDraft || {}).sort((a, b) => {
    const aIdx = layoutOrder.indexOf(a);
    const bIdx = layoutOrder.indexOf(b);
    if (aIdx === -1 && bIdx === -1) return a.localeCompare(b);
    if (aIdx === -1) return 1;
    if (bIdx === -1) return -1;
    return aIdx - bIdx;
  });

  function resetState() {
    users = [];
    templates = [];
    activeUser = null;
    layouts = {};
    layoutDraft = {};
    layoutUnsupported = [];
    layoutError = '';
    expandedPrefs = new Set();
  }

  function showToast(message, type = 'success') {
    toast = message;
    toastType = type;
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toast = '';
    }, 4000);
  }

  async function loadUsers() {
    if (!serverId) return;
    usersLoading = true;
    usersError = '';
    try {
      users = await api.getEmbyLayoutUsers(serverId);
    } catch (err) {
      usersError = err.message || 'Failed to load users';
    } finally {
      usersLoading = false;
    }
  }

  async function loadTemplates() {
    templatesLoading = true;
    templatesError = '';
    try {
      templates = await api.getEmbyLayoutTemplates();
    } catch (err) {
      templatesError = err.message || 'Failed to load templates';
    } finally {
      templatesLoading = false;
    }
  }

  async function viewLayout(user) {
    if (!user) return;
    activeUser = user;
    layoutLoading = true;
    layoutError = '';
    layoutUnsupported = [];
    try {
      const params = {};
      if (layoutClient && layoutClient.trim()) params.client = layoutClient.trim();
      if (layoutDeviceId && layoutDeviceId.trim()) params.deviceId = layoutDeviceId.trim();
      const res = await api.getEmbyLayouts(serverId, user.Id, params);
      const loaded = res.layouts || res || {};
      layoutUnsupported = res.unsupported || [];
      layouts = loaded;
      const nextDraft = {};
      Object.entries(loaded).forEach(([prefId, value]) => {
        nextDraft[prefId] = JSON.stringify(value ?? {}, null, 2);
      });
      layoutDraft = nextDraft;
      const initial = Object.keys(nextDraft).slice(0, 2);
      expandedPrefs = new Set(initial);
    } catch (err) {
      layoutError = err.message || 'Failed to load layouts';
    } finally {
      layoutLoading = false;
    }
  }

  function togglePref(prefId) {
    const next = new Set(expandedPrefs);
    if (next.has(prefId)) {
      next.delete(prefId);
    } else {
      next.add(prefId);
    }
    expandedPrefs = next;
  }

  function buildLayoutPayload() {
    const payload = {};
    for (const [prefId, raw] of Object.entries(layoutDraft)) {
      if (!raw || !raw.trim()) {
        payload[prefId] = {};
        continue;
      }
      try {
        payload[prefId] = JSON.parse(raw);
      } catch (err) {
        throw new Error(`Invalid JSON for "${prefId}"`);
      }
    }
    return payload;
  }

  async function pushToUser() {
    if (!activeUser) return;
    let payload;
    try {
      payload = buildLayoutPayload();
    } catch (err) {
      showToast(err.message, 'error');
      return;
    }
    pushing = true;
    try {
      const requestPayload = { layout: payload };
      if (layoutClient && layoutClient.trim()) requestPayload.client = layoutClient.trim();
      if (layoutDeviceId && layoutDeviceId.trim()) requestPayload.deviceId = layoutDeviceId.trim();
      await api.applyEmbyLayout(serverId, activeUser.Id, requestPayload);
      showToast('Layout pushed to user', 'success');
    } catch (err) {
      showToast(err.message || 'Failed to push layout', 'error');
    } finally {
      pushing = false;
    }
  }

  function openTemplateModal({ mode = 'create', name = '', description = '', jsonText = '' } = {}) {
    templateFormMode = mode;
    templateForm = { name, description, jsonText };
    templateFormError = '';
    showTemplateModal = true;
  }

  function openCreateTemplate() {
    openTemplateModal({
      mode: 'create',
      jsonText: JSON.stringify({ home: {} }, null, 2)
    });
  }

  function openSaveTemplateFromLayout() {
    try {
      const payload = buildLayoutPayload();
      openTemplateModal({
        mode: 'save',
        jsonText: JSON.stringify(payload, null, 2)
      });
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  function openCloneTemplateFromUser() {
    if (!activeUser) return;
    try {
      const payload = buildLayoutPayload();
      openTemplateModal({
        mode: 'clone',
        name: `${activeUser.Name} Layout`,
        description: `Cloned from ${activeUser.Name}`,
        jsonText: JSON.stringify(payload, null, 2)
      });
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  async function saveTemplate() {
    templateFormError = '';
    const name = templateForm.name.trim();
    if (!name) {
      templateFormError = 'Template name is required';
      return;
    }
    let payload;
    try {
      payload = JSON.parse(templateForm.jsonText);
    } catch (err) {
      templateFormError = 'Template JSON is invalid';
      return;
    }
    try {
      await api.createEmbyLayoutTemplate({
        name,
        description: templateForm.description.trim(),
        layout: payload
      });
      showToast('Template saved', 'success');
      showTemplateModal = false;
      loadTemplates();
    } catch (err) {
      showToast(err.message || 'Failed to save template', 'error');
    }
  }

  function openApplyTemplateModal({ templateId = '', userIds = [] } = {}) {
    if (!templates.length) {
      loadTemplates();
    }
    applyTemplateId = templateId ? String(templateId) : (templates[0]?.id ? String(templates[0].id) : '');
    applyUserIds = new Set(userIds.map((id) => String(id)));
    applyProgress = null;
    applyStatus = {};
    showApplyModal = true;
  }

  function toggleApplyUser(userId) {
    const next = new Set(applyUserIds);
    if (next.has(userId)) {
      next.delete(userId);
    } else {
      next.add(userId);
    }
    applyUserIds = next;
  }

  async function applyTemplateToUsers() {
    if (!applyTemplateId) {
      showToast('Select a template', 'error');
      return;
    }
    if (applyUserIds.size === 0) {
      showToast('Select at least one user', 'error');
      return;
    }

    const template = templates.find((t) => String(t.id) === String(applyTemplateId));
    if (!template) {
      showToast('Template not found', 'error');
      return;
    }

    let payload = template.json_blob || {};
    if (typeof payload === 'string') {
      try {
        payload = JSON.parse(payload);
      } catch (err) {
        showToast('Template JSON is invalid', 'error');
        return;
      }
    }

    const targets = Array.from(applyUserIds);
    applyProgress = { running: true, total: targets.length, done: 0, current: '' };
    applyStatus = {};

    let successCount = 0;
    for (const userId of targets) {
      const user = users.find((u) => String(u.Id) === String(userId));
      applyProgress = { ...applyProgress, current: user?.Name || userId };
      applyStatus = { ...applyStatus, [userId]: { status: 'pending' } };
      try {
        const requestPayload = { template: payload };
        if (layoutClient && layoutClient.trim()) requestPayload.client = layoutClient.trim();
        if (layoutDeviceId && layoutDeviceId.trim()) requestPayload.deviceId = layoutDeviceId.trim();
        await api.applyEmbyLayout(serverId, userId, requestPayload);
        applyStatus = { ...applyStatus, [userId]: { status: 'success' } };
        successCount += 1;
      } catch (err) {
        applyStatus = {
          ...applyStatus,
          [userId]: { status: 'error', error: err.message || 'Failed' }
        };
      }
      applyProgress = {
        ...applyProgress,
        done: applyProgress.done + 1
      };
    }

    applyProgress = { ...applyProgress, running: false, current: '' };
    if (successCount === targets.length) {
      showToast('Template applied to users', 'success');
    } else {
      showToast('Template applied with errors', 'error');
    }
  }

  function openPreview(template) {
    if (!template) return;
    previewTitle = template.name || 'Template Preview';
    previewJson = JSON.stringify(template.json_blob || {}, null, 2);
    showPreviewModal = true;
  }

  async function deleteTemplate(template) {
    if (!template) return;
    if (!confirm(`Delete template "${template.name}"?`)) return;
    try {
      await api.deleteEmbyLayoutTemplate(template.id);
      showToast('Template deleted', 'success');
      loadTemplates();
    } catch (err) {
      showToast(err.message || 'Failed to delete template', 'error');
    }
  }
</script>

<div class="layouts-panel">
  {#if toast}
    <div class="toast" class:error={toastType === 'error'} class:success={toastType === 'success'}>
      <span class="toast-icon">
        {#if toastType === 'success'}
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
        {:else}
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
        {/if}
      </span>
      {toast}
    </div>
  {/if}

  <div class="panel-header">
    <div>
      <h3>Home-Screen Layouts</h3>
      <p class="muted">Sync, edit, and template Emby home-screen layouts</p>
    </div>
  </div>

  <div class="client-controls">
    <div class="client-field">
      <label class="label">Client</label>
      <input class="input" type="text" bind:value={layoutClient} placeholder="Emby Web" />
      <div class="hint">Use the exact client name from Emby web network calls.</div>
    </div>
    <div class="client-field">
      <label class="label">Device ID</label>
      <input class="input" type="text" bind:value={layoutDeviceId} placeholder="faveswitch" />
      <div class="hint">Keep stable per device; Emby stores prefs by client + device.</div>
    </div>
    <div class="client-actions">
      <button class="btn btn-secondary btn-sm" on:click={() => activeUser && viewLayout(activeUser)} disabled={!activeUser || layoutLoading}>
        Reload Layout
      </button>
    </div>
  </div>

  <div class="tabs">
    <button class="tab" class:active={activeTab === 'users'} on:click={() => (activeTab = 'users')}>
      Users
    </button>
    <button class="tab" class:active={activeTab === 'templates'} on:click={() => (activeTab = 'templates')}>
      Templates
    </button>
  </div>

  {#if activeTab === 'users'}
    <div class="card">
      <div class="section-header">
        <div>
          <h4>User Layouts</h4>
          <p class="muted">Select a user to view and edit their layout preferences</p>
        </div>
        <button class="btn btn-secondary btn-sm" on:click={loadUsers} disabled={usersLoading}>
          {usersLoading ? 'Refreshing...' : 'Refresh Users'}
        </button>
      </div>

      {#if usersError}
        <div class="alert alert-error">{usersError}</div>
      {:else if usersLoading}
        <div class="loading-row">Loading users...</div>
      {:else if users.length === 0}
        <div class="empty-state">
          <p>No users found for this server.</p>
        </div>
      {:else}
        <div class="user-grid">
          {#each users as user (user.Id)}
            <div class="user-card" class:active={activeUser?.Id === user.Id}>
              <div class="user-meta">
                <div class="avatar">{user.Name?.charAt(0) || '?'}</div>
                <div>
                  <div class="user-name">{user.Name}</div>
                  <div class="user-id">ID: {user.Id}</div>
                </div>
              </div>
              <button class="btn btn-secondary btn-sm" on:click={() => viewLayout(user)}>
                View Layout
              </button>
            </div>
          {/each}
        </div>
      {/if}
    </div>

    <div class="card layout-editor">
      <div class="section-header">
        <div>
          <h4>{activeUser ? `Layout: ${activeUser.Name}` : 'Select a User'}</h4>
          <p class="muted">Display preferences are grouped by ID (home, resume, libraries)</p>
        </div>
        {#if activeUser}
          <div class="actions">
            <button class="btn btn-ghost btn-sm" on:click={openCloneTemplateFromUser} disabled={layoutLoading}>
              Clone Layout
            </button>
            <button class="btn btn-secondary btn-sm" on:click={openSaveTemplateFromLayout} disabled={layoutLoading}>
              Save to Template
            </button>
            <button class="btn btn-secondary btn-sm" on:click={() => openApplyTemplateModal({ userIds: [activeUser.Id] })}>
              Apply Template
            </button>
            <button class="btn btn-primary btn-sm" on:click={pushToUser} disabled={pushing || layoutLoading}>
              {pushing ? 'Pushing...' : 'Push to User'}
            </button>
          </div>
        {/if}
      </div>

      {#if layoutError}
        <div class="alert alert-error">{layoutError}</div>
      {:else if layoutLoading}
        <div class="loading-row">Loading layout preferences...</div>
      {:else if !activeUser}
        <div class="empty-state">
          <p>Select a user to inspect their layout preferences.</p>
        </div>
      {:else if orderedLayoutKeys.length === 0}
        <div class="empty-state">
          <p>No layout preferences returned for this user.</p>
        </div>
      {:else}
        {#if layoutUnsupported.length}
          <div class="alert alert-error">
            Unsupported preference IDs skipped: {layoutUnsupported.join(', ')}
          </div>
        {/if}
        <div class="pref-list">
          {#each orderedLayoutKeys as prefId (prefId)}
            <div class="pref-card">
              <button class="pref-header" on:click={() => togglePref(prefId)}>
                <div class="pref-title">
                  <span class="badge badge-warning">{prefId}</span>
                </div>
                <span class="toggle">
                  {expandedPrefs.has(prefId) ? 'Collapse' : 'Expand'}
                </span>
              </button>
              {#if expandedPrefs.has(prefId)}
                <textarea
                  class="json-editor"
                  bind:value={layoutDraft[prefId]}
                  spellcheck="false"
                  rows="10"
                ></textarea>
              {/if}
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {:else}
    <div class="card">
      <div class="section-header">
        <div>
          <h4>Layout Templates</h4>
          <p class="muted">Create, preview, and apply reusable layout packs</p>
        </div>
        <button class="btn btn-primary btn-sm" on:click={openCreateTemplate}>
          Create Template
        </button>
      </div>

      {#if templatesError}
        <div class="alert alert-error">{templatesError}</div>
      {:else if templatesLoading}
        <div class="loading-row">Loading templates...</div>
      {:else if templates.length === 0}
        <div class="empty-state">
          <p>No templates saved yet.</p>
        </div>
      {:else}
        <div class="template-grid">
          {#each templates as template (template.id)}
            <div class="template-card">
              <div class="template-info">
                <div class="template-name">{template.name}</div>
                <div class="template-desc">{template.description || 'No description'}</div>
              </div>
              <div class="template-actions">
                <button class="btn btn-ghost btn-sm" on:click={() => openPreview(template)}>
                  Preview
                </button>
                <button class="btn btn-secondary btn-sm" on:click={() => openApplyTemplateModal({ templateId: template.id })}>
                  Apply to User(s)
                </button>
                <button class="btn btn-ghost btn-sm danger" on:click={() => deleteTemplate(template)}>
                  Delete
                </button>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {/if}

  {#if showTemplateModal}
    <div class="modal-backdrop" on:click|self={() => (showTemplateModal = false)}>
      <div class="modal">
        <div class="modal-header">
          <h4>{templateFormMode === 'clone' ? 'Clone Template' : 'Create Template'}</h4>
        </div>
        <div class="modal-body">
          {#if templateFormError}
            <div class="alert alert-error">{templateFormError}</div>
          {/if}
          <div class="form-grid">
            <div>
              <label class="label">Template Name</label>
              <input class="input" type="text" bind:value={templateForm.name} placeholder="Home Layout - Kids" />
            </div>
            <div>
              <label class="label">Description</label>
              <input class="input" type="text" bind:value={templateForm.description} placeholder="Optional description" />
            </div>
          </div>
          <div class="editor-block">
            <label class="label">Template JSON</label>
            <textarea class="json-editor" bind:value={templateForm.jsonText} rows="12" spellcheck="false"></textarea>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn btn-ghost" on:click={() => (showTemplateModal = false)}>Cancel</button>
          <button class="btn btn-primary" on:click={saveTemplate}>Save Template</button>
        </div>
      </div>
    </div>
  {/if}

  {#if showApplyModal}
    <div class="modal-backdrop" on:click|self={() => (showApplyModal = false)}>
      <div class="modal">
        <div class="modal-header">
          <h4>Apply Template</h4>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div>
              <label class="label">Template</label>
              <select class="input" bind:value={applyTemplateId}>
                <option value="">Select a template</option>
                {#each templates as template}
                  <option value={template.id}>{template.name}</option>
                {/each}
              </select>
            </div>
            <div>
              <label class="label">Users</label>
              <div class="user-select">
                {#each users as user (user.Id)}
                  <label class="user-select-row">
                    <input
                      type="checkbox"
                      checked={applyUserIds.has(String(user.Id))}
                      on:change={() => toggleApplyUser(String(user.Id))}
                    />
                    <span>{user.Name}</span>
                  </label>
                {/each}
              </div>
            </div>
          </div>

          {#if applyProgress}
            <div class="progress-block">
              <div class="progress-meta">
                Applying {applyProgress.done} / {applyProgress.total}
              </div>
              <div class="progress-bar">
                <div
                  class="progress-bar-fill"
                  style="width: {applyProgress.total ? (applyProgress.done / applyProgress.total) * 100 : 0}%"
                ></div>
              </div>
              {#if applyProgress.current}
                <div class="progress-current">Current: {applyProgress.current}</div>
              {/if}
              <div class="progress-status">
                {#each Object.entries(applyStatus) as [userId, status]}
                  <div class="status-row">
                    <span>{users.find((u) => String(u.Id) === String(userId))?.Name || userId}</span>
                    <span class="badge" class:badge-success={status.status === 'success'} class:badge-error={status.status === 'error'}>
                      {status.status}
                    </span>
                  </div>
                {/each}
              </div>
            </div>
          {/if}
        </div>
        <div class="modal-actions">
          <button class="btn btn-ghost" on:click={() => (showApplyModal = false)}>Close</button>
          <button class="btn btn-primary" on:click={applyTemplateToUsers} disabled={applyProgress?.running}>
            {applyProgress?.running ? 'Applying...' : 'Apply Template'}
          </button>
        </div>
      </div>
    </div>
  {/if}

  {#if showPreviewModal}
    <div class="modal-backdrop" on:click|self={() => (showPreviewModal = false)}>
      <div class="modal">
        <div class="modal-header">
          <h4>{previewTitle}</h4>
        </div>
        <div class="modal-body">
          <textarea class="json-editor" rows="16" readonly value={previewJson}></textarea>
        </div>
        <div class="modal-actions">
          <button class="btn btn-primary" on:click={() => (showPreviewModal = false)}>Close</button>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .layouts-panel {
    padding: 24px;
  }

  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
  }

  .client-controls {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 12px;
    margin-bottom: 18px;
    padding: 12px;
    border: 1px solid var(--border);
    border-radius: 12px;
    background: var(--bg-secondary);
  }

  .client-field .input {
    margin-bottom: 6px;
  }

  .client-actions {
    display: flex;
    align-items: flex-end;
  }

  .hint {
    font-size: 11px;
    color: var(--text-tertiary);
  }

  .panel-header h3 {
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
  }

  .muted {
    font-size: 13px;
    color: var(--text-tertiary);
  }

  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 16px;
  }

  .section-header h4 {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
  }

  .actions {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .user-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 12px;
  }

  .user-card {
    padding: 12px;
    border: 1px solid var(--border);
    background: var(--bg-primary);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .user-card.active {
    border-color: rgba(139, 92, 246, 0.4);
    box-shadow: 0 0 0 1px rgba(139, 92, 246, 0.25);
  }

  .user-meta {
    display: flex;
    gap: 10px;
    align-items: center;
  }

  .avatar {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    background: rgba(139, 92, 246, 0.2);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    color: var(--text-primary);
  }

  .user-name {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
  }

  .user-id {
    font-size: 11px;
    color: var(--text-tertiary);
  }

  .layout-editor {
    margin-top: 16px;
  }

  .pref-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .pref-card {
    background: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
  }

  .pref-header {
    width: 100%;
    border: none;
    background: var(--bg-secondary);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    color: var(--text-primary);
    cursor: pointer;
  }

  .pref-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
  }

  .toggle {
    font-size: 12px;
    color: var(--text-tertiary);
  }

  .json-editor {
    width: 100%;
    border: none;
    border-top: 1px solid var(--border);
    background: #0b0714;
    color: #e8e3f7;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
    font-size: 12px;
    line-height: 1.5;
    padding: 14px;
    resize: vertical;
  }

  .json-editor:focus {
    outline: 1px solid var(--accent);
  }

  .template-grid {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .template-card {
    padding: 14px 16px;
    border: 1px solid var(--border);
    border-radius: 12px;
    background: var(--bg-primary);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .template-info {
    flex: 1;
  }

  .template-name {
    font-size: 14px;
    font-weight: 600;
  }

  .template-desc {
    font-size: 12px;
    color: var(--text-tertiary);
    margin-top: 4px;
  }

  .template-actions {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .danger {
    color: #ef4444;
  }

  .loading-row {
    font-size: 13px;
    color: var(--text-tertiary);
  }

  .empty-state {
    text-align: center;
    color: var(--text-tertiary);
    padding: 24px 12px;
  }

  .toast {
    position: fixed;
    top: 24px;
    right: 24px;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 18px;
    background: var(--bg-card);
    border: 1px solid rgba(139, 92, 246, 0.3);
    border-radius: 10px;
    box-shadow: var(--shadow-elevated);
    z-index: 2000;
    animation: slideIn 0.3s ease;
  }

  .toast.success {
    border-color: rgba(16, 185, 129, 0.4);
  }

  .toast.error {
    border-color: rgba(239, 68, 68, 0.4);
  }

  .toast-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 22px;
    height: 22px;
    border-radius: 6px;
    background: rgba(139, 92, 246, 0.2);
  }

  .toast.error .toast-icon {
    color: #ef4444;
    background: rgba(239, 68, 68, 0.2);
  }

  .toast.success .toast-icon {
    color: #10b981;
    background: rgba(16, 185, 129, 0.2);
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateX(24px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }

  .modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(7, 4, 16, 0.75);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1500;
    padding: 20px;
  }

  .modal {
    width: min(760px, 92vw);
    max-height: 90vh;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    box-shadow: var(--shadow-elevated);
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .modal-header {
    padding: 16px 20px;
    border-bottom: 1px solid var(--border);
  }

  .modal-body {
    padding: 18px 20px;
    overflow: auto;
  }

  .modal-actions {
    padding: 16px 20px;
    border-top: 1px solid var(--border);
    display: flex;
    justify-content: flex-end;
    gap: 10px;
  }

  .form-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 12px;
    margin-bottom: 12px;
  }

  .label {
    display: block;
    font-size: 12px;
    color: var(--text-secondary);
    margin-bottom: 6px;
  }

  .editor-block {
    margin-top: 12px;
  }

  .user-select {
    max-height: 200px;
    overflow: auto;
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 8px;
    background: var(--bg-primary);
  }

  .user-select-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 4px;
    font-size: 13px;
    color: var(--text-secondary);
  }

  .progress-block {
    margin-top: 16px;
    background: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 12px;
  }

  .progress-meta {
    font-size: 12px;
    color: var(--text-tertiary);
    margin-bottom: 8px;
  }

  .progress-bar {
    height: 8px;
    border-radius: 999px;
    background: var(--bg-secondary);
    overflow: hidden;
  }

  .progress-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--accent), #c084fc);
  }

  .progress-current {
    margin-top: 8px;
    font-size: 12px;
    color: var(--text-secondary);
  }

  .progress-status {
    margin-top: 12px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .status-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    color: var(--text-secondary);
  }

  @media (max-width: 720px) {
    .section-header {
      flex-direction: column;
      align-items: flex-start;
    }

    .template-card {
      flex-direction: column;
      align-items: flex-start;
    }

    .template-actions {
      width: 100%;
    }
  }
</style>
