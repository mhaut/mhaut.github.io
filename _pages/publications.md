---
layout: page
permalink: /publications/
title: Publications
description: Publications in reversed chronological order.
nav: true
nav_order: 2
---

<div style="margin-bottom: 2rem; font-size: 1.1rem;">
  <a href="#journals"><strong>Journal Papers</strong></a> · 
  <a href="#conferences"><strong>Conference Papers</strong></a>
</div>

<h2 id="journals" style="margin-bottom: 1.5rem;">Journal Papers</h2>

<div class="publications">
{% bibliography --query @article %}
</div>

<hr style="margin: 4rem 0;">

<h2 id="conferences" style="margin-bottom: 1.5rem;">Conference Papers</h2>

<div class="publications">
{% bibliography --query @inproceedings %}
</div>
