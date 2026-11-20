---
title: "Finetuning LLMs for discriminating similar languages"
categories: ["nlp", "ai"]
date: "16.01.2024"
excerpt: "How difficult is to distinguish between similar languages and dialects? I finetuned bert multilingual models for the DSL (discriminating between similar languages) shared task."

---

Explanatory video (5 min): https://youtu.be/JFo7F-MQ7lM
<br/><br/>
More details & discussion on github: https://github.com/kkristianr/dialect-identification
<br/><br/>


The shared task is "DSL" (discriminating between similar languages) and it has been part of the VarDial (Varieties and Dialects) workshop for more than 10 years. The winners in the last competitions did not rely on llms, but rather n-gram models combined with Naive Bayes or, in general, probabilistic models. Curious about the absence of large language models, I wanted to see if llms can be useful for this type of task.


### Challenges
1. high lexical overlap: one sentence could be correct in all similar languages. 
2. scarsity of training data: dialects are a good example of low-resource languages. LLMs rely on large training data, here we lack it. 

### Approach 
I picked up the shared task from 2017 and their training data to finetune multilingual bert and BERTic models, in order to evaluate finetuning strategies on generic bert models with limited training data for classifying low-resource languages.

The finetuned model is published on hugging-face, and a proof of concept has been deployed on streamlit to showcase the classification system.








