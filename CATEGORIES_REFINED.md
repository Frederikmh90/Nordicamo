# News Categories for Alternative Media - Refined List

**Target:** 7-10 categories suitable for hyper-partisan/alternative news media in Nordic countries

**Context:** These outlets often focus on topics that mainstream media may cover differently, including conspiracy theories, anti-establishment narratives, immigration critiques, and health skepticism.

---

## Proposed Categories (10 Categories)

### 1. **Politics & Governance**
- Elections, political parties, government actions
- Political scandals, corruption
- Parliamentary debates, policy decisions
- Political figures and their actions

### 2. **Immigration & National Identity**
- Immigration policies and debates
- Border control, asylum seekers
- National identity, cultural preservation
- Integration issues, multiculturalism critique

### 3. **Health & Medicine**
- Pandemic coverage, vaccines
- Healthcare policy, medical freedom
- Alternative medicine, health skepticism
- Public health measures critique

### 4. **Media & Censorship**
- Mainstream media criticism
- Free speech, censorship concerns
- Social media deplatforming
- Information control narratives

### 5. **International Relations & Conflict**
- War, geopolitics, foreign policy
- NATO, EU, international organizations
- Conflicts (Ukraine, Middle East, etc.)
- Diplomatic relations

### 6. **Economy & Labor**
- Economic policy, inflation, financial markets
- Financial regulatory violations, securities law, stock trading
- Stock market manipulation, investments, acquisitions
- Economic crime, financial fraud, corporate fraud
- Corporate critique, wealth inequality
- Workers' rights, labor issues
- Cryptocurrency, banking, financial institutions

### 7. **Crime & Justice**
- Law enforcement, police actions
- Judicial system, court cases, legal proceedings
- Regulatory violations, lawsuits, legal disputes
- Crime statistics, safety concerns
- Economic crime cases, financial crime trials
- Legal reforms, justice system critique

### 8. **Social Issues & Culture**
- Gender issues, feminism critique
- Education policy, school reforms
- Religion, cultural values
- Family policy, social welfare

### 9. **Environment, Climate & Energy**
- Climate change, environmental policy
- Energy policy, renewable energy
- Environmental activism, green movements
- Fossil fuels, energy independence

### 10. **Technology, Science & Digital Society**
- Big tech, social media platforms
- Privacy, surveillance, digital rights
- Science and research
- AI, automation, technological change

---

## Category Assignment Strategy

**For Qwen2.5 LLM Prompt:**

```
Classify this news article into 1-3 most relevant categories from:
1. Politics & Governance
2. Immigration & National Identity  
3. Health & Medicine
4. Media & Censorship
5. International Relations & Conflict
6. Economy & Labor
7. Crime & Justice
8. Social Issues & Culture
9. Environment, Climate & Energy
10. Technology, Science & Digital Society

Respond with JSON:
{
  "categories": ["category1", "category2"],
  "confidence": "high|medium|low"
}
```

---

## Rationale

These 10 categories:
- ✅ Cover major themes in alternative media
- ✅ Are mutually exclusive enough for clear classification
- ✅ Allow for multi-labeling (articles can have 1-3 categories)
- ✅ Work across Nordic countries (Denmark, Sweden, Norway, Finland)
- ✅ Suitable for both academic research and public dashboard

---

## Final Category List ✅

The 10 categories are finalized and implemented in:
- `scripts/01_data_preprocessing.py`
- `scripts/02_nlp_processing.py`

