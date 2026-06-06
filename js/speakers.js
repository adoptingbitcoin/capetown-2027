/**
 * speakers.js — Client-side renderer for Adopting Bitcoin Cape Town 2027
 * Dynamically renders speaker grid (speakers.html) and speaker detail (speaker.html)
 * from data/speakers.json.
 */
(function () {
  'use strict';

  var BASE_URL = 'https://za27.adoptingbitcoin.org/';
  var JSON_PATH = 'data/speakers.json';
  var PLACEHOLDER_IMG = 'images/anon-img.png';

  /**
   * HTML-escape a string to prevent XSS / rendering issues.
   */
  function escapeHTML(str) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  /**
   * Get speaker display name: "Name Surname" trimmed.
   */
  function displayName(speaker) {
    return ((speaker.name || '') + ' ' + (speaker.surname || '')).trim();
  }

  /**
   * Get speaker photo URL with fallback chain.
   */
  function photoURL(speaker) {
    if (speaker.photo && speaker.photo.trim()) return speaker.photo;
    if (speaker.pretalx_photo && speaker.pretalx_photo.trim()) return speaker.pretalx_photo;
    return PLACEHOLDER_IMG;
  }

  /**
   * Convert bio text to <p> tags. Split on double newlines, HTML-escape each paragraph.
   */
  function bioToHTML(bio) {
    if (!bio) return '';
    var paragraphs = bio.split('\n\n');
    var html = '';
    for (var i = 0; i < paragraphs.length; i++) {
      var p = paragraphs[i].trim();
      if (p) {
        html += '<p>' + escapeHTML(p) + '</p>';
      }
    }
    return html;
  }

  /**
   * Convert a YouTube watch URL to an embed URL.
   * "https://www.youtube.com/watch?v=XYZ&list=..." → "https://www.youtube.com/embed/XYZ"
   */
  function youtubeEmbedURL(url) {
    if (!url) return '';
    var converted = url.replace('watch?v=', 'embed/');
    return converted.split('&')[0];
  }

  /**
   * Normalise a nostr identifier to a full URL.
   */
  function nostrURL(nostr) {
    if (!nostr) return '';
    if (nostr.indexOf('http') === 0) return nostr;
    return 'https://primal.net/p/' + nostr;
  }

  /**
   * Render the speakers grid into div.speakers-collection.
   */
  function renderGrid(speakers, container) {
    var wrapper = document.createElement('div');
    wrapper.className = 'collection-list speakers-list';

    for (var i = 0; i < speakers.length; i++) {
      var s = speakers[i];
      var name = displayName(s);
      var photo = photoURL(s);
      var slug = s.slug || '';
      var company = s.company || '';

      var item = document.createElement('div');
      item.className = 'collection-item';

      item.innerHTML =
        '<a href="speaker.html?s=' + encodeURIComponent(slug) + '" class="speaker-link w-inline-block">' +
          '<div class="speaker-img-overlay"></div>' +
          '<img src="' + escapeHTML(photo) + '" loading="lazy" alt="' + escapeHTML(name) + '" class="speaker-img" onerror="this.onerror=null;this.src=\'' + PLACEHOLDER_IMG + '\'">' +
        '</a>' +
        '<a href="speaker.html?s=' + encodeURIComponent(slug) + '" class="speaker-name-link w-inline-block">' +
          '<div class="speaker-name">' + escapeHTML(name) + '</div>' +
        '</a>' +
        '<div class="speaker-title">' + escapeHTML(company) + '</div>';

      wrapper.appendChild(item);
    }

    container.appendChild(wrapper);
  }

  /**
   * Render the speaker detail into div#speaker-detail.
   */
  function renderDetail(speaker, container) {
    var name = displayName(speaker);
    var photo = photoURL(speaker);
    var company = speaker.company || '';
    var role = speaker.role || '';
    var website = speaker.website && speaker.website.trim() ? speaker.website : '#';
    var bio = bioToHTML(speaker.bio);

    // Update page meta
    document.title = name + ' — Adopting Bitcoin Cape Town 2027';

    var absolutePhoto = photo.indexOf('http') === 0 ? photo : BASE_URL + photo;

    setMeta('description', name + (company ? ' — ' + company : '') + ' at Adopting Bitcoin Cape Town 2027');
    setMeta('og:title', name + ' — Adopting Bitcoin Cape Town 2027');
    setMeta('og:image', absolutePhoto);
    setMeta('twitter:title', name + ' — Adopting Bitcoin Cape Town 2027');
    setMeta('twitter:image', absolutePhoto);

    // Build socials HTML
    var socialsHTML = '';
    if (speaker.twitter && speaker.twitter.trim()) {
      socialsHTML +=
        '<a href="' + escapeHTML(speaker.twitter) + '" class="speaker-socials-icon w-inline-block">' +
          '<img src="images/x-icon.svg" loading="lazy" alt="">' +
        '</a>';
    }
    if (speaker.nostr && speaker.nostr.trim()) {
      var nURL = nostrURL(speaker.nostr);
      socialsHTML +=
        '<div class="w-embed">' +
          '<a href="' + escapeHTML(nURL) + '" target="_blank" class="speaker-socials-icon w-inline-block">' +
            '<img src="https://cdn.prod.website-files.com/6828b74c83472364dfc249b2/6828b74c83472364dfc24a3b_Nostr.svg" loading="lazy" width="22" alt="">' +
          '</a>' +
        '</div>';
    }

    // Build YouTube HTML
    var youtubeHTML = '';
    if (speaker.youtube && speaker.youtube.trim()) {
      var embedURL = youtubeEmbedURL(speaker.youtube);
      youtubeHTML =
        '<div class="w-video w-embed">' +
          '<iframe src="' + escapeHTML(embedURL) + '" frameborder="0" allowfullscreen style="width:100%;aspect-ratio:16/9;"></iframe>' +
        '</div>';
    }

    var html =
      '<section class="section section-speaker">' +
        '<div class="container container-narrow">' +
          '<div class="columns-speaker w-row">' +
            '<div class="w-col w-col-8">' +
              '<div>' +
                '<h2 class="speaker-heading">' + escapeHTML(name) + '</h2>' +
                '<div class="es-20"></div>' +
                '<a href="' + escapeHTML(website) + '" class="speaker-title speaker-page w-inline-block">' +
                  '<div>' + escapeHTML(company) + '</div>' +
                '</a>' +
                '<div class="speaker-title speaker-page">' + escapeHTML(role) + '</div>' +
                '<div class="speaker-socials speaker-socials-subpage">' +
                  socialsHTML +
                '</div>' +
                '<div class="es-20"></div>' +
                '<div class="speaker-bio w-richtext">' + bio + '</div>' +
                '<div class="es-20"></div>' +
              '</div>' +
            '</div>' +
            '<div class="w-col w-col-4">' +
              '<div class="speaker-img-bg">' +
                '<img src="' + escapeHTML(photo) + '" loading="lazy" alt="' + escapeHTML(name) + '" class="speaker-page-image" onerror="this.onerror=null;this.src=\'' + PLACEHOLDER_IMG + '\'">' +
              '</div>' +
            '</div>' +
          '</div>' +
          '<div class="es-60"></div>' +
          youtubeHTML +
        '</div>' +
      '</section>';

    container.innerHTML = html;
  }

  /**
   * Set or create a <meta> tag by property or name attribute.
   */
  function setMeta(key, value) {
    var meta = document.querySelector('meta[property="' + key + '"]') ||
               document.querySelector('meta[name="' + key + '"]');
    if (meta) {
      meta.setAttribute('content', value);
    } else {
      meta = document.createElement('meta');
      if (key.indexOf('og:') === 0 || key.indexOf('twitter:') === 0) {
        meta.setAttribute('property', key);
      } else {
        meta.setAttribute('name', key);
      }
      meta.setAttribute('content', value);
      document.head.appendChild(meta);
    }
  }

  /**
   * Fetch speakers JSON and dispatch to the correct renderer.
   */
  function init() {
    var gridContainer = document.querySelector('div.speakers-collection');
    var detailContainer = document.getElementById('speaker-detail');

    if (!gridContainer && !detailContainer) return;

    fetch(JSON_PATH)
      .then(function (response) {
        if (!response.ok) throw new Error('Failed to load speakers data');
        return response.json();
      })
      .then(function (speakers) {
        if (gridContainer) {
          renderGrid(speakers, gridContainer);
        }

        if (detailContainer) {
          var params = new URLSearchParams(window.location.search);
          var slug = params.get('s');

          if (!slug) {
            window.location.href = 'speakers.html';
            return;
          }

          var speaker = null;
          for (var i = 0; i < speakers.length; i++) {
            if (speakers[i].slug === slug) {
              speaker = speakers[i];
              break;
            }
          }

          if (!speaker) {
            detailContainer.innerHTML =
              '<section class="section section-speaker">' +
                '<div class="container container-narrow">' +
                  '<h2 class="speaker-heading">Speaker not found</h2>' +
                  '<p>The speaker you are looking for does not exist. <a href="speakers.html">View all speakers</a>.</p>' +
                '</div>' +
              '</section>';
            return;
          }

          renderDetail(speaker, detailContainer);
        }
      })
      .catch(function (err) {
        console.error('speakers.js error:', err);
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
