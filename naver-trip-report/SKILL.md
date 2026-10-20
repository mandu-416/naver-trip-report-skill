---
name: naver-trip-report
description: Build a time-calculated, day-by-day travel itinerary report from Korean travel blogs. Crawls Naver (search.naver.com blog tab + m.blog.naver.com posts) and Google results through the Firecrawl API, fits sights, shopping, workouts (pool, gym, dawn runs) and cheap local restaurants around the traveler's fixed bookings, hotel and arrival/departure times, then draws numbered route maps per day with Google Flow and embeds them in a shareable report. Use this whenever someone wants a travel plan, 여행 일정, 동선, 쇼핑 코스, 맛집 동선, 일정표 with times, or a 여행 보고서 built from Naver/네이버 blog research, or asks to crawl Naver for a destination — even if they only mention one piece (e.g. "네이버에서 시드니 쇼핑코스 크롤링해줘", "3일 동선 보고서로 써줘", "지도에 번호 적어서 동선 그려줘").
---

# Naver trip report

Turn "plan my days in <city>" into a report a traveler can actually follow: every stop has a time, every move has a travel time, every meal has three nearby cheap options with sources, and every day has a map.

The workflow below came out of a real planning session. Most of the value is in the order of operations and in the traps it avoids, so follow the order and read the "why" notes.

## 0. Gather the fixed constraints first

Ask (or extract from what the user already said) before planning anything:

- Dates and weekdays of the trip, arrival time on day 1, departure time on the last day
- Hotel name / address — all travel times are computed from it
- Already-booked tours or activities with their meeting points and times
- Must-dos (e.g. pool + gym at a specific venue, dawn running, specific sights, shopping)
- Pace preferences (e.g. "departure day should be relaxed", "don't cram shopping into one day")

Why: in practice the user drips these in one at a time, and each one invalidates part of a finished plan (a 14:00 arrival kills a morning; a booked tour day can't host a workout; a hotel change shifts every walking time). Collecting them up front avoids rewriting the whole report three times. If something is unknown, plan with a stated assumption and say so in the report's lead.

Treat booked tours as immovable blocks. Put workouts and long side-trips on days that are not tour days, not the departure day, and not already full, and if no day fits, say so plainly instead of squeezing it in.

## 1. Crawl Naver (and Google) with Firecrawl

The API key lives in a `.env` file as `FIRECRAWL_API_KEY`. Never print it; load it into the environment and pass it in a header.

Use the bundled script:

```bash
python -I scripts/naver_crawl.py search "시드니 시내 여행코스" --out work/course
python -I scripts/naver_crawl.py posts work/course/posts.txt --limit 6 --out work/course/posts
python -I scripts/naver_crawl.py google "cheap eats Haymarket Sydney locals" --out work/food
```

`search` scrapes the Naver blog tab and writes `posts.txt` (one `url | title` per line). `posts` scrapes each post through `m.blog.naver.com` and writes cleaned markdown. `google` uses Firecrawl's `/v1/search` and keeps each result's headings, which is usually enough to pull restaurant names, addresses and prices.

Things that went wrong before and how the script handles them:

- `www.naver.com` itself has no travel content. Use `search.naver.com/search.naver?ssc=tab.blog.all&query=...` for the blog tab.
- Desktop `blog.naver.com` pages are iframes; `m.blog.naver.com/<id>/<postNo>` returns the actual post body.
- On Windows the console is cp949 and Korean/emoji output crashes `print`. `python -I` also ignores `PYTHONIOENCODING`. The script writes UTF-8 files instead of printing content. Read the files.
- Some posts are sponsored (affiliate links, "프로모션", coupon blocks). Keep using their facts, but flag them as possibly promotional in the report.

Search several angles in parallel: `<city> 시내 여행코스`, `<city> 쇼핑코스`, `<city> 러닝 코스`, the specific venue name (e.g. `올림픽파크 수영장`), and per-area food queries (`<area> 가성비 맛집 현지인`). For opening hours and prices, prefer the venue's official page; scrape it directly.

## 2. Plan the days

For each day, build a table: `시간 | 일정 | 이동 | 메모`. Rules of thumb that held up:

- Compute every leg from the hotel (or the previous stop) and write the mode and minutes ("기차 Town Hall → Lidcombe 환승, 약 40–45분"). Label estimates as estimates.
- Check weekday-dependent hours for every stop (markets that close Mon/Tue, weekend-only markets, late-night shopping nights, weekday-only lunch places, pool hours that differ on weekends). Weekday mistakes are the most common silent error.
- Dawn runs: start around sunrise; prefer waterfront routes reported by local runners in the crawled posts; keep them 3.5–7 km and give a shorter fallback.
- After a late tour return, next morning starts later; before an early tour, the evening ends early.
- On the departure day, aim to be at the airport about 3 hours before an international flight and leave hotel luggage in storage; keep that day light.
- Split shopping across days near where the user already is, and put any store that is closed on later days on the earliest day it's open.

## 3. Restaurants: three per meal, along the route

For each meal slot in the itinerary, pick three inexpensive places locals actually use, located on or next to that part of the route. Sources: Naver posts by local residents ("현지인", "n년차", "거주"), plus Google results from local food media or official precinct guides. For each: name (Korean + original), location relative to the route, a signature dish with price if a source gives one, and a link to the page you opened. Don't list hours you didn't verify; tell the reader to check Google Maps instead. Avoid weekday traps (e.g. a weekday-only lunch spot on a Saturday).

## 4. Write the report

If a document connector (e.g. Claude Docs) is available, write the report there so it can be shared and commented on; otherwise write Markdown/HTML. Structure:

1. Title, as-of date
2. Lead: dates, hotel, the key scheduling decisions (where workouts and runs went and why)
3. 한눈에 보기 — one table, one row per day (morning / day / evening)
4. Sources and method (one short paragraph)
5. One section per day: heading, 1–2 sentence point, the time table, the day's map, a one-line fallback
6. 이동시간과 교통 table (hotel-based)
7. 동선별 식당 추천 — a sub-heading per meal slot with its 3-row table
8. 준비물과 주의사항 (weekday traps, booking needed, passport for duty free, sun protection, etc.)
9. 출처 list

When the user changes a constraint later, search the doc for every place the old value appears (hotel name, walking minutes, station names, "다음 날 05:30 러닝" type cross-references) and update them all, including the summary table and restaurant-location notes.

## 5. Draw the day maps with Google Flow

See `references/google-flow-maps.md` for the browser procedure and prompt templates. The short version:

- One image per day in Google Flow (Nano Banana): numbered red pins in visiting order, a dashed route, a white label card per stop with time + one-line description, orange fork markers for that day's restaurants, a legend, and a title with the date.
- Nano Banana usually renders labels in English even when you supply Korean. Generate first, pick the better of the two outputs, then send an edit: "keep the map, routes, pins and layout exactly the same; only rewrite all label text in Korean" with the exact label strings. The same edit can fix a misplaced route.
- Inspect each result for geography errors (pins on the wrong side of a harbour, a route wandering through unrelated streets) and mention any that remain. These are illustrations, not navigation maps; say so under the maps.
- Downloading files requires the user's explicit OK. Once given, download the 1K original of each final image, rename them `day1.jpg`…, and embed each under its day heading (for Claude Docs: upload as an asset of the doc's artifact, create a blob, then `![alt](blob/<id>)`).

## Privacy

The finished report contains personal travel details. Don't publish it or the maps anywhere public unless the user asks, and keep API keys only in `.env`.
