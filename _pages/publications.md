---
layout: page
permalink: /publications/
title: Publications
description: Publications in reversed chronological order.
nav: true
nav_order: 2
---

<div style="margin-bottom: 2rem; padding: 1.2rem; border-left: 4px solid var(--global-theme-color); background: var(--global-bg-color); border-radius: 0 8px 8px 0; line-height: 2;">
  <strong>87 JCR journal articles</strong> (52 Q1, 27 Q2, 1 Q3, 1 Q4)<br>
  <strong>63+ conference papers</strong> (international and national)<br>
  <strong>h-index: 40</strong> (Google Scholar)<br>
  <strong>7,600+ citations</strong><br>
  ESI Highly Cited &amp; Hot Papers
</div>

<div style="margin-bottom: 2rem; font-size: 1.1rem;">
  <a href="#journals"><strong>Journal Papers</strong></a> · 
  <a href="#conferences"><strong>International Conferences</strong></a> · 
  <a href="#national"><strong>National Conferences</strong></a>
</div>

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
