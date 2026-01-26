<script>
  import { api } from '../api.js';
  import { getServerIcon as getSharedServerIcon, usesNativeColor } from '../serverIcons.js';

  export let serverId = null;
  export let item;
  export let user = null;
  export let serverLabel = '';

  let isFavorite = item.UserData?.IsFavorite || false;
  let toggling = false;

  async function toggleFavorite() {
    if (!user || !serverId || toggling) return;

    toggling = true;
    try {
      if (isFavorite) {
        await api.removeFavorite(serverId, user.Id, item.Id);
        isFavorite = false;
      } else {
        if ((serverLabel || '').toLowerCase() === 'audiobookshelf') {
          await api.addAbsUserFavourite(serverId, user.Name || '', item.Id);
        } else {
          await api.addFavorite(serverId, user.Id, item.Id, user.Name || '');
        }
        isFavorite = true;
      }
    } catch (e) {
      console.error('Failed to toggle favorite:', e);
    } finally {
      toggling = false;
    }
  }

  function getYear(item) {
    return item.ProductionYear || item.PremiereDate?.substring(0, 4) || '';
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
        return api.getImageUrl(serverId, item.Id, 'Primary', 300, item.ImageTags.Primary);
      }
      return api.getImageUrl(serverId, item.Id, 'Primary', 300);
    }
    return null;
  }

  function getServerIconUrl(type) {
    return getSharedServerIcon(type);
  }

  $: isNativeColor = usesNativeColor(serverLabel);
</script>

<div class="media-card">
  {#if serverLabel}
    <span class="server-tag">
      {#if getServerIconUrl(serverLabel)}
        <img src={getServerIconUrl(serverLabel)} alt={`${serverLabel} icon`} class:native-color={isNativeColor} />
      {:else}
        {serverLabel}
      {/if}
    </span>
  {/if}
  {#if getImageUrl(item)}
    <img src={getImageUrl(item)} alt={item.Name} loading="lazy" />
  {:else}
    <div class="no-image">
      <span class="text-[--text-tertiary] text-sm">No Image</span>
    </div>
  {/if}

  <div class="info">
    <div class="title" title={item.Name}>{item.Name}</div>
    <div class="meta">
      {#if getYear(item)}
        <span class="year">{getYear(item)}</span>
      {/if}
      <span class="type">{item.Type}</span>
      {#if getStatusLabel(item)}
        <span class="status">{getStatusLabel(item)}</span>
      {/if}
    </div>

    {#if user}
      <button
        class="fav-btn"
        class:is-favorite={isFavorite}
        on:click|stopPropagation={toggleFavorite}
        disabled={toggling}
        title={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
      >
        {#if toggling}
          <span class="spinner"></span>
        {:else}
          <svg width="18" height="18" viewBox="0 0 24 24" fill={isFavorite ? 'currentColor' : 'none'} stroke="currentColor" stroke-width="2">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
          </svg>
        {/if}
      </button>
    {/if}
  </div>
</div>

<style>
  .media-card {
    position: relative;
  }

  img {
    width: 100%;
    aspect-ratio: 2/3;
    object-fit: cover;
    border-radius: 12px 12px 0 0;
    display: block;
  }

  .no-image {
    width: 100%;
    aspect-ratio: 2/3;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg-primary);
    border-radius: 12px 12px 0 0;
  }

  .info {
    padding: 12px;
    position: relative;
  }

  .title {
    font-weight: 600;
    font-size: 14px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    color: var(--text-primary);
    margin-bottom: 4px;
  }

  .meta {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
  }

  .server-tag {
    position: absolute;
    top: 8px;
    left: 8px;
    padding: 4px 8px;
    background: rgba(0, 0, 0, 0.65);
    color: #fff;
    border-radius: 999px;
    font-size: 11px;
    z-index: 2;
    backdrop-filter: blur(4px);
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }

  .server-tag img {
    width: 14px;
    height: 14px;
    filter: brightness(0) invert(1);
  }

  .server-tag img.native-color {
    filter: none;
  }

  .year {
    color: var(--text-secondary);
  }

  .type {
    color: var(--accent);
    text-transform: uppercase;
    font-weight: 500;
    font-size: 10px;
    padding: 2px 6px;
    background: rgba(139, 92, 246, 0.15);
    border-radius: 4px;
  }

  .status {
    color: #34d399;
    text-transform: uppercase;
    font-weight: 600;
    font-size: 10px;
    padding: 2px 6px;
    background: rgba(16, 185, 129, 0.15);
    border-radius: 4px;
  }

  .fav-btn {
    position: absolute;
    top: -36px;
    right: 8px;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(4px);
    border: none;
    border-radius: 8px;
    font-size: 18px;
    cursor: pointer;
    color: var(--text-secondary);
    transition: all 0.2s;
  }

  .fav-btn:hover {
    background: rgba(0, 0, 0, 0.8);
    color: #fbbf24;
  }

  .fav-btn.is-favorite {
    color: #fbbf24;
  }

  .fav-btn:disabled {
    opacity: 0.5;
    cursor: wait;
  }

  .fav-btn .spinner {
    width: 14px;
    height: 14px;
    border: 2px solid rgba(255, 255, 255, 0.2);
    border-top-color: currentColor;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }
</style>

