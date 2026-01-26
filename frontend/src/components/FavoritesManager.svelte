<script>
  import { api } from '../api.js';

  export let serverId = null;
  export let user = null;
  export let serverType = null;

  let favorites = [];
  let searchResults = [];
  let collections = [];
  let selectedCollection = null;
  let collectionsLoading = false;
  let loading = false;
  let searchLoading = false;
  let error = null;
  let searchTerm = '';
  let showSearch = false;
  let lastUserId = null;
  let lastServerId = null;

  $: isAudiobookshelf = serverType === 'audiobookshelf';

  $: if (isAudiobookshelf && user && serverId) {
    if (user.Id !== lastUserId || serverId !== lastServerId) {
      lastUserId = user.Id;
      lastServerId = serverId;
      selectedCollection = null;
      collections = [];
      loadCollections();
    }
  }

  $: if (!isAudiobookshelf && user && serverId) {
    loadFavorites();
  }

  $: if (isAudiobookshelf && user && serverId && selectedCollection) {
    loadCollectionItems();
  }

  async function loadFavorites() {
    if (!user || !serverId) return;

    loading = true;
    error = null;

    try {
      const result = await api.getFavorites(serverId, user.Id);
      favorites = result.Items || [];
    } catch (e) {
      error = e.message;
      favorites = [];
    } finally {
      loading = false;
    }
  }

  async function loadCollections() {
    if (!user || !serverId) return;

    collectionsLoading = true;
    error = null;

    try {
      console.log('[Favarr] ABS collections request', { serverId, userId: user.Id });
      const result = await api.getCollections(serverId, user.Id);
      console.log('[Favarr] ABS collections response', result);
      collections = result || [];
      if (!selectedCollection && collections.length > 0) {
        const favourites = collections.find(isFavouritesCollection);
        selectedCollection = favourites || collections[0];
      } else if (collections.length === 0) {
        favorites = [];
      }
    } catch (e) {
      error = e.message;
      collections = [];
      selectedCollection = null;
    } finally {
      collectionsLoading = false;
    }
  }

  async function loadCollectionItems() {
    if (!user || !serverId || !selectedCollection) return;

    loading = true;
    error = null;

    try {
      console.log('[Favarr] ABS collection items request', {
        serverId,
        userId: user.Id,
        collectionId: selectedCollection.Id
      });
      const result = await api.getCollectionItems(serverId, user.Id, selectedCollection.Id);
      console.log('[Favarr] ABS collection items response', result);
      favorites = result.Items || [];
    } catch (e) {
      error = e.message;
      favorites = [];
    } finally {
      loading = false;
    }
  }

  async function searchItems() {
    if (!serverId) return;

    if (!searchTerm.trim()) {
      searchResults = [];
      return;
    }

    searchLoading = true;
    try {
      const result = await api.getItems(serverId, {
        search: searchTerm,
        limit: 20
      });
      searchResults = result.Items || [];
    } catch (e) {
      error = e.message;
    } finally {
      searchLoading = false;
    }
  }

  async function addToFavorites(item) {
    if (!user || !serverId) return;

    try {
      if (isAudiobookshelf) {
        const collection = selectedCollection || await ensureFavouritesCollection();
        if (!collection) {
          throw new Error('Please select a collection');
        }
        console.log('[Favarr] ABS add collection item', {
          serverId,
          userId: user.Id,
          collectionId: collection.Id,
          itemId: item.Id
        });
        await api.addCollectionItem(serverId, user.Id, collection.Id, item.Id);
        await loadCollectionItems();
      } else {
        await api.addFavorite(serverId, user.Id, item.Id);
        await loadFavorites();
      }
      searchResults = searchResults.map(r =>
        r.Id === item.Id ? { ...r, isAdded: true } : r
      );
    } catch (e) {
      error = e.message;
    }
  }

  async function removeFromFavorites(item) {
    if (!user || !serverId) return;

    try {
      if (isAudiobookshelf && selectedCollection) {
        console.log('[Favarr] ABS remove collection item', {
          serverId,
          userId: user.Id,
          collectionId: selectedCollection.Id,
          itemId: item.Id
        });
        await api.removeCollectionItem(serverId, user.Id, selectedCollection.Id, item.Id);
        favorites = favorites.filter(f => f.Id !== item.Id);
      } else {
        await api.removeFavorite(serverId, user.Id, item.Id);
        favorites = favorites.filter(f => f.Id !== item.Id);
      }
    } catch (e) {
      error = e.message;
    }
  }

  function toggleSearch() {
    showSearch = !showSearch;
    if (!showSearch) {
      searchTerm = '';
      searchResults = [];
    }
  }

  function isInFavorites(itemId) {
    return favorites.some(f => f.Id === itemId);
  }

  function isFavouritesCollection(collection) {
    const name = collection?.Name?.toLowerCase();
    return name === 'favourites' || name === 'favorites';
  }

  async function ensureFavouritesCollection() {
    const existing = collections.find(isFavouritesCollection);
    if (existing) {
      selectedCollection = existing;
      return existing;
    }
    console.log('[Favarr] ABS create favourites collection', { serverId, userId: user.Id });
    await api.createCollection(serverId, user.Id, {
      name: 'Favourites',
      description: 'Favourites from Favarr'
    });
    await loadCollections();
    const created = collections.find(isFavouritesCollection);
    if (created) {
      selectedCollection = created;
      return created;
    }
    return null;
  }

  function selectCollection(collection) {
    selectedCollection = collection;
  }

  function getStatusLabel(item) {
    if (!item?.UserData?.Played) return null;
    const type = (item.Type || '').toLowerCase();
    if (type.includes('audio') || type.includes('book') || type.includes('podcast')) {
      return 'Read';
    }
    return 'Watched';
  }

  function getImageUrl(item) {
    if (!serverId) return null;
    if (item.ImageTags?.Primary) {
      if (typeof item.ImageTags.Primary === 'string' && item.ImageTags.Primary.startsWith('/')) {
        return api.getImageUrl(serverId, item.Id, 'Primary', 150, item.ImageTags.Primary);
      }
      return api.getImageUrl(serverId, item.Id, 'Primary', 150);
    }
    return null;
  }
