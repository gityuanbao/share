## 视频链接

https://www.bilibili.com/video/BV1jg9tYEE4i/

## 资源合集

AI生成检测工具的开源仓库：https://github.com/YuchuanTian/AIGC_text_detector

对应的论文链接：https://arxiv.org/pdf/2305.18149

hugging face上的检测demo：https://huggingface.co/spaces?q=AI+Detector （这里只是搜索结果，这些应用都会不断更新，而且提供源码）

AI生成在线检测网站：https://matrix.tencent.com/ai-detect/ai_gen_txt

### 关于论文中的检测原理

这篇论文讲的是怎么检测AI写的文本，尤其是短文本。原理用大白话来说是这样的：

AI写的短文本有时候跟人写的太像了，很难分清，所以不能简单地把文本分成“人写的”和“AI写的”两类。作者觉得短文本有点不好分类，于是提出了一种新方法，叫Multiscale Positive-Unlabeled (MPU)框架。

核心想法：把人写的文本看成“正类”，AI写的短文本不完全当“负类”，而是部分“不好分类”的状态。

怎么做：用一个特别的MPU损失函数，根据文本长度调整判断标准，短文本更倾向于“不确定”，长文本更能分清来源。

加点料：还通过随机删句子，造出不同长度的训练文本，让模型学得更全面。

简单来说，就是不硬分两类，而是承认短文本的模糊性，再用灵活的方法提高检测效果。实验证明，这招对短文本和长文本都管用。

### 双语提示词

中文：

为保证输出质量，你的输出需提高文本复杂程度和节奏感，实现出色表达。提高文本复杂程度，你需要通过提高词汇运用的丰富度与内容的不可预测度。提高文章节奏感，你可以通过描述句子长度和句式的波动幅度。强节奏感的文本，句子构建富有动态变化。

英文：

To ensure the quality of the output, your output needs to increase the complexity of the text and the sense of rhythm to achieve excellent expression. To increase the complexity of the text, you need to enhance the richness of vocabulary usage and the unpredictability of the content. To enhance the sense of rhythm in the article, you can do so by describing the fluctuations in sentence length and sentence patterns. A text with a strong sense of rhythm features dynamic changes in sentence construction.