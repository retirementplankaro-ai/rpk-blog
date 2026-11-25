# Retirement Plan Karo Blog

Static blog for https://blog.retirementplankaro.com (Cloudflare Pages project, deploys `public/` from `main` automatically on every push, no build command).

## Adding an article
1. Create `content/posts/YYYY-MM-DD-<slug>.md` with front matter:
   ```
   ---
   title: ...
   description: ... (under 160 characters)
   date: YYYY-MM-DD
   slug: lowercase-words-with-dashes
   tool_name: Free SIP Calculator
   tool_url: https://retirementplankaro.com/sip-calculator/
   ---
   ```
2. Body in Markdown. Use `## ` sections, one table, a `## FAQ` section where every question is a `### ...?` heading (this becomes FAQ schema).
3. `pip install --break-system-packages markdown` if needed, then `python3 build.py`.
4. Commit both `content/` and `public/` and push to `main`.

## Calculator links (use the most relevant one as tool_url; build.py adds UTM tags automatically)
Base: https://retirementplankaro.com
- /retirement-planner/ (default for retirement corpus, pension, FIRE)
- /sip-calculator/  /lumpsum-calculator/  /swp-calculator/  /cagr-calculator/  /investment-returns-calculator/
- /income-tax-calculator/  /hra-calculator/  /gratuity-calculator/
- /epf-calculator/  /ppf-calculator/  /nps-calculator/  /fd-calculator/  /rd-calculator/  /sukanya-samriddhi-calculator/
- /loan-emi-calculator/  /home-loan-eligibility-calculator/
- /term-insurance-calculator/  /inflation-calculator/  /expense-calculator/
- /life-goal-planner/  /asset-allocation-planner/  /risk-profile-test/  /net-worth-tracker/
- /mutual-fund-portfolio-analysis/  /stock-portfolio-analysis/  /interest-rates-today/
Inside the article body, also link 1-2 relevant calculators naturally, each with
?utm_source=blog&utm_medium=article&utm_campaign=<slug>.

## Writing rules
- Audience: Indian salaried families, 25–60. Simple Hinglish (Roman script) or Hindi; short sentences.
- 800–1,200 words. Real worked numbers, computed in code, never guessed.
- Educational only: no named stock or fund recommendations, no guaranteed returns (SEBI rules). The disclaimer is added automatically.
- Never repeat a topic or slug already in `content/posts/`.
- Do not use the word "AI" in article copy.
