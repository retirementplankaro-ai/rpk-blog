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
   tool_url: https://retirementplankaro.com
   ---
   ```
2. Body in Markdown. Use `## ` sections, one table, a `## FAQ` section where every question is a `### ...?` heading (this becomes FAQ schema).
3. `pip install --break-system-packages markdown` if needed, then `python3 build.py`.
4. Commit both `content/` and `public/` and push to `main`.

## Writing rules
- Audience: Indian salaried families, 25–60. Simple Hinglish (Roman script) or Hindi; short sentences.
- 800–1,200 words. Real worked numbers, computed in code, never guessed.
- Educational only: no named stock or fund recommendations, no guaranteed returns (SEBI rules). The disclaimer is added automatically.
- Never repeat a topic or slug already in `content/posts/`.
- Do not use the word "AI" in article copy.
