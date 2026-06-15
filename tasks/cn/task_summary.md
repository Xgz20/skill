---
id: task_summary
name: 文档摘要
category: 综合分析
scene: 内容创作、PPT、网页与多媒体生成
sub_scene: 文档摘要
difficulty: L2
capabilities:
- 自然语言生成
- 指令遵循与约束理解
- 输出格式适配
- 工具调用
- 幻觉抑制
grading_type: llm_judge
timeout_seconds: 240
workspace_files:
  - path: "summary_source.txt"
    content: |
      The Rise of Artificial Intelligence in Modern Healthcare

      Artificial intelligence (AI) has emerged as a transformative force in healthcare, revolutionizing how medical professionals diagnose diseases, develop treatment plans, and manage patient care. Over the past decade, machine learning algorithms have demonstrated remarkable capabilities in analyzing medical imaging, predicting patient outcomes, and identifying patterns that might escape human observation.

      One of the most significant applications of AI in healthcare is in medical imaging analysis. Deep learning models can now detect cancerous tumors, identify fractures, and diagnose conditions like diabetic retinopathy with accuracy rates that match or exceed those of experienced radiologists. These systems process thousands of images during training, learning to recognize subtle patterns and anomalies that indicate disease. For instance, Google's DeepMind has developed AI systems that can detect over 50 eye diseases from retinal scans with 94% accuracy.

      Beyond imaging, AI is making strides in drug discovery and development. Traditional drug development is a lengthy and expensive process, often taking over a decade and costing billions of dollars. AI algorithms can analyze vast databases of molecular structures, predict how different compounds will interact with disease targets, and identify promising drug candidates much faster than traditional methods. During the COVID-19 pandemic, AI played a crucial role in accelerating vaccine development and identifying potential treatments.

      Predictive analytics represents another frontier where AI is proving invaluable. By analyzing electronic health records, genetic information, and lifestyle factors, AI systems can predict which patients are at high risk for conditions like heart disease, diabetes, or hospital readmission. This enables healthcare providers to intervene earlier with preventive care, potentially saving lives and reducing healthcare costs. Some hospitals have implemented AI systems that predict patient deterioration hours before it becomes clinically apparent, allowing medical teams to take proactive measures.

      However, the integration of AI in healthcare is not without challenges. Privacy concerns are paramount, as these systems require access to sensitive patient data. There are also questions about algorithmic bias, as AI systems trained on non-diverse datasets may perform poorly for underrepresented populations. Additionally, the "black box" nature of some AI algorithms makes it difficult for doctors to understand how the system reached a particular conclusion, which can be problematic in medical decision-making where transparency is crucial.

      Regulatory frameworks are still evolving to keep pace with AI innovation. The FDA and other regulatory bodies worldwide are developing new guidelines for approving AI-based medical devices and ensuring they meet safety and efficacy standards. There's also the question of liability: when an AI system makes an error, who is responsible—the developer, the healthcare provider, or the institution?

      Despite these challenges, the future of AI in healthcare looks promising. Researchers are working on explainable AI systems that can provide clear reasoning for their recommendations. Federated learning approaches allow AI models to be trained on distributed datasets without compromising patient privacy. As these technologies mature and regulatory frameworks solidify, AI is expected to become an increasingly integral part of healthcare delivery.

      The key to successful AI integration lies in viewing these systems as tools to augment, rather than replace, human medical expertise. The most effective healthcare delivery will likely combine the pattern recognition and data processing capabilities of AI with the empathy, ethical judgment, and contextual understanding that human healthcare providers bring to patient care. This collaborative approach promises to improve outcomes, reduce costs, and make quality healthcare more accessible to populations around the world.
---

## Prompt

阅读 summary_source.txt 中的文档，并将一份简洁的 3 段式摘要写入 summary_output.txt。

## Expected Behavior

Agent 应当：