</script>

{#if !user}
  <div class="card text-center py-8">
    <p class="text-[--text-secondary]">Please select a user to manage favorites.</p>
  </div>
{:else}
  <div class="card">
    <div class="flex items-center justify-between mb-4">
      <h2 class="card-title !mb-0">
        {isAudiobookshelf ? 'Collections' : 'Favorites'} for {user.Name}
      </h2>
      <button class="btn btn-primary" on:click={toggleSearch}>
        {showSearch ? 'Close' : (isAudiobookshelf ? '+ Add to Collection' : '+ Add Items')}
      </button>
    </div>

    {#if error}
      <div class="alert alert-error">{error}</div>
    {/if}

    {#if isAudiobookshelf}
      <div class="collections-panel">
        <div class="collections-header">
          <h3 class="text-sm font-medium text-[--accent]">Collections</h3>
          {#if !collectionsLoading && !collections.some(isFavouritesCollection)}
            <button class="btn btn-secondary btn-sm" on:click={ensureFavouritesCollection}>
              + Favourites
            </button>
          {/if}
        </div>
        {#if collectionsLoading}
          <p class="text-sm text-[--text-secondary]">Loading collections...</p>
        {:else if collections.length === 0}
          <p class="text-sm text-[--text-secondary]">No collections found.</p>
        {:else}
          <div class="collection-list">
            {#each collections as collection (collection.Id)}
              <button
                class="collection-btn"
                class:active={selectedCollection?.Id === collection.Id}
                on:click={() => selectCollection(collection)}
              >
                <span class="collection-name">{collection.Name}</span>
                <span class="badge badge-success">{collection.ItemCount}</span>
              </button>
            {/each}
          </div>
        {/if}
      </div>
    {/if}

    {#if showSearch}
      <div class="search-section">
        <h3 class="text-sm font-medium text-[--accent] mb-3">
          {isAudiobookshelf
            ? `Search Items to Add to ${selectedCollection?.Name || 'Favourites'}`
            : 'Search Items to Add'}
        </h3>
        <form class="flex gap-3" on:submit|preventDefault={searchItems}>
          <input
            type="text"
            class="input flex-1"
            placeholder={isAudiobookshelf ? 'Search for audiobooks, podcasts...' : 'Search for movies, shows...'}
            bind:value={searchTerm}
          />
          <button type="submit" class="btn btn-secondary" disabled={searchLoading}>
            {searchLoading ? 'Searching...' : 'Search'}
          </button>
        </form>

        {#if searchResults.length > 0}
          <div class="search-results">
            {#each searchResults as item (item.Id)}
              <div class="result-item">
                {#if getImageUrl(item)}
                  <img src={getImageUrl(item)} alt={item.Name} />
                {:else}
                  <div class="no-img">
                    <span class="text-xs text-[--text-tertiary]">No Image</span>
                  </div>
                {/if}
                <div class="result-info">
                  <div class="result-title">{item.Name}</div>
                  <div class="result-meta">
                    <span class="badge badge-success">{item.Type}</span>
                    {#if item.ProductionYear}
                      <span class="text-[--text-secondary]">{item.ProductionYear}</span>
                    {/if}
                    {#if getStatusLabel(item)}
                      <span class="badge badge-warning">{getStatusLabel(item)}</span>
                    {/if}
                  </div>
                </div>
                <button
                  class="btn"
                  class:btn-primary={!isInFavorites(item.Id) && !item.isAdded}
                  class:btn-secondary={isInFavorites(item.Id) || item.isAdded}
                  on:click={() => addToFavorites(item)}
                  disabled={isInFavorites(item.Id) || item.isAdded}
                >
                  {isInFavorites(item.Id) || item.isAdded ? 'Added' : 'Add'}
                </button>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    {/if}
  </div>

  <div class="card">
    <h3 class="text-sm font-medium text-[--accent] mb-4">
      {isAudiobookshelf
        ? (selectedCollection?.Name || 'Collection')
        : 'Current Favorites'}
      <span class="badge badge-success ml-2">{favorites.length}</span>
    </h3>

    {#if loading}
      <div class="favorites-skeleton">
        {#each Array(5) as _, idx}
          <div class="skeleton-row" aria-hidden="true">
            <div class="skeleton thumb"></div>
            <div class="skeleton text w-60"></div>
            <div class="skeleton text w-40"></div>
          </div>
        {/each}
      </div>
    {:else if favorites.length === 0}
      <p class="text-[--text-secondary] text-center py-8">
        {isAudiobookshelf
          ? 'No collection items yet. Click "+ Add to Collection" to add books.'
          : 'No favorites yet. Click "+ Add Items" to search and add media to your favorites.'}
      </p>
    {:else}
      <div class="favorites-list">
        {#each favorites as item (item.Id)}
          <div class="favorite-item">
            {#if getImageUrl(item)}
              <img src={getImageUrl(item)} alt={item.Name} />
            {:else}
              <div class="no-img">
                <span class="text-xs text-[--text-tertiary]">No Image</span>
              </div>
            {/if}
            <div class="favorite-info">
              <div class="favorite-title">{item.Name}</div>
              <div class="favorite-meta">
                <span class="badge badge-success">{item.Type}</span>
                {#if item.ProductionYear}
                  <span class="text-[--text-secondary]">{item.ProductionYear}</span>
                {/if}
                {#if getStatusLabel(item)}
                  <span class="badge badge-warning">{getStatusLabel(item)}</span>
                {/if}
              </div>
            </div>
            <button
              class="btn btn-remove"
              on:click={() => removeFromFavorites(item)}
            >
              Remove
            </button>
          </div>
        {/each}
      </div>
    {/if}
  </div>
{/if}

<style>
  .search-section {
    background: var(--bg-primary);
    padding: 16px;
    border-radius: 12px;
    margin-top: 16px;
    border: 1px solid var(--border);
  }

  .collections-panel {
    background: var(--bg-primary);
    padding: 16px;
    border-radius: 12px;
    margin-top: 16px;
    border: 1px solid var(--border);
  }

  .collections-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
  }

  .collection-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-height: 200px;
    overflow-y: auto;
  }

  .collection-btn {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 10px 12px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.2s;
    text-align: left;
  }

  .collection-btn:hover {
    border-color: rgba(139, 92, 246, 0.3);
  }

  .collection-btn.active {
    background: rgba(139, 92, 246, 0.15);
    border-color: rgba(139, 92, 246, 0.4);
  }

  .collection-name {
    font-size: 13px;
    font-weight: 500;
    color: var(--text-primary);
  }

  .search-results {
    margin-top: 16px;
    max-height: 400px;
    overflow-y: auto;
  }

  .result-item,
  .favorite-item {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 12px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    margin-bottom: 8px;
    transition: all 0.2s;
  }

  .result-item:hover,
  .favorite-item:hover {
    border-color: rgba(139, 92, 246, 0.3);
  }

  .result-item img,
  .favorite-item img {
    width: 50px;
    height: 75px;
    object-fit: cover;
    border-radius: 8px;
    flex-shrink: 0;
  }

  .no-img {
    width: 50px;
    height: 75px;
    background: var(--bg-primary);
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    flex-shrink: 0;
  }

  .result-info,
  .favorite-info {
    flex: 1;
    min-width: 0;
  }

  .result-title,
  .favorite-title {
    font-weight: 600;
    font-size: 14px;
    margin-bottom: 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .result-meta,
  .favorite-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
  }

  .favorites-list {
    max-height: 500px;
    overflow-y: auto;
  }

  .btn-remove {
    background: rgba(239, 68, 68, 0.15);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.2);
  }

  .btn-remove:hover {
    background: rgba(239, 68, 68, 0.25);
  }

  .favorites-skeleton {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .skeleton-row {
    display: grid;
    grid-template-columns: 50px 1fr auto;
    align-items: center;
    gap: 12px;
    padding: 10px;
    border: 1px solid var(--border);
    border-radius: 10px;
    background: var(--bg-card);
  }

  .skeleton {
    background: linear-gradient(90deg, rgba(255,255,255,0.04) 25%, rgba(255,255,255,0.12) 37%, rgba(255,255,255,0.04) 63%);
    background-size: 400% 100%;
    animation: shimmer 1.4s ease infinite;
    border-radius: 8px;
  }

  .skeleton.thumb {
    width: 50px;
    height: 75px;
    border-radius: 8px;
  }

  .skeleton.text {
    height: 10px;
    border-radius: 4px;
  }

  .skeleton.text.w-60 { width: 60%; }
  .skeleton.text.w-40 { width: 40%; }

  @keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
  }
</style>
