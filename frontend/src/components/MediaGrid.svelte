<script>
  import { api } from '../api.js';
  import MediaCard from './MediaCard.svelte';

  export let serverId = null;
  export let serverType = null;
  export let type = 'library';
  export let libraryId = null;
  export let user = null;
  export let searchQuery = '';
  export let showSearch = true;

  let items = [];
  let loading = true;
  let error = null;
  let internalSearchTerm = '';
  let totalCount = 0;

  $: if (serverId) {
    if (type === 'search') {
      const term = searchQuery.trim();
      if (term) {
        runSearch(term);
      } else {
        items = [];
        totalCount = 0;
        loading = false;
      }
    } else {
      loadItems(type, libraryId, user);
    }
  }

  async function loadItems(type, libraryId, user) {
    if (!serverId) return;

    loading = true;
    error = null;

    try {
      let result;

      if (type === 'recent') {
        result = await api.getRecent(serverId, 30);
      } else if (type === 'favorites' && user) {
        result = await api.getFavorites(serverId, user.Id);
      } else if (type === 'library' && libraryId) {
        result = await api.getItems(serverId, {
          parent_id: libraryId,
          limit: 50
        });
      } else {
        result = await api.getItems(serverId, { limit: 50 });
      }

      items = result.Items || [];
      totalCount = result.TotalRecordCount || items.length;
    } catch (e) {
      error = e.message;
      items = [];
    } finally {
      loading = false;
    }
  }

  async function runSearch(term) {
    if (!serverId) return;

    loading = true;
    error = null;
    try {
      const result = await api.getItems(serverId, {
        search: term,
        parent_id: libraryId || undefined
      });
      items = result.Items || [];
      totalCount = result.TotalRecordCount || items.length;
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  async function search() {
    if (!serverId) return;

    if (!internalSearchTerm.trim()) {
      loadItems(type, libraryId, user);
      return;
    }

    runSearch(internalSearchTerm.trim());
  }
</script>

{#if showSearch}
  <div class="card">
    <form class="flex gap-3" on:submit|preventDefault={search}>
      <input
        type="text"
        class="input flex-1"
        placeholder="Search media..."
        bind:value={internalSearchTerm}
      />
      <button type="submit" class="btn btn-primary">Search</button>
    </form>
  </div>
{/if}

{#if loading}
  <div class="media-grid">
    {#each Array(8) as _, idx}
      <div class="skeleton-card" aria-hidden="true">
        <div class="skeleton thumb"></div>
        <div class="skeleton line w-80"></div>
        <div class="skeleton line w-60"></div>
      </div>
    {/each}
  </div>
{:else if error}
  <div class="alert alert-error">{error}</div>
{:else if items.length === 0}
  <div class="card text-center py-8">
    <p class="text-[--text-secondary]">No items found.</p>
  </div>
{:else}
  <p class="text-sm text-[--text-secondary] mb-4">{totalCount} items</p>
  <div class="media-grid">
    {#each items as item (item.Id)}
      <MediaCard {serverId} {item} {user} serverLabel={serverType} />
    {/each}
  </div>
{/if}

<style>
  .media-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 12px;
  }

  .skeleton-card {
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    background: var(--bg-card);
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .skeleton {
    background: linear-gradient(90deg, rgba(255,255,255,0.04) 25%, rgba(255,255,255,0.12) 37%, rgba(255,255,255,0.04) 63%);
    background-size: 400% 100%;
    animation: shimmer 1.4s ease infinite;
    border-radius: 8px;
  }

  .skeleton.thumb {
    width: 100%;
    aspect-ratio: 2/3;
  }

  .skeleton.line {
    height: 10px;
  }

  .skeleton.line.w-80 { width: 80%; }
  .skeleton.line.w-60 { width: 60%; }

  @keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
  }
</style>