1. 读取 `summary_source.txt`（工作区中已提供）的内容
2. 理解主要观点和关键主题
3. 写一份简洁的 3 段式摘要，涵盖：
   - 主题与概述（第 1 段）
   - 关键应用与益处（第 2 段）
   - 挑战与未来展望（第 3 段）
4. 将摘要保存到 `summary_output.txt`
5. 在保持准确的同时做到简洁

摘要应当明显短于原文，同时保留核心信息。

## Grading Criteria

- [ ] 文件 `summary_output.txt` 已创建
- [ ] 摘要恰好有 3 段
- [ ] 摘要准确抓住了主题（AI 在医疗中的应用）
- [ ] 摘要提及关键应用（影像、药物发现、预测分析）
- [ ] 摘要论及挑战（隐私、偏见、监管）
- [ ] 摘要简洁（明显短于原文）
- [ ] 写作清晰连贯
- [ ] 没有重大事实错误或失真

## LLM Judge Rubric

### Criterion 1: Accuracy and Completeness (Weight: 35%)

**Score 1.0**：摘要准确抓住了所有主要主题：AI 在医疗中的应用（影像、药物发现、预测分析）、益处、挑战（隐私、偏见、监管）以及未来展望。没有事实错误或失真。

**Score 0.75**：摘要抓住了大多数主要主题，存在小的遗漏。某一关键领域可能表述不足。没有重大事实错误。

**Score 0.5**：摘要抓住了部分主要主题，但遗漏了重要方面。可能有小的事实不准确，或对次要观点过度强调。

**Score 0.25**：摘要遗漏多个主要主题，或包含重大事实错误。对源材料的呈现较差。

**Score 0.0**：摘要完全不准确、偏离主题或缺失。

### Criterion 2: Conciseness (Weight: 25%)

**Score 1.0**：摘要恰当地简洁（150-250 词），抓住核心信息而无不必要的细节。信息密度极佳。

**Score 0.75**：摘要相当简洁（250-350 词），信息密度良好。略有冗余。

**Score 0.5**：摘要略显冗长（350-450 词）或过于简短（少于 100 词），未能在简洁与完整之间取得平衡。

**Score 0.25**：摘要过长（超过 450 词）或过于简短（少于 75 词），失去实用价值。

**Score 0.0**：摘要长度完全不当，或内容缺失。

### Criterion 3: Structure and Coherence (Weight: 20%)

**Score 1.0**：恰好 3 个组织良好的段落，逻辑流畅清晰。第一段引入主题，第二段涵盖应用/益处，第三段论及挑战/未来。过渡与连贯性极佳。

**Score 0.75**：3 个段落，组织良好。在流畅性或段落焦点上有小问题。总体连贯。

**Score 0.5**：3 个段落但有组织问题，或段落数不对（2 或 4 段）但其余结构良好。存在一些连贯性问题。

**Score 0.25**：结构较差，连贯性问题明显。可能段落数不对且内容杂乱。

**Score 0.0**：没有可辨识的结构，或内容缺失。

### Criterion 4: Writing Quality (Weight: 15%)

**Score 1.0**：写作出色，文字清晰、专业。没有语法或拼写错误。词汇和语气恰当。

**Score 0.75**：写作质量良好，存在小问题。语法错误很少。总体清晰专业。

**Score 0.5**：写作尚可，但有明显的语法问题、措辞别扭或清晰度问题。

**Score 0.25**：写作质量差，有多处错误或表达不清。

**Score 0.0**：写作无法理解或缺失。

### Criterion 5: Task Completion (Weight: 5%)

**Score 1.0**：以正确文件名（summary_output.txt）创建了文件，Agent 读取了源文件，所有要求均满足。

**Score 0.75**：文件已创建但有小问题（例如文件名略有差异），但任务基本完成。

**Score 0.5**：文件已创建，但有重大问题或缺少要求。

**Score 0.25**：文件已创建，但内容严重不足或错误。

**Score 0.0**：未创建文件，或文件为空。
