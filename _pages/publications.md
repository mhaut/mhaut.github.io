---
layout: page
permalink: /publications/
title: Publications
description: Journal articles and conference contributions in reverse chronological order.
nav: true
nav_order: 2
---

<div style="margin-bottom: 2rem; padding: 1.2rem; border-left: 4px solid var(--global-theme-color); background: var(--global-bg-color); border-radius: 0 8px 8px 0; line-height: 2;">
  <strong>{% bibliography_count --query @article %} journal articles</strong> listed on this website<br>
  <strong>{% bibliography_count --query @inproceedings %} conference contributions</strong> listed on this website<br>
  <a href="https://scholar.google.com/citations?user=zLffeY8AAAAJ&amp;sortby=pubdate">Latest publications and current citation metrics on Google Scholar</a><br>
  ESI Highly Cited &amp; Hot Papers
</div>

Bibliography updated on 19 October 2026. Articles use the year of their journal volume where assigned; Early Access articles are identified in their entries.

{% include bib_search.liquid %}

<div style="margin-bottom: 2rem; font-size: 1.1rem;">
  <a href="#journals"><strong>Journal Papers</strong></a> · 
  <a href="#conferences"><strong>International Conferences</strong></a> · 
  <a href="#national"><strong>National Conferences</strong></a>
</div>

<div id="publication-list">

<h2 id="journals" style="margin-bottom: 1.5rem;">Journal Papers</h2>

<div class="publications">
{% bibliography --query @article %}
</div>

<hr style="margin: 4rem 0;">

<h2 id="conferences" style="margin-bottom: 1.5rem;">International Conference Papers</h2>

<div class="publications">
{% bibliography --query @inproceedings[keywords!=national] %}
</div>

<hr style="margin: 4rem 0;">

<h2 id="national" style="margin-bottom: 1.5rem;">National Conference Papers</h2>

<div class="publications">
{% bibliography --query @inproceedings[keywords=national] %}
</div>

</div>
