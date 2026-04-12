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
  <a href="#conferences"><strong>International Conferences</strong></a> · 
  <a href="#national"><strong>National Conferences</strong></a>
</div>

<h2 id="journals" style="margin-bottom: 1.5rem;">Journal Papers</h2>

{% for y in (2016..2026) reversed %}
{% bibliography --query @article[year={{y}}] %}
{% endfor %}

<hr style="margin: 4rem 0;">

<h2 id="conferences" style="margin-bottom: 1.5rem;">International Conference Papers</h2>

{% for y in (2015..2026) reversed %}
{% bibliography --query @inproceedings[year={{y}},keywords!=national] %}
{% endfor %}

<hr style="margin: 4rem 0;">

<h2 id="national" style="margin-bottom: 1.5rem;">National Conference Papers</h2>

{% for y in (2016..2026) reversed %}
{% bibliography --query @inproceedings[year={{y}},keywords=national] %}
{% endfor %}
