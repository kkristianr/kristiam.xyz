---
title: "Semantic shift analysis with vector space models"
categories: ["nlp", "ai"]
date: "04.06.2024"
excerpt: "Train and align word embeddings from scratch from diachronic and synchronic corpora to discover semantic shifts."
---

I have given a more theoretical presentation about this topic at the course "Research topics in NLP" on the 4th june 2024. You can find it <a href="/materials/semantic_change.pdf" target="_blank">here</a>.

You can access and try the application on: <a href="https://sem.kristiam.xyz" target="_blank">sem.kristiam.xyz</a>. There you will find the same explanations from below. 

### The idea
The idea behind word embeddings comes from the distributional hypothesis: words that appear in similar contexts have similar meanings. Since embeddings will reflect their training data, and the data is usually not perfect, they will inherit its biases. 
In this project, we want to use that bias to our advantage by analyzing how the meaning of a word shifts across space (e.g., publisher, genre) or time (e.g., year, decade). For each setting, we train embeddings from scratch on the given data. 
Since word embeddings from different corpora can't be simply compared, we align them into a common vector space to allow some analysis.



